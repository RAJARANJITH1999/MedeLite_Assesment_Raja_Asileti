import re

from django import forms

CCN_PATTERN = re.compile(r"^[A-Za-z0-9]{6}$")

PREVIOUS_COVERAGE_CHOICES = [
    ("", "Select..."),
    ("Yes", "Yes"),
    ("No", "No"),
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
    emr = forms.CharField(
        label="EMR",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g. PCC"}),
        help_text="Electronic Medical Record system used by the facility (e.g. PCC, MatrixCare, PointClickCare).",
    )
    current_census = forms.IntegerField(
        label="Current Census",
        required=False,
        min_value=0,
        help_text="Number of residents currently at the facility today.",
    )
    patient_type = forms.CharField(
        label="Type of Patient",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g. Long-term & Short-term"}),
        help_text="Type(s) of care this facility provides, e.g. Long-term, Short-term, or both.",
    )
    previous_coverage = forms.ChoiceField(
        label="Previous Coverage from Medelite",
        choices=PREVIOUS_COVERAGE_CHOICES,
        required=False,
        help_text="Has Medelite staffed or provided coverage at this facility before?",
    )
    previous_performance = forms.CharField(
        label="Previous Provider Performance from Medelite",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g. About 30 patients/day"}),
        help_text="If previously covered, roughly how many patients/day did Medelite providers see here?",
    )
    medical_coverage = forms.CharField(
        label="Medical Coverage",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g. Optometry, PCP, Podiatry"}),
        help_text="Specialist coverage available on-site, e.g. Optometry, PCP, Podiatry.",
    )
