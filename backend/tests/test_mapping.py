import json
from pathlib import Path

from app.services.mapping import map_facility_data

FIXTURE = Path(__file__).parent / "fixtures" / "raw_686123.json"


def load_raw():
    return json.loads(FIXTURE.read_text())


def test_maps_provider_info_fields():
    facility = map_facility_data("686123", load_raw())

    assert facility.ccn == "686123"
    assert facility.facility_name_from_cms == "KENDALL LAKES HEALTHCARE AND REHAB CENTER"
    assert facility.state == "FL"
    assert facility.certified_beds == 150
    assert facility.overall_rating == 5
    assert facility.health_inspection_rating == 5
    assert facility.staffing_rating == 2
    assert facility.quality_rating == 5


def test_maps_claims_measures_to_str_lt_shorthand():
    facility = map_facility_data("686123", load_raw())

    assert facility.str_hospitalization.facility_value == 27.372263
    assert facility.str_ed_visit.facility_value == 7.664234
    assert facility.lt_hospitalization.facility_value == 2.062629
    assert facility.lt_ed_visit.facility_value == 0.656291
    assert facility.str_hospitalization.national_avg is not None
    assert facility.str_hospitalization.state_avg is not None


def test_medicare_care_compare_url_uses_ccn():
    facility = map_facility_data("686123", load_raw())

    assert facility.medicare_care_compare_url == (
        "https://www.medicare.gov/care-compare/details/nursing-home/686123"
    )


def test_missing_claims_measure_yields_none_not_crash():
    raw = load_raw()
    raw["claims_measures"] = []

    facility = map_facility_data("686123", raw)

    assert facility.str_hospitalization.facility_value is None
