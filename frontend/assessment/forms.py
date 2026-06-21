import re

from django import forms

CCN_PATTERN = re.compile(r"^[A-Za-z0-9]{6}$")

OTHER_SENTINEL = "__other__"

PREVIOUS_COVERAGE_CHOICES = [
    ("", "Select..."),
    ("Yes", "Yes"),
    ("No", "No"),
]

EMR_CHOICES = [
    ("", "Select..."),
    ("PointClickCare (PCC)", "PointClickCare (PCC)"),
    ("MatrixCare", "MatrixCare"),
    ("American HealthTech (AHT)", "American HealthTech (AHT)"),
    ("Netsmart", "Netsmart"),
    ("MEDITECH", "MEDITECH"),
    (OTHER_SENTINEL, "Other (type below)"),
]

PATIENT_TYPE_CHOICES = [
    ("", "Select..."),
    ("Long-term & Short-term", "Long-term & Short-term"),
    ("Long-term only", "Long-term only"),
    ("Short-term only", "Short-term only"),
    ("Memory Care", "Memory Care"),
    ("Skilled Nursing / Rehab", "Skilled Nursing / Rehab"),
    (OTHER_SENTINEL, "Other (type below)"),
]

PREVIOUS_PERFORMANCE_CHOICES = [
    ("", "Select..."),
    ("No prior coverage", "No prior coverage"),
    ("Under 10 patients/day", "Under 10 patients/day"),
    ("10–30 patients/day", "10–30 patients/day"),
    ("30–50 patients/day", "30–50 patients/day"),
    ("50+ patients/day", "50+ patients/day"),
    (OTHER_SENTINEL, "Other (describe below)"),
]

MEDICAL_COVERAGE_CHOICES = [
    ("Optometry", "Optometry"),
    ("Primary Care (PCP)", "Primary Care (PCP)"),
    ("Podiatry", "Podiatry"),
    ("Dental", "Dental"),
    ("Psychiatry / Behavioral Health", "Psychiatry / Behavioral Health"),
    ("Dermatology", "Dermatology"),
    ("Audiology", "Audiology"),
    ("Wound Care", "Wound Care"),
    (OTHER_SENTINEL, "Other (type below)"),
]


class CCNLookupForm(forms.Form):
    ccn = forms.CharField(
        label="CMS Certification Number (CCN)",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={"placeholder": "e.g. 686123", "autofocus": True}),
        help_text="The 6-character facility ID assigned by CMS. Find it on the facility's Medicare Care Compare page.",
    )
    facility_name_override = forms.CharField(
        label="Custom facility name (optional)",
        required=False,
        help_text="Overrides the CMS legal name on the exported report only.",
    )

    def clean_ccn(self):
        ccn = self.cleaned_data["ccn"].strip()
        if not CCN_PATTERN.match(ccn):
            raise forms.ValidationError("CCN must be exactly 6 alphanumeric characters.")
        return ccn


class ManualInputsForm(forms.Form):
    emr = forms.ChoiceField(
        label="EMR",
        choices=EMR_CHOICES,
        required=False,
        help_text="Electronic Medical Record system used by the facility. Pick \"Other\" to type one not listed.",
    )
    emr_other = forms.CharField(
        label="EMR (other)",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Type the EMR name"}),
    )
    current_census = forms.IntegerField(
        label="Current Census",
        required=False,
        min_value=0,
        help_text="Number of residents currently at the facility today.",
    )
    patient_type = forms.ChoiceField(
        label="Type of Patient",
        choices=PATIENT_TYPE_CHOICES,
        required=False,
        help_text="Type(s) of care this facility provides. Pick \"Other\" to describe a different mix.",
    )
    patient_type_other = forms.CharField(
        label="Type of Patient (other)",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Describe the patient type"}),
    )
    previous_coverage = forms.ChoiceField(
        label="Previous Coverage from Medelite",
        choices=PREVIOUS_COVERAGE_CHOICES,
        required=False,
        help_text="Has Medelite staffed or provided coverage at this facility before?",
    )
    previous_performance = forms.ChoiceField(
        label="Previous Provider Performance from Medelite",
        choices=PREVIOUS_PERFORMANCE_CHOICES,
        required=False,
        help_text="If previously covered, roughly how many patients/day did Medelite providers see here?",
    )
    previous_performance_other = forms.CharField(
        label="Previous Provider Performance (other)",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Describe previous performance"}),
    )
    medical_coverage = forms.MultipleChoiceField(
        label="Medical Coverage",
        choices=MEDICAL_COVERAGE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Specialist coverage available on-site. Check \"Other\" to add one not listed.",
    )
    medical_coverage_other = forms.CharField(
        label="Medical Coverage (other)",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Add any other specialty"}),
    )

    def clean(self):
        cleaned_data = super().clean()

        def resolve_other(field_name, other_field_name):
            if cleaned_data.get(field_name) == OTHER_SENTINEL:
                cleaned_data[field_name] = cleaned_data.get(other_field_name, "").strip()
            cleaned_data.pop(other_field_name, None)

        resolve_other("emr", "emr_other")
        resolve_other("patient_type", "patient_type_other")
        resolve_other("previous_performance", "previous_performance_other")

        selected = cleaned_data.get("medical_coverage") or []
        values = [value for value in selected if value != OTHER_SENTINEL]
        other_text = cleaned_data.pop("medical_coverage_other", "").strip()
        if OTHER_SENTINEL in selected and other_text:
            values.append(other_text)
        cleaned_data["medical_coverage"] = ", ".join(values)

        return cleaned_data
