import json
from pathlib import Path

from app.schemas.manual import ManualInputs
from app.schemas.report import ReportPayload
from app.services.mapping import map_facility_data
from app.services.report_fields import build_report_rows

FIXTURE = Path(__file__).parent / "fixtures" / "raw_686123.json"

EXPECTED_LABELS = [
    "Name of Facility",
    "Location",
    "EMR",
    "Census Capacity",
    "Current Census",
    "Type of Patient",
    "Previous Coverage from Medelite",
    "Previous Provider Performance from Medelite",
    "Medical Coverage",
    "Overall Star Rating",
    "Health Inspection",
    "Staffing",
    "Quality of Resident Care",
    "Short Term Hospitalization",
    "STR National Avg. for Hospitalization",
    "STR State National Avg. for Hospitalization",
    "STR ED Visit",
    "STR ED Visits National Avg.",
    "STR ED Visits State Avg.",
    "LT Hospitalization",
    "LT National Avg. for Hospitalization",
    "LT State National Avg. for Hospitalization",
    "ED Visit",
    "LT ED Visits National Avg.",
    "LT ED Visits State Avg.",
]


def _payload(name_override=None):
    raw = json.loads(FIXTURE.read_text())
    facility = map_facility_data("686123", raw)
    manual = ManualInputs(facility_name_override=name_override, current_census=112, emr="PCC")
    return ReportPayload(facility=facility, manual=manual)


def test_field_order_matches_facility_assessment_snapshot_template():
    rows = build_report_rows(_payload())
    labels = [label for label, _ in rows]

    assert labels == EXPECTED_LABELS


def test_name_override_replaces_only_the_name_field():
    rows = build_report_rows(_payload(name_override="Medelite Internal Name"))
    rows_by_label = dict(rows)

    assert rows_by_label["Name of Facility"] == "Medelite Internal Name"


def test_no_override_falls_back_to_cms_name():
    rows = build_report_rows(_payload())
    rows_by_label = dict(rows)

    assert rows_by_label["Name of Facility"] == "KENDALL LAKES HEALTHCARE AND REHAB CENTER"
