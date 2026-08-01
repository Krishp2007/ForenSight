import os
import logging
from datetime import datetime
import re
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

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
        Build a meaningful HTML executive summary from the assembled report context.
        Used when no LLM (Gemini/Ollama) is configured.
        """
        case = ctx.get("case", {})
        total = ctx.get("total_events", 0)
        anomalies_count = ctx.get("anomalies_count", 0)
        critical_high = ctx.get("critical_high_count", 0)
        span_hours = ctx.get("span_hours", 0)
        enriched = ctx.get("enriched_techniques", [])
        correlations = ctx.get("correlations", [])
        anomalies = ctx.get("anomalies", [])

        tactics = list({t.get("tactic", "") for t in enriched if t.get("tactic")})
        technique_ids = [t.get("id", "") for t in enriched[:5]]

        severity_counts: Dict[str, int] = {}
        for a in anomalies:
            sev = (a.get("severity") or "info").lower()
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        lines = []
        lines.append("<h3>Executive Summary</h3>")
        lines.append(
            f"<p>Case <strong>{case.get('title', 'N/A')}</strong> was analysed by the "
            f"ForenSight ML &amp; Graph engine. A total of <strong>{total:,}</strong> log events "
            f"were ingested, covering <strong>{span_hours} hours</strong> of activity. "
            f"The Isolation Forest anomaly detector flagged <strong>{anomalies_count}</strong> "
            f"outlying events"
        )
        if critical_high:
            lines[-1] += (
                f", of which <strong>{critical_high}</strong> carry a "
                "<em>Critical</em> or <em>High</em> severity rating</p>"
            )
        else:
            lines[-1] += ", none of which reached Critical or High severity.</p>"

        if severity_counts:
            lines.append("<p><strong>Anomaly severity breakdown:</strong> " +
                ", ".join(
                    f"<strong>{cnt}</strong> {sev}"
                    for sev, cnt in sorted(severity_counts.items(),
                                           key=lambda x: ["critical","high","medium","low","info"].index(x[0])
                                           if x[0] in ["critical","high","medium","low","info"] else 99)
                ) + ".</p>")

        if correlations:
            rules = list({c.get("rule", "UNKNOWN") for c in correlations})
            lines.append(
                f"<p>The graph correlation engine produced "
                f"<strong>{len(correlations)}</strong> derived relationships across "
                f"<strong>{len(rules)}</strong> rule(s): "
                + ", ".join(f"<em>{r.replace('_', ' ').title()}</em>" for r in rules[:5])
                + ("." if len(rules) <= 5 else f" and {len(rules)-5} more.")
                + "</p>"
            )

        if enriched:
            lines.append(
                f"<p><strong>{len(enriched)}</strong> MITRE ATT&amp;CK technique(s) were "
                "identified during this investigation"
            )
            if tactics:
                lines[-1] += f", spanning tactics: <strong>{', '.join(tactics)}</strong>"
            if technique_ids:
                lines[-1] += (
                    ". Observed techniques include: "
                    + ", ".join(f"<code>{t}</code>" for t in technique_ids)
                    + ("." if len(enriched) <= 5 else f" and {len(enriched)-5} more.")
                )
            else:
                lines[-1] += ".</p>"
            if not lines[-1].endswith("</p>"):
                lines[-1] += "</p>"

        lines.append(
            "<p style='color:#64748b; font-size:8pt; margin-top:10px;'>"
            "ℹ️ <em>This summary was generated by the local ForenSight analysis engine. "
            "Configure a Gemini API key or an Ollama endpoint to enable AI-narrative "
            "investigation guidance and natural-language findings.</em></p>"
        )
        return "\n".join(lines)

    @classmethod
    async def compile_html_report(cls, case_id: str, org_id: str) -> str:
        """Render the Jinja2 report template with case metadata, returning a full HTML string."""
        context = await cls.get_report_context(case_id, org_id)
        
        # Load Jinja2 template via Environment for full filter support
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
        pdf_bytes = await loop.run_in_executor(
            None,
            lambda: HTML(string=html_content).write_pdf()
        )
        return pdf_bytes
