import os
import logging
from datetime import datetime
import re
from typing import Dict, Any

from jinja2 import Template

from backend.app.repositories.case_repository import CaseRepository
from backend.app.repositories.graph_repository import GraphRepository
from backend.app.services.ai.copilot import CopilotService
from backend.app.db.mongodb import db_client
from bson import ObjectId

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
        """Gather all database timeline logs, anomaly counts, graph lists and AI summaries for the case."""
        case = await CaseRepository.get_by_id(case_id, org_id)
        if not case:
            raise ValueError("Case not found or access denied")
            
        # 1. Total event stats
        total_events = await db_client.db["events"].count_documents({
            "case_id": case["_id"],
            "organization_id": case["organization_id"]
        })
        
        # 2. Anomaly counts
        anomalies_count = await db_client.db["events"].count_documents({
            "case_id": case["_id"],
            "organization_id": case["organization_id"],
            "is_anomaly": True
        })
        
        # 3. Critical/High severity counts
        critical_high_count = await db_client.db["events"].count_documents({
            "case_id": case["_id"],
            "organization_id": case["organization_id"],
            "severity": {"$in": ["critical", "high"]}
        })
        
        # 4. Top anomalies list
        cursor = db_client.db["events"].find({
            "case_id": case["_id"],
            "organization_id": case["organization_id"],
            "is_anomaly": True
        }).sort("anomaly_score", -1)
        anomalies = await cursor.to_list(length=100)
        
        # Format timestamps for display
        for a in anomalies:
            if isinstance(a.get("timestamp"), datetime):
                a["timestamp"] = a["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                
        # 5. Graph entities (Filter and limit to crucial connections to avoid massive PDF printouts)
        raw_graph = await GraphRepository.get_case_graph(case_id, org_id)
        raw_edges = raw_graph.get("edges", [])
        
        # Filter for anomalous or critical/high severity connections
        filtered_edges = [
            e for e in raw_edges 
            if e.get("is_anomaly") or e.get("severity") in ("critical", "high")
        ]
        
        # Sort so that anomalies and critical connections appear at the top
        def get_sort_key(edge):
            is_anom = 1 if edge.get("is_anomaly") else 0
            sev = 2 if edge.get("severity") == "critical" else (1 if edge.get("severity") == "high" else 0)
            return (is_anom, sev)
            
        filtered_edges.sort(key=get_sort_key, reverse=True)
        filtered_edges = filtered_edges[:45]  # Cap at 45 crucial threat links
        
        # Keep nodes associated with the active edges
        active_nodes = set()
        for edge in filtered_edges:
            active_nodes.add(edge["source"])
            active_nodes.add(edge["target"])
            
        filtered_nodes = [
            n for n in raw_graph.get("nodes", []) 
            if n["id"] in active_nodes
        ]
        
        graph = {
            "nodes": filtered_nodes,
            "edges": filtered_edges
        }
        
        # 6. Copilot analysis report
        copilot_markdown = await CopilotService.analyze_case_timeline(case_id, org_id)
        copilot_html = markdown_to_html(copilot_markdown)
        
        return {
            "case": case,
            "case_id": case_id,
            "total_events": total_events,
            "anomalies_count": anomalies_count,
            "critical_high_count": critical_high_count,
            "anomalies": anomalies,
            "graph": graph,
            "copilot_analysis_html": copilot_html,
            "date_generated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        }

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
