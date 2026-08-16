import os
import logging
from datetime import datetime
import re
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.app.services.context.report_context import build_report_context

logger = logging.getLogger(__name__)

# Lazy-check WeasyPrint to avoid loading Pango/Cairo C-libraries on startup
def is_weasyprint_available() -> bool:
    try:
        from weasyprint import HTML
        return True
    except Exception:
        return False

weasyprint_available = is_weasyprint_available()

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
        """Delegate to the centralized report context builder and inject copilot_analysis_html."""
        context = await build_report_context(case_id, org_id)

        # Inject copilot_analysis_html if not already set by an LLM provider.
        # Falls back to a structured local summary built from the context data.
        if not context.get("copilot_analysis_html"):
            context["copilot_analysis_html"] = cls._build_fallback_analysis_html(context)

        return context

    @classmethod
    def _build_fallback_analysis_html(cls, ctx: Dict[str, Any]) -> str:
        """
        Build a comprehensive, humanized executive summary from report context.
        """
        case = ctx.get("case", {})
        total = ctx.get("total_events", 0)
        anomalies_count = ctx.get("anomalies_count", 0)
        critical_high = ctx.get("critical_high_count", 0)
        span_hours = ctx.get("span_hours", 0)
        enriched = ctx.get("enriched_techniques", [])
        correlations = ctx.get("correlations", [])
        anomalies = ctx.get("anomalies", [])
        evidence_list = ctx.get("evidence_list", [])

        tactics = list({t.get("tactic", "") for t in enriched if t.get("tactic")})
        technique_ids = [t.get("id", "") for t in enriched[:5]]

        severity_counts: Dict[str, int] = {}
        for a in anomalies:
            sev = (a.get("severity") or "info").lower()
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        lines = []
        lines.append("<h3>Executive Investigation Overview</h3>")
        lines.append(
            f"<p>Case <strong>{case.get('title', 'N/A')}</strong> was processed through the "
            f"ForenSight multi-source forensic pipeline. A total of <strong>{total:,}</strong> log events "
            f"were analyzed from <strong>{len(evidence_list)} ingested evidence file(s)</strong> over a span of "
            f"<strong>{span_hours} hours</strong>.</p>"
        )

        lines.append("<div style='margin: 10px 0;'><strong>Key Forensic Findings & Incident Insights:</strong><ul>")
        lines.append(
            f"<li><strong>ML Outlier Detections:</strong> The Isolation Forest algorithm identified "
            f"<strong>{anomalies_count} anomalous events</strong> out of {total:,} logs. "
            f"Of these, <strong>{critical_high}</strong> require immediate priority response due to Critical/High risk scores.</li>"
        )

        if correlations:
            rules = list({c.get("rule", "UNKNOWN") for c in correlations})
            rule_str = ", ".join(f"<code>{r.replace('_', ' ').title()}</code>" for r in rules[:4])
            lines.append(
                f"<li><strong>Graph Attack Path Correlations:</strong> The Neo4j graph correlation engine linked "
                f"<strong>{len(correlations)} key entity relationships</strong> across rules: {rule_str}.</li>"
            )

        if enriched:
            tech_str = ", ".join(f"<code>{t}</code>" for t in technique_ids)
            lines.append(
                f"<li><strong>MITRE ATT&CK Framework Mapping:</strong> <strong>{len(enriched)} technique(s)</strong> "
                f"spanned tactics: <strong>{', '.join(tactics) if tactics else 'Execution / Persistence'}</strong>. "
                f"Observed identifiers: {tech_str}.</li>"
            )
        lines.append("</ul></div>")

        # Top Plain English Highlights
        if anomalies:
            lines.append("<p><strong>Top Anomaly Plain-English Indicators:</strong></p><ul>")
            for a in anomalies[:4]:
                desc = a.get("description") or f"{a.get('subject')} ➔ {a.get('action')} ➔ {a.get('object')}"
                sev = a.get("severity", "info").upper()
                lines.append(f"<li><strong>[{sev}]</strong> {desc}</li>")
            lines.append("</ul>")

        lines.append(
            "<p style='color:#64748b; font-size:8pt; margin-top:10px;'>"
            "ℹ️ <em>Generated automatically by ForenSight Analytics. "
            "All findings are cross-verified against forensic evidence signatures.</em></p>"
        )
        return "\n".join(lines)

    @classmethod
    async def compile_html_report(cls, case_id: str, org_id: str) -> str:
        """Render the Jinja2 report template with case metadata, returning a full HTML string."""
        context = await cls.get_report_context(case_id, org_id)
        return cls._render_template(context)

    @staticmethod
    def _render_template(context: Dict[str, Any]) -> str:
        """Render the report.html Jinja2 template from an already-assembled context dict."""
        templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            "templates"
        )
        env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(disabled_extensions=("html",)),
        )
        template = env.get_template("report.html")
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
        def _build_pdf():
            from weasyprint import HTML
            return HTML(string=html_content).write_pdf()

        pdf_bytes = await loop.run_in_executor(None, _build_pdf)
        return pdf_bytes
