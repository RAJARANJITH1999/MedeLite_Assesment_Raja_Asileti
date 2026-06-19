from fastapi import APIRouter, Response

from app.schemas.report import ExportRequest
from app.services.docx_export import render_report_docx
from app.services.pdf import render_report_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/pdf")
async def export_pdf(request: ExportRequest) -> Response:
    payload = request.to_report_payload()
    pdf_bytes = render_report_pdf(payload, ai_summary=request.ai_summary)
    filename = f"facility-assessment-{payload.facility.ccn}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/docx")
async def export_docx(request: ExportRequest) -> Response:
    payload = request.to_report_payload()
    docx_bytes = render_report_docx(payload, ai_summary=request.ai_summary)
    filename = f"facility-assessment-{payload.facility.ccn}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
