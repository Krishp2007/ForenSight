import logging
import asyncio
import os
import google.generativeai as genai
from typing import List, Dict, Any, Optional

from backend.app.config import settings
from backend.app.repositories.case_repository import CaseRepository
from backend.app.db.mongodb import db_client
from backend.app.services.ai.vector_store import VectorStore

logger = logging.getLogger(__name__)

class CopilotService:
    @staticmethod
    def get_fallback_summary(case: Dict[str, Any], anomalies: List[Dict[str, Any]], semantic_context: List[Dict[str, Any]], question: Optional[str]) -> str:
        """Provide a high-quality analysis summary if Gemini API is offline or unconfigured."""
        summary = []
        summary.append(f"# 🛡️ Forensic Audit: {case.get('title', 'Investigation Case')}")
        summary.append(f"**Description:** {case.get('description', 'No description provided')}\n")
        
        if question:
            summary.append(f"### 💬 Contextual Query: '{question}'")
            if semantic_context:
                summary.append("Matched timeline context events:")
                for sc in semantic_context[:3]:
                    summary.append(f"- **{sc.get('timestamp')}**: {sc.get('subject')} -> [{sc.get('action')}] -> {sc.get('object')} (Match Distance: {sc.get('distance', 0.0):.4f})")
            else:
                summary.append("- *No semantically similar events found.*")
            summary.append("")
            
        summary.append(f"### 🌲 Machine Learning Anomaly Detections")
        if anomalies:
            summary.append(f"Out of {len(anomalies)} analyzed log events, the following anomalies were isolated:")
            for idx, a in enumerate(anomalies[:5]):
                ts = a.get("timestamp")
                subj = a.get("subject")
                act = a.get("action")
                obj = a.get("object")
                sev = a.get("severity")
                score = a.get("anomaly_score", 0.0)
                summary.append(f"{idx+1}. **[{sev.upper()}]** at `{ts}`: **{subj}** performed `{act}` on `{obj}` (Anomaly Score: `{score:.4f}`)")
        else:
            summary.append("- *No major outliers detected in current timelines.*")
            
        summary.append("\n### 🔍 Initial Audit & Remediation Advice")
        summary.append("1. **Credential Scrutiny**: Inspect logins surrounding any highlighted outlier times.")
        summary.append("2. **Process Isolation**: Verify authority for execution paths tagged as high anomaly score.")
        summary.append("3. **Log Expansion**: Gather network capture dumps for hosts showing anomalous target ports.")
        summary.append("\n*Note: This report is compiled using local heuristic fallbacks because Gemini API credentials are not active.*")
        
        return "\n".join(summary)

    @classmethod
    async def analyze_case_timeline(cls, case_id: str, org_id: str, question: Optional[str] = None) -> str:
        """Compile case history, run semantic index searches, and generate a Gemini response (with local fallbacks)."""
        logger.info(f"Generating copilot summary for case {case_id}")
        
        # 1. Fetch Case details
        case = await CaseRepository.get_by_id(case_id, org_id)
        if not case:
            return "Case not found or access denied."
            
        # 2. Fetch Top Anomalies from MongoDB
        cursor = db_client.db["events"].find({
            "case_id": case["_id"],
            "organization_id": case["organization_id"],
            "is_anomaly": True
        }).sort("anomaly_score", -1)
        anomalies = await cursor.to_list(length=30)
        
        # 3. Retrieve semantic context if query provided
        semantic_context = []
        if question:
            semantic_context = await VectorStore.search_similar_events(case_id, org_id, query=question, limit=5)
            
        # 4. Formulate Prompt (shared by both Gemini and Ollama)
        prompt_lines = []
        prompt_lines.append(f"You are Antigravity, a forensic investigator assistant analyzing case logs for the 'ForenSight AI' platform.")
        prompt_lines.append(f"Analyze the following security investigation details:\n")
        prompt_lines.append(f"Case Title: {case.get('title')}")
        prompt_lines.append(f"Case Description: {case.get('description')}")
        
        if question:
            prompt_lines.append(f"\nThe investigator is asking this specific question: '{question}'")
            prompt_lines.append("\nHere are the semantically relevant events found via FAISS similarity matching:")
            for sc in semantic_context:
                prompt_lines.append(f"- At {sc.get('timestamp')}, Subject '{sc.get('subject')}' performed '{sc.get('action')}' on Object '{sc.get('object')}'. Severity: {sc.get('severity')}.")
                
        prompt_lines.append(f"\nHere are the top anomalous outliers flagged by our Machine Learning (Isolation Forest) model:")
        for idx, a in enumerate(anomalies[:10]):
            prompt_lines.append(f"- At {a.get('timestamp')}, Subject '{a.get('subject')}' did '{a.get('action')}' to '{a.get('object')}'. Severity: {a.get('severity')}. Anomaly Score: {a.get('anomaly_score', 0.0):.4f}.")
            
        prompt_lines.append("\nTask: Based on these anomalies and matching logs, write a detailed forensic analysis report in Markdown. Highlight potential attack patterns (like execution, persistence, or data staging), specify which nodes are suspicious, and recommend immediate containment steps. Keep your tone professional, concise, and objective. If the question is a general conversation or math query (like 'how are you' or '2+2'), reply to it naturally while linking it to the investigation context if relevant.")
        
        prompt = "\n".join(prompt_lines)

        # Check LLM provider choice from config setting
        llm_provider = os.getenv("LLM_PROVIDER", settings.LLM_PROVIDER).lower()
        
        if llm_provider == "local":
            logger.info("LLM provider explicitly set to 'local'. Using local heuristic analysis.")
            return cls.get_fallback_summary(case, anomalies, semantic_context, question)
            
        elif llm_provider == "ollama":
            import httpx
            logger.info(f"Using local Ollama LLM provider ({settings.OLLAMA_MODEL}) at {settings.OLLAMA_HOST}")
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    payload = {
                        "model": settings.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False
                    }
                    response = await client.post(f"{settings.OLLAMA_HOST}/api/generate", json=payload)
                    if response.status_code == 200:
                        return response.json().get("response", "No response returned from Ollama.")
                    else:
                        raise ValueError(f"Ollama server returned status code {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Local Ollama invocation failed: {e}. Falling back to local heuristic analysis.")
                return cls.get_fallback_summary(case, anomalies, semantic_context, question)
                
        # Default/Gemini Path
        api_key = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY)
        if not api_key or api_key == "change_me_in_production":
            logger.info("Gemini API key not configured. Falling back to local analysis.")
            return cls.get_fallback_summary(case, anomalies, semantic_context, question)
            
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: model.generate_content(prompt)
            )
            
            if response and response.text:
                return response.text
            else:
                raise ValueError("Empty response returned from Google Gemini.")
                
        except Exception as e:
            logger.error(f"Gemini API invocation failed: {e}. Using high-quality local fallback analysis.")
            return cls.get_fallback_summary(case, anomalies, semantic_context, question)
