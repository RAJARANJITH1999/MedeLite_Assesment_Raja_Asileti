from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from assessment.forms import CCNLookupForm
from assessment.models import SavedLookup

SAMPLE_FACILITY = {
    "ccn": "686123",
    "facility_name_from_cms": "KENDALL LAKES HEALTHCARE AND REHAB CENTER",
    "legal_business_name": "KENDALL LAKES HEALTHCARE AND REHAB CENTER, LLC",
    "address": "5280 SW 157 AVENUE",
    "city": "MIAMI",
    "state": "FL",
    "zip_code": "33185",
    "certified_beds": 150,
    "overall_rating": 5,
    "health_inspection_rating": 5,
    "staffing_rating": 2,
    "quality_rating": 5,
    "str_hospitalization": {"label": "Short Term Hospitalization", "facility_value": 27.37, "national_avg": 23.88, "state_avg": 26.2, "unit": "%", "footnote": None},
    "str_ed_visit": {"label": "STR ED Visit", "facility_value": 7.66, "national_avg": 12.01, "state_avg": 9.16, "unit": "%", "footnote": None},
    "lt_hospitalization": {"label": "LT Hospitalization", "facility_value": 2.06, "national_avg": 1.9, "state_avg": 2.15, "unit": "", "footnote": None},
    "lt_ed_visit": {"label": "LT ED Visit", "facility_value": 0.66, "national_avg": 1.8, "state_avg": 1.16, "unit": "", "footnote": None},
    "medicare_care_compare_url": "https://www.medicare.gov/care-compare/details/nursing-home/686123",
}


class CCNLookupFormTests(TestCase):
    def test_rejects_short_ccn(self):
        form = CCNLookupForm(data={"ccn": "123", "facility_name_override": ""})
        self.assertFalse(form.is_valid())

    def test_rejects_non_alphanumeric_ccn(self):
        form = CCNLookupForm(data={"ccn": "12-456", "facility_name_override": ""})
        self.assertFalse(form.is_valid())

    def test_accepts_valid_ccn(self):
        form = CCNLookupForm(data={"ccn": "686123", "facility_name_override": ""})
        self.assertTrue(form.is_valid())


class LookupViewTests(TestCase):
    @patch("assessment.views.backend_client.get_facility")
    def test_valid_ccn_redirects_to_manual_inputs(self, mock_get_facility):
        mock_get_facility.return_value = SAMPLE_FACILITY

        response = self.client.post(reverse("lookup"), {"ccn": "686123", "facility_name_override": ""})

        self.assertRedirects(response, reverse("manual_inputs"))
        self.assertEqual(self.client.session["facility_data"]["ccn"], "686123")

    @patch("assessment.views.backend_client.get_facility")
    def test_backend_error_shows_form_error_not_crash(self, mock_get_facility):
        from assessment.backend_client import BackendError

        mock_get_facility.side_effect = BackendError("CCN 000000 was not found.", 404)

        response = self.client.post(reverse("lookup"), {"ccn": "000000", "facility_name_override": ""})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "was not found")


class ManualInputsAndResultsFlowTests(TestCase):
    @patch("assessment.views.backend_client.get_insights")
    def test_full_flow_creates_saved_lookup_and_renders_results(self, mock_get_insights):
        mock_get_insights.return_value = {"summary": "Test summary.", "generated_by": "rule-based"}

        session = self.client.session
        session["facility_data"] = SAMPLE_FACILITY
        session["manual_inputs"] = {"facility_name_override": ""}
        session.save()

        response = self.client.post(
            reverse("manual_inputs"),
            {
                "emr": "PCC",
                "current_census": 112,
                "patient_type": "Long-term & Short-term",
                "previous_coverage": "Yes",
                "previous_performance": "About 30 patients/day",
                "medical_coverage": "Optometry, PCP, Podiatry",
            },
        )

        self.assertRedirects(response, reverse("results"))
        self.assertEqual(SavedLookup.objects.count(), 1)
        saved = SavedLookup.objects.first()
        self.assertEqual(saved.ccn, "686123")
        self.assertEqual(saved.ai_summary, "Test summary.")

        results_response = self.client.get(reverse("results"))
        self.assertContains(results_response, "KENDALL LAKES HEALTHCARE AND REHAB CENTER")
        self.assertContains(results_response, "Test summary.")

    def test_results_without_session_redirects_to_lookup(self):
        response = self.client.get(reverse("results"))
        self.assertRedirects(response, reverse("lookup"))


class BrandingGuardrailTests(TestCase):
    def test_name_override_does_not_touch_brand_header(self):
        session = self.client.session
        session["facility_data"] = SAMPLE_FACILITY
        session["manual_inputs"] = {"facility_name_override": "Medelite Internal Name"}
        session.save()

        response = self.client.get(reverse("results"))

        content = response.content.decode()
        self.assertIn("Medelite Internal Name", content)
        self.assertIn("INFINITE", content)
        # The brand wordmark block appears before the overridden name in the body.
        self.assertLess(content.index('class="wordmark"'), content.index("Medelite Internal Name"))
