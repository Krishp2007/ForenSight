from fastapi import APIRouter, HTTPException, status, Depends, Response
from fastapi.responses import HTMLResponse
from bson import ObjectId
import logging

from backend.app.services.reports.pdf_compiler import ReportCompiler, weasyprint_available
from backend.app.repositories.case_repository import CaseRepository
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.rbac import require_viewer
from backend.app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["reports"])


@router.get("/cases/{case_id}/report/html", response_class=HTMLResponse)
async def get_html_report_preview(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Viewer+ can view the HTML report."""
    require_viewer(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")
    try:
        html_str = await ReportCompiler.compile_html_report(case_id, current_user.organization_id)
        return HTMLResponse(content=html_str)
    except Exception as e:
        logger.error(f"Failed compiling HTML report: {e}")
        raise HTTPException(status_code=500, detail=f"Report rendering error: {e}")


@router.get("/cases/{case_id}/report/pdf")
async def download_pdf_report(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Viewer+ can download the PDF report."""
    require_viewer(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    if not weasyprint_available:
        raise HTTPException(
            status_code=424,
            detail=(
                "WeasyPrint system libraries are not available on this host. "
                "Use the HTML preview endpoint instead: /api/v1/cases/{case_id}/report/html "
                "and print to PDF from your browser (Ctrl+P)."
            ),
        )
    try:
        pdf_bytes = await ReportCompiler.compile_pdf_report(case_id, current_user.organization_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=ForenSight_Report_{case_id}.pdf"},
        )
    except Exception as e:
        logger.error(f"Failed generating PDF: {e}")
        raise HTTPException(status_code=500, detail=f"PDF compiler error: {e}")
