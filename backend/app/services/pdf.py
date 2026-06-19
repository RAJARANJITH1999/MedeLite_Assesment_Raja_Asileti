from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.schemas.report import ReportPayload
from app.services.report_fields import build_report_rows

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR), autoescape=True)


def render_report_html(payload: ReportPayload, ai_summary: str | None = None) -> str:
    template = _env.get_template("report.html.jinja")
    return template.render(
        state=payload.facility.state,
        rows=build_report_rows(payload),
        ai_summary=ai_summary,
        medicare_url=payload.facility.medicare_care_compare_url,
    )


def render_report_pdf(payload: ReportPayload, ai_summary: str | None = None) -> bytes:
    html = render_report_html(payload, ai_summary)
    return HTML(string=html).write_pdf()
