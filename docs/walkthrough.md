# Walkthrough — Complete ForenSight AI Documentation Generation

We have compiled full, in-depth technical documentation for the entire **ForenSight AI Digital Forensics & AI Copilot Platform**.

---

## 📄 Created Documentation Files

1. **Full Technical Documentation Manual (HTML & Print-Ready PDF Layout)**:
   * [`docs/ForenSight_AI_Platform_Full_Documentation.html`](file:///d:/ForenSight/ForenSight/docs/ForenSight_AI_Platform_Full_Documentation.html)
2. **Automated PDF Generator Script**:
   * [`generate_pdf_docs.py`](file:///d:/ForenSight/ForenSight/generate_pdf_docs.py)
3. **Implementation & Technical Plan**:
   * [`docs/implementation_plan.md`](file:///d:/ForenSight/ForenSight/docs/implementation_plan.md)

---

## 📚 Document Coverage & Summary

The generated documentation spans **12 comprehensive sections**:

| Section # | Title | Key Contents Covered |
| :--- | :--- | :--- |
| **Section 1** | Executive Overview & Core Capabilities | Mission statement, platform scope, core features matrix (evtx, pcap, PyOD, Neo4j, Qdrant, Gemini AI). |
| **Section 2** | High-Level Architecture & Microservices Matrix | ASCII architecture diagram, 7-microservice breakdown (Web, API, MongoDB, Neo4j, Qdrant, Redis, MinIO). |
| **Section 3** | Evidence Ingestion & Forensic Parsing Pipeline | Chain of custody, SHA-256 calculation, file routing, parser modules (`evtx_parser`, `pcap_parser`, `browser_parser`, `csv_parser`, `json_parser`, `text_parser`). |
| **Section 4** | Machine Learning & Anomaly Detection Engine | PyOD HBOS algorithm details, anomaly scoring ($0.0 - 1.0$), heuristic threat detection rules (brute force, privilege escalation, log erasure). |
| **Section 5** | Knowledge Graph & Cross-Case Vector Intelligence | Neo4j Cypher entity node/relationship schemas, Qdrant dense vector store (384-dim embeddings), cross-case IoC correlation. |
| **Section 6** | AI Copilot & Natural Language Querying | Gemini 1.5/2.0 RAG pipeline architecture, context building, specialized modes (Timeline Explainer, Threat Analyst, Cypher Generator). |
| **Section 7** | Frontend SPA Architecture & Workflows | React 18 + Vite + Tailwind CSS + Lucide icons, page hierarchy, 7 interactive tabs in `CaseDetailPage.jsx`. |
| **Section 8** | Database Schemas & Data Models | Complete MongoDB collection schemas (`users`, `cases`, `evidence`, `events`, `audit_logs`). |
| **Section 9** | Complete REST API Reference | Exhaustive endpoint table with HTTP methods, route parameters, auth requirements for Auth, Cases, Evidence, Events, Chat, Graph, Similarity, Reports, Users. |
| **Section 10** | Security, RBAC & Multi-Tenant Isolation | JWT tokens, Bcrypt password hashing, 4-tier RBAC (`Admin`, `Investigator`, `Analyst`, `Viewer`), organizational data segregation. |
| **Section 11** | Production Deployment & Operations Blueprint | One-command `docker-compose.yml` deployment, `.env` reference, health check endpoints, Nginx SSL setup. |
| **Section 12** | Developer & Contributor Guide | Backend virtualenv setup, FastAPI server start, frontend Vite dev server, running `pytest` test suite. |

---

## 🖨️ How to Save as PDF

### Method A: Browser One-Click PDF Export (Recommended)
1. Open [`docs/ForenSight_AI_Platform_Full_Documentation.html`](file:///d:/ForenSight/ForenSight/docs/ForenSight_AI_Platform_Full_Documentation.html) in Microsoft Edge, Google Chrome, Firefox, or any web browser.
2. Press **`Ctrl + P`** (or `Cmd + P` on Mac).
3. Select Destination: **Save as PDF**.
4. Click **Save** to export `ForenSight_AI_Platform_Full_Documentation.pdf`.

### Method B: Command Line (Edge / WeasyPrint)
Run the generator script in your terminal:
```powershell
python d:\ForenSight\ForenSight\generate_pdf_docs.py
```
