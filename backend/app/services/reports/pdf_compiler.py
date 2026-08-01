import os
import logging
from datetime import datetime
import re
from typing import Dict, Any

from jinja2 import Template

from backend.app.services.context.report_context import build_report_context

logger = logging.getLogger(__name__)

# Try importing WeasyPrint, flag if missing or failing on Windows
weasyprint_available = True
try:
    from weasyprint import HTML
except Exception as e:
    logger.warning(f"WeasyPrint library import failed or is missing system dependencies: {e}. PDF generation will fall back to HTML previews.")
    weasyprint_available = False

def markdown_to_html(md_text: str) -> str:
    """Helper to convert markdown strings to HTML elements without external dependencies."""
    lines = md_text.split("\n")
    html_lines = []
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        
        # Headers
        if stripped.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1>{stripped[2:]}</h1>")
            
        # Bullet list items
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            item_text = stripped[2:]
            # Replace bold and code formats
            item_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", item_text)
            item_text = re.sub(r"`(.*?)`", r"<code>\1</code>", item_text)
            html_lines.append(f"<li>{item_text}</li>")
            
        else:
            if in_list and stripped == "":
                html_lines.append("</ul>")
                in_list = False
            if stripped:
                p_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", stripped)
                p_text = re.sub(r"`(.*?)`", r"<code>\1</code>", p_text)
                html_lines.append(f"<p>{p_text}</p>")
                
    if in_list:
        html_lines.append("</ul>")
        
    return "\n".join(html_lines)

class ReportCompiler:
    @classmethod
    async def get_report_context(cls, case_id: str, org_id: str) -> Dict[str, Any]:
        """Delegate to the centralized report context builder."""
        return await build_report_context(case_id, org_id)

    @classmethod
    async def compile_html_report(cls, case_id: str, org_id: str) -> str:
        """Render the Jinja2 report template with case metadata, returning a full HTML string."""
        context = await cls.get_report_context(case_id, org_id)
        
        # Load Jinja2 template (located at backend/templates/report.html)
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            "templates", "report.html"
        )
        
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
            
        template = Template(template_content)
        return template.render(**context)

    @classmethod
    async def compile_pdf_report(cls, case_id: str, org_id: str) -> bytes:
        """Convert rendered HTML report string into binary PDF using WeasyPrint (falls back to HTML if dependencies are missing)."""
        html_content = await cls.compile_html_report(case_id, org_id)
        
        if not weasyprint_available:
            raise RuntimeError(
                "WeasyPrint is missing system level DLL libraries (Pango/Cairo) on this host. "
                "Please query the HTML preview report endpoint (/api/v1/cases/{case_id}/report/html) directly."
            )
            
        # Compile PDF binary in a separate thread pool executor
        import asyncio
        loop = asyncio.get_running_loop()
        pdf_bytes = await loop.run_in_executor(
            None,
            lambda: HTML(string=html_content).write_pdf()
        )
        return pdf_bytes
