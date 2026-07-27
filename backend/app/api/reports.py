from fastapi import APIRouter, HTTPException, status, Depends, Response
from fastapi.responses import HTMLResponse
from bson import ObjectId
import logging

from backend.app.services.reports.pdf_compiler import ReportCompiler, weasyprint_available
from backend.app.repositories.case_repository import CaseRepository
from backend.app.auth.dependencies import get_current_user
from backend.app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["reports"])

@router.get("/cases/{case_id}/report/html", response_class=HTMLResponse)
async def get_html_report_preview(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Retrieve a fully compiled, beautifully styled HTML incident report preview for a forensic case."""
    if not ObjectId.is_valid(case_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid case ID format"
        )
        
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or access denied"
        )
        
    try:
        html_str = await ReportCompiler.compile_html_report(case_id, current_user.organization_id)
        return HTMLResponse(content=html_str, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed compiling HTML report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report rendering error: {str(e)}"
        )

@router.get("/cases/{case_id}/report/pdf")
async def download_pdf_report(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Generate and download a print-ready binary PDF incident report using WeasyPrint (with fallback suggestions)."""
    if not ObjectId.is_valid(case_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid case ID format"
        )
        
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or access denied"
        )
        
    if not weasyprint_available:
        # Graceful dependency warning response
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail=(
                "WeasyPrint system level libraries (Pango/Cairo) are not active on this Windows host. "
                "Please query the HTML preview endpoint: /api/v1/cases/{case_id}/report/html. "
                "You can print that HTML preview to a PDF directly from your web browser using Ctrl+P."
            )
        )
        
    try:
        pdf_bytes = await ReportCompiler.compile_pdf_report(case_id, current_user.organization_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=ForenSight_Report_{case_id}.pdf"
            }
        )
    except Exception as e:
        logger.error(f"Failed generating PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF compiler compilation error: {str(e)}"
        )
