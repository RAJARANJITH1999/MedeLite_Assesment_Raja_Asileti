import json
from pathlib import Path

from app.schemas.manual import ManualInputs
from app.schemas.report import ReportPayload
from app.services.mapping import map_facility_data
from app.services.pdf import render_report_html

FIXTURE = Path(__file__).parent / "fixtures" / "raw_686123.json"


def test_brand_header_survives_facility_name_override():
    """INFINITE — Managed by MEDELITE must never be replaced by facility/override names."""
    raw = json.loads(FIXTURE.read_text())
    facility = map_facility_data("686123", raw)
    manual = ManualInputs(facility_name_override="INFINITE Rebrand Attempt")
    payload = ReportPayload(facility=facility, manual=manual)

    html = render_report_html(payload)

    assert '<div class="brand-name">INFINITE</div>' in html
    assert "Managed by MEDELITE" in html
    # the override text appears in the body, not in the brand header block
    assert html.index('class="brand-name"') < html.index("INFINITE Rebrand Attempt")
