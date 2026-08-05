import os
import sys

def main():
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "docs"))
    html_file = os.path.join(docs_dir, "ForenSight_AI_Complete_Project_Manual.html")
    pdf_file = os.path.join(docs_dir, "ForenSight_AI_Complete_Project_Manual.pdf")
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>ForenSight AI — Complete Project Documentation Manual</title>
  <style>
    @page {
      size: A4;
      margin: 15mm;
      @bottom-right {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 8pt;
        font-family: sans-serif;
        color: #64748b;
      }
      @bottom-left {
        content: "ForenSight AI — Complete DFIR Platform Manual";
        font-size: 8pt;
        font-family: sans-serif;
        color: #64748b;
      }
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      color: #1e293b;
      line-height: 1.5;
      font-size: 9.5pt;
      margin: 0;
      padding: 0;
    }

    .cover {
      page-break-after: always;
      text-align: center;
      padding-top: 80px;
    }

    .cover h1 {
      font-size: 26pt;
      color: #1e1b4b;
      margin-bottom: 5px;
    }

    .cover .subtitle {
      font-size: 14pt;
      color: #4f46e5;
      font-weight: 600;
      margin-bottom: 40px;
    }

    .cover .meta-box {
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      padding: 20px;
      max-width: 450px;
      margin: 0 auto;
      background: #f8fafc;
      text-align: left;
      font-size: 9pt;
    }

    h2 {
      color: #1e1b4b;
      border-bottom: 2px solid #6366f1;
      padding-bottom: 4px;
      font-size: 14pt;
      margin-top: 25px;
      page-break-after: avoid;
    }

    h3 {
      color: #334155;
      font-size: 11pt;
      margin-top: 18px;
      page-break-after: avoid;
    }

    p, li {
      text-align: justify;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0;
      font-size: 8.5pt;
      page-break-inside: avoid;
    }

    th, td {
      border: 1px solid #cbd5e1;
      padding: 6px 10px;
      text-align: left;
    }

    th {
      background-color: #f1f5f9;
      color: #1e293b;
      font-weight: 600;
    }

    .code-block {
      background: #0f172a;
      color: #38bdf8;
      font-family: monospace;
      padding: 10px;
      border-radius: 6px;
      font-size: 8pt;
      white-space: pre;
      overflow-x: auto;
      margin: 10px 0;
    }

    .badge {
      font-weight: bold;
      color: #4f46e5;
    }
  </style>
</head>
<body>

  <!-- COVER PAGE -->
  <div class="cover">
    <h1>ForenSight AI</h1>
    <div class="subtitle">Complete Technical Architecture & Implementation Manual</div>
    <p>Comprehensive Documentation for Digital Forensics & AI Copilot Platform</p>

    <div class="meta-box" style="margin-top: 60px;">
      <p><strong>System Version:</strong> 1.0.0 (Production Release)</p>
      <p><strong>Core Stack:</strong> FastAPI, React (Vite), MongoDB, Neo4j, FAISS, Groq LLM</p>
      <p><strong>Scope:</strong> End-to-End Pipeline, Database Schemas, API Endpoints, AI RAG Architecture</p>
      <p><strong>Target Audience:</strong> Forensic Investigators, Security Engineers & Developers</p>
    </div>
  </div>

  <!-- SECTION 1: EXECUTIVE OVERVIEW -->
  <h2>1. Executive Platform Overview</h2>
  <p><strong>ForenSight AI</strong> is an event-driven Digital Forensics & Incident Response (DFIR) platform designed to automate evidence ingestion, event normalization, threat detection, and AI-assisted investigation. It enables cyber incident responders to analyze large volumes of multi-format forensic evidence (PCAP, SQLite, CSV, JSON, TXT/LOG) in seconds rather than hours.</p>
  
  <h3>Key Investigator Capabilities</h3>
  <ul>
    <li><strong>Multi-Format Evidence Ingestion:</strong> Automatic parsing of Network Captures (.pcap, .pcapng), Browser History Databases (.sqlite), Log Files (.csv, .json, .txt), and Threat Hashes (.md5, .sha256).</li>
    <li><strong>Automated Knowledge Graph Construction:</strong> Real-time mapping of processes, parent-child relationships, network sockets, registry modifications, and domain lookups into Neo4j execution trees.</li>
    <li><strong>Isolation Forest Anomaly Detection:</strong> Machine learning algorithms that evaluate event attributes to assign risk scores and flag outlier activities.</li>
    <li><strong>FAISS Vector Search Engine:</strong> L2-normalized sentence embeddings enabling natural language semantic search across millions of historical log records.</li>
    <li><strong>Interactive AI Copilot (Groq LLM + Fallback):</strong> Dual-engine AI query system using Llama-3.3-70B via Groq for instant answers with real-time SSE streaming, backed by a 100% offline local report generator fallback.</li>
  </ul>

  <!-- SECTION 2: ARCHITECTURE & PIPELINE -->
  <h2>2. System Architecture & Processing Pipeline</h2>
  <p>The platform follows an event-driven microservices architecture where heavy CPU/IO parsing and vector calculations run asynchronously in background thread executors to keep main API loops responsive.</p>

  <div class="code-block">
+-----------------------------------------------------------------------------------+
|                            FORENSIGHT PROCESSING PIPELINE                         |
+-----------------------------------------------------------------------------------+
| 1. UPLOAD & MINIO S3 STORAGE                                                     |
|    Investigator upload -> SHA-256 calculation -> MinIO S3 Object Storage           |
|                                                                                   |
| 2. FORMAT DETECTION & ASYNC PARSING                                               |
|    Magic Bytes detection -> Scapy / SQLite / CSV DictReader thread executors      |
|                                                                                   |
| 3. MONGODB BULK INGESTION                                                         |
|    SAO (Subject-Action-Object) normalization -> Bulk MongoDB write (PARSED status)|
|                                                                                   |
| 4. NEO4J GRAPH LINEAGE SYNC & CORRELATIONS                                        |
|    EntityRelationshipExtractor -> Neo4j SPAWNED/CONNECTED_TO edges -> Cypher rules|
|                                                                                   |
| 5. ML ANOMALY & FAISS VECTOR SEARCH INDEXING                                      |
|    Isolation Forest scoring -> SentenceTransformer (MiniLM) -> FAISS Index build  |
+-----------------------------------------------------------------------------------+
  </div>

  <!-- SECTION 3: FILE BY FILE CODEBASE DIRECTORY -->
  <h2>3. Complete File-by-File Codebase Directory</h2>
  <table>
    <thead>
      <tr>
        <th>File Path</th>
        <th>Category</th>
        <th>Description & Operational Logic</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>backend/app/main.py</td>
        <td><span class="badge">Core</span></td>
        <td>FastAPI app initialization, DB connection lifecycle management (MongoDB, Neo4j, Redis, MinIO), CORS/GZip middleware, startup evidence recovery.</td>
      </tr>
      <tr>
        <td>backend/app/config.py</td>
        <td><span class="badge">Core</span></td>
        <td>Pydantic BaseSettings loading system env vars (GROQ_API_KEY, MONGODB_URI, NEO4J_URI, MINIO_*, JWT_SECRET).</td>
      </tr>
      <tr>
        <td>backend/app/api/evidence.py</td>
        <td><span class="badge">API</span></td>
        <td>SHA-256 hashing, MinIO S3 upload, background parsing pipeline trigger, reprocess, and cascading deletion (S3, Mongo, Neo4j, FAISS).</td>
      </tr>
      <tr>
        <td>backend/app/api/chat.py</td>
        <td><span class="badge">API</span></td>
        <td>AI Copilot endpoints. Non-streaming POST + real-time Server-Sent Events (SSE) token streaming (GET /copilot/stream).</td>
      </tr>
      <tr>
        <td>backend/app/api/graph.py</td>
        <td><span class="badge">API</span></td>
        <td>Knowledge Graph API. Serves nodes & edges for Cytoscape.js canvas rendering, shortest path lookups, and neighborhood expansion.</td>
      </tr>
      <tr>
        <td>backend/app/api/events.py</td>
        <td><span class="badge">API</span></td>
        <td>Timeline events API. Queries MongoDB events with severity/type filters and safe Pydantic field fallbacks.</td>
      </tr>
      <tr>
        <td>backend/app/api/correlations.py</td>
        <td><span class="badge">API</span></td>
        <td>Graph correlation engine route. Returns detected attack chains, LOLBin executions, registry persistence, and threat scores.</td>
      </tr>
      <tr>
        <td>backend/app/api/cases.py</td>
        <td><span class="badge">API</span></td>
        <td>Case management (create case, list by org, update status, case overview metrics).</td>
      </tr>
      <tr>
        <td>backend/app/api/auth.py</td>
        <td><span class="badge">API</span></td>
        <td>Authentication API (login, register, JWT token issue, password reset, token validation).</td>
      </tr>
      <tr>
        <td>backend/app/parsers/pcap_parser.py</td>
        <td><span class="badge">Parser</span></td>
        <td>Parses binary .pcap/.pcapng network packet captures using Scapy into network IP socket & DNS event records.</td>
      </tr>
      <tr>
        <td>backend/app/parsers/browser_parser.py</td>
        <td><span class="badge">Parser</span></td>
        <td>Ingests Chrome/Edge SQLite databases (History, Downloads, Logins) and extracts domain visits and credentials.</td>
      </tr>
      <tr>
        <td>backend/app/parsers/csv_parser.py</td>
        <td><span class="badge">Parser</span></td>
        <td>CSV parser with alias column detection (timestamp, subject, action, object, IP, PID).</td>
      </tr>
      <tr>
        <td>backend/app/parsers/extractor.py</td>
        <td><span class="badge">Parser</span></td>
        <td>EntityRelationshipExtractor deriving Neo4j nodes (Process, Domain, IP, File) and edges (SPAWNED, CONNECTED_TO) from events.</td>
      </tr>
      <tr>
        <td>backend/app/services/ai/copilot.py</td>
        <td><span class="badge">AI</span></td>
        <td>Main Copilot orchestrator. Manages RAG context building, Groq API invocations, token streaming, and fallback execution.</td>
      </tr>
      <tr>
        <td>backend/app/services/copilot/groq_provider.py</td>
        <td><span class="badge">AI</span></td>
        <td>Async Groq LLM client (llama-3.3-70b-versatile) with retry backoff, timeout handling, and refusal detection.</td>
      </tr>
      <tr>
        <td>backend/app/services/copilot/query_router.py</td>
        <td><span class="badge">AI</span></td>
        <td>Classifier & fast-path executor for 12 query types (file sizes, case counts, graph attack chains, greetings, etc.).</td>
      </tr>
      <tr>
        <td>backend/app/services/copilot/report_generator.py</td>
        <td><span class="badge">AI</span></td>
        <td>Local deterministic fallback engine. Builds structured Markdown DFIR reports when external LLMs are unavailable.</td>
      </tr>
      <tr>
        <td>backend/app/services/ai/vector_store.py</td>
        <td><span class="badge">AI</span></td>
        <td>FAISS vector store engine. Deduplicates event sentences, encodes via all-MiniLM-L6-v2, and executes cosine similarity searches.</td>
      </tr>
      <tr>
        <td>frontend/src/pages/CaseDetailPage.jsx</td>
        <td><span class="badge">UI</span></td>
        <td>Main case workspace page. Features top navigation tab bar and 4 interactive dashboard quick-action cards.</td>
      </tr>
      <tr>
        <td>frontend/src/components/graph/GraphView.jsx</td>
        <td><span class="badge">UI</span></td>
        <td>Cytoscape.js interactive graph canvas supporting hierarchical process trees, force-directed views, and neighbor highlighting.</td>
      </tr>
      <tr>
        <td>frontend/src/components/graph/NodeDetailsPanel.jsx</td>
        <td><span class="badge">UI</span></td>
        <td>Side panel inspecting selected node properties featuring a 2-state "Focus Neighborhood" / "Cancel Focus Neighborhood" toggle button.</td>
      </tr>
      <tr>
        <td>frontend/src/components/chat/ChatPanel.jsx</td>
        <td><span class="badge">UI</span></td>
        <td>Interactive AI investigator chat interface supporting SSE token streaming, Markdown response formatting, and clickable evidence citations.</td>
      </tr>
    </tbody>
  </table>

  <!-- SECTION 4: AI & RAG ARCHITECTURE -->
  <h2>4. AI Copilot RAG & Defense Architecture</h2>
  <p>The Copilot uses a multi-layered Retrieval-Augmented Generation (RAG) architecture with prompt-injection defense fencing:</p>
  <ul>
    <li><strong>Intent Classification:</strong> Incoming questions are evaluated by <code>query_router.py</code> to immediately satisfy factual queries (e.g. file size comparisons, case statistics, evidence lists) via direct database queries.</li>
    <li><strong>Context Building:</strong> Complex analytical queries trigger <code>context_builder.py</code>, which aggregates case metadata, Isolation Forest anomalies, Neo4j graph correlations, and top FAISS semantic vector matches.</li>
    <li><strong>Prompt Defense Fencing:</strong> Raw forensic logs are safely wrapped inside <code>&lt;FORENSIC_EVIDENCE&gt;</code> XML tags with system instructions forbidding the LLM from executing untrusted log strings as instructions.</li>
    <li><strong>Fault-Tolerant Fallback:</strong> If the Groq API experiences timeouts, rate limits, or network errors, the system automatically falls back to <code>report_generator.py</code> to synthesize a complete, deterministic forensic report without crashing the UI.</li>
  </ul>

</body>
</html>
"""

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated HTML manual: {html_file}")

    # Try generating PDF using headless browser or WeasyPrint
    pdf_generated = False
    try:
        from weasyprint import HTML
        HTML(html_file).write_pdf(pdf_file)
        pdf_generated = True
        print(f"Successfully generated PDF via WeasyPrint: {pdf_file}")
    except Exception as e:
        print(f"WeasyPrint unavailable ({e}), trying Playwright/Selenium/Headless browser...")

    if not pdf_generated:
        try:
            import subprocess
            # Try msedge or chrome headless to print to pdf
            edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            if not os.path.exists(edge_path):
                edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
            
            if os.path.exists(edge_path):
                cmd = f'"{edge_path}" --headless --disable-gpu --print-to-pdf="{pdf_file}" "{html_file}"'
                subprocess.run(cmd, shell=True, check=True)
                pdf_generated = True
                print(f"Successfully generated PDF via Edge headless: {pdf_file}")
        except Exception as e:
            print(f"Headless print error: {e}")

    # Clean up unwanted docs files except processing_pipeline_diagram.html & project_architecture_summary.html & new PDF/HTML manual
    keep_files = {
        "processing_pipeline_diagram.html",
        "project_architecture_summary.html",
        "ForenSight_AI_Complete_Project_Manual.html",
        "ForenSight_AI_Complete_Project_Manual.pdf",
    }

    for item in os.listdir(docs_dir):
        if item not in keep_files:
            file_path = os.path.join(docs_dir, item)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Deleted extra file: {item}")
            except Exception as e:
                print(f"Could not delete {item}: {e}")

if __name__ == "__main__":
    main()
