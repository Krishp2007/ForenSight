import os
import sys
import subprocess
import shutil

HTML_DOC_PATH = os.path.abspath("d:/ForenSight/ForenSight/docs/ForenSight_AI_Platform_Full_Documentation.html")
PDF_DOC_PATH = os.path.abspath("d:/ForenSight/ForenSight/docs/ForenSight_AI_Platform_Full_Documentation.pdf")

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ForenSight AI — Full Technical Platform Documentation</title>
<style>
  @page {
    size: A4;
    margin: 20mm 15mm 20mm 15mm;
    @bottom-right {
      content: "Page " counter(page) " of " counter(pages);
      font-size: 9pt;
      font-family: 'Segoe UI', sans-serif;
      color: #64748b;
    }
    @bottom-left {
      content: "ForenSight AI Platform Documentation v1.0.0";
      font-size: 9pt;
      font-family: 'Segoe UI', sans-serif;
      color: #64748b;
    }
  }

  :root {
    --primary: #0F172A;
    --accent: #1F3A5F;
    --highlight: #0284C7;
    --highlight-light: #E0F2FE;
    --text: #1E293B;
    --text-muted: #64748B;
    --border: #E2E8F0;
    --bg-alt: #F8FAFC;
    --code-bg: #0F172A;
    --code-text: #F1F5F9;
  }

  * { box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    color: var(--text);
    line-height: 1.6;
    margin: 0;
    padding: 0;
    font-size: 10.5pt;
    background: #ffffff;
  }

  /* Cover Page */
  .cover-page {
    page-break-after: always;
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 60px 40px;
    background: linear-gradient(135deg, #0F172A 0%, #1F3A5F 100%);
    color: #ffffff;
    border-radius: 8px;
    margin-bottom: 40px;
  }
  .cover-brand {
    font-size: 42pt;
    font-weight: 800;
    letter-spacing: -1px;
    color: #38BDF8;
    margin-bottom: 10px;
  }
  .cover-title {
    font-size: 24pt;
    font-weight: 700;
    margin-bottom: 20px;
    color: #F8FAFC;
  }
  .cover-subtitle {
    font-size: 14pt;
    color: #94A3B8;
    max-width: 650px;
    margin-bottom: 60px;
    line-height: 1.5;
  }
  .cover-meta {
    font-size: 11pt;
    color: #CBD5E1;
    border-top: 1px solid rgba(255,255,255,0.2);
    padding-top: 25px;
    width: 80%;
  }

  /* Headings */
  h1 {
    font-size: 20pt;
    color: var(--accent);
    border-bottom: 2px solid var(--highlight);
    padding-bottom: 8px;
    margin-top: 35px;
    margin-bottom: 18px;
    page-break-after: avoid;
  }
  h2 {
    font-size: 15pt;
    color: var(--primary);
    margin-top: 25px;
    margin-bottom: 12px;
    page-break-after: avoid;
  }
  h3 {
    font-size: 12pt;
    color: var(--highlight);
    margin-top: 18px;
    margin-bottom: 8px;
    page-break-after: avoid;
  }

  p { margin-top: 0; margin-bottom: 12px; text-align: justify; }

  /* Table of Contents */
  .toc-container {
    background: var(--bg-alt);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 35px;
    page-break-after: always;
  }
  .toc-title {
    font-size: 18pt;
    font-weight: 700;
    color: var(--primary);
    margin-bottom: 15px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
  }
  .toc-list { list-style: none; padding: 0; margin: 0; }
  .toc-item {
    font-size: 11pt;
    padding: 6px 0;
    border-bottom: 1px dashed var(--border);
    display: flex;
    justify-content: space-between;
  }
  .toc-item a { text-decoration: none; color: var(--accent); font-weight: 600; }

  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 18px 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
  }
  th {
    background: var(--accent);
    color: #ffffff;
    text-align: left;
    padding: 10px 12px;
    font-weight: 600;
  }
  td {
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
  }
  tr:nth-child(even) { background-color: var(--bg-alt); }

  /* Callout boxes */
  .callout {
    border-left: 4px solid var(--highlight);
    background: var(--highlight-light);
    padding: 12px 16px;
    border-radius: 0 6px 6px 0;
    margin: 16px 0;
    font-size: 10pt;
  }
  .callout-title { font-weight: 700; color: var(--highlight); margin-bottom: 4px; }

  /* Code blocks */
  pre {
    background: var(--code-bg);
    color: var(--code-text);
    padding: 14px 18px;
    border-radius: 6px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 8.5pt;
    overflow-x: auto;
    page-break-inside: avoid;
    line-height: 1.45;
  }
  code {
    font-family: 'Consolas', 'Courier New', monospace;
    background: var(--bg-alt);
    color: var(--highlight);
    padding: 2px 5px;
    border-radius: 4px;
    font-size: 9pt;
  }
  pre code { background: transparent; color: inherit; padding: 0; }

  /* Badges */
  .badge {
    display: inline-block;
    padding: 2px 8px;
    font-size: 8.5pt;
    font-weight: 700;
    border-radius: 12px;
    color: #fff;
    background: var(--highlight);
  }
  .badge-post { background: #10B981; }
  .badge-get { background: #3B82F6; }
  .badge-patch { background: #F59E0B; }
  .badge-delete { background: #EF4444; }

  .page-break { page-break-after: always; }
</style>
</head>
<body>

<!-- COVER PAGE -->
<div class="cover-page">
  <div class="cover-brand">ForenSight AI</div>
  <div class="cover-title">Full Platform Technical Documentation & Specification</div>
  <div class="cover-subtitle">Enterprise Digital Forensics, Graph Intelligence, Vector Correlation & AI Copilot Platform</div>
  <div class="cover-meta">
    <strong>Author:</strong> ForenSight AI Engineering Team &nbsp;|&nbsp; 
    <strong>Version:</strong> 1.0.0 &nbsp;|&nbsp; 
    <strong>Classification:</strong> Enterprise Confidential
  </div>
</div>

<!-- TABLE OF CONTENTS -->
<div class="toc-container">
  <div class="toc-title">Table of Contents</div>
  <ul class="toc-list">
    <li class="toc-item"><a href="#sec1">1. Executive Overview & Core Capabilities</a></li>
    <li class="toc-item"><a href="#sec2">2. High-Level Architecture & Microservices Matrix</a></li>
    <li class="toc-item"><a href="#sec3">3. Evidence Ingestion & Forensic Parsing Pipeline</a></li>
    <li class="toc-item"><a href="#sec4">4. Machine Learning & Anomaly Detection Engine</a></li>
    <li class="toc-item"><a href="#sec5">5. Knowledge Graph & Cross-Case Vector Intelligence</a></li>
    <li class="toc-item"><a href="#sec6">6. AI Copilot & Natural Language Forensic Querying (RAG)</a></li>
    <li class="toc-item"><a href="#sec7">7. Frontend SPA Architecture & User Workflows</a></li>
    <li class="toc-item"><a href="#sec8">8. Database Schemas & Data Models</a></li>
    <li class="toc-item"><a href="#sec9">9. Complete REST API Reference</a></li>
    <li class="toc-item"><a href="#sec10">10. Security, RBAC & Multi-Tenant Isolation</a></li>
    <li class="toc-item"><a href="#sec11">11. Production Deployment & Operations Blueprint</a></li>
  </ul>
</div>

<!-- SECTION 1 -->
<h1 id="sec1">1. Executive Overview & Core Capabilities</h1>
<p><strong>ForenSight AI</strong> is an enterprise-grade digital forensics platform designed for security operations centers (SOC), incident response (IR) teams, and forensic investigators. It automates the parsing of heterogeneous forensic artifacts, correlates entities across incident timelines using graph databases, detects anomalies via machine learning, and provides an AI Copilot for interactive natural language investigation.</p>

<div class="callout">
  <div class="callout-title">Core Mission</div>
  Transform raw, unstructured, multi-source digital evidence into actionable forensic intelligence, reducing incident investigation timelines from days to minutes.
</div>

<h3>Key Capabilities Matrix</h3>
<table>
  <thead>
    <tr>
      <th>Capability</th>
      <th>Engine / Technology</th>
      <th>Operational Benefit</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Automated Artifact Parsing</strong></td>
      <td>python-evtx, scapy, sqlite3, pandas</td>
      <td>Parses Windows Event Logs, PCAPs, Browser History, CSV, JSON, and raw text logs out-of-the-box.</td>
    </tr>
    <tr>
      <td><strong>ML Anomaly Detection</strong></td>
      <td>PyOD (HBOS / Isolation Forest)</td>
      <td>Automatically flags suspicious logons, unexpected network connections, and privilege escalation attempts.</td>
    </tr>
    <tr>
      <td><strong>Knowledge Graph Correlation</strong></td>
      <td>Neo4j 5.12 + APOC Plugins</td>
      <td>Connects IPs, accounts, processes, and domains into an interactive visual entity relationship map.</td>
    </tr>
    <tr>
      <td><strong>Cross-Case Vector Search</strong></td>
      <td>Qdrant Vector DB + Sentence Transformers</td>
      <td>Identifies shared Indicators of Compromise (IoCs) and threat patterns across past and active cases.</td>
    </tr>
    <tr>
      <td><strong>AI Forensic Copilot</strong></td>
      <td>Google Gemini 1.5/2.0 + RAG Pipeline</td>
      <td>Answers complex investigative questions with inline evidence citations and automated summary drafting.</td>
    </tr>
  </tbody>
</table>

<div class="page-break"></div>

<!-- SECTION 2 -->
<h1 id="sec2">2. High-Level Architecture & Microservices Matrix</h1>
<p>ForenSight AI follows a modular microservice architecture orchestrated via Docker Containers. All components communicate securely over dedicated internal container networks.</p>

<pre>
                                +-----------------------------------+
                                |     React 18 SPA (Vite + Nginx)   |
                                +-----------------+-----------------+
                                                  | HTTP / REST
                                                  v
                                +-----------------+-----------------+
                                |  FastAPI ASGI Backend (Port 8000) |
                                +--+-------+-------+--------+----+--+
                                   |       |       |        |    |
           +-----------------------+       |       |        |    +-----------------------+
           |                               |       |        |                            |
           v                               v       v        v                            v
  +--------+--------+          +-----------+--+  +-+--------+--+  +--------------------+  +-------+-------+
  |  MongoDB 6.0    |          |  Neo4j 5.12  |  |  Qdrant DB  |  | Redis 7.0 + Celery |  |  MinIO S3     |
  |  (Evidence DB)  |          | (Graph Engine|  | (Vector Store|  | (Async Bus/Cache)  |  | (Object Store)|
  +-----------------+          +--------------+  +-------------+  +--------------------+  +---------------+
</pre>

<h3>Microservice Inventory</h3>
<table>
  <thead>
    <tr>
      <th>Service Name</th>
      <th>Port(s)</th>
      <th>Primary Role & Responsibility</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>web</code></td>
      <td><code>80 / 443</code></td>
      <td>Nginx web server hosting the compiled React SPA frontend. Handles TLS termination.</td>
    </tr>
    <tr>
      <td><code>api</code></td>
      <td><code>8000</code></td>
      <td>FastAPI backend handling REST API routes, authentication, RBAC, and orchestration.</td>
    </tr>
    <tr>
      <td><code>mongodb</code></td>
      <td><code>27017</code></td>
      <td>Primary document store for cases, user accounts, evidence metadata, and raw parsed events.</td>
    </tr>
    <tr>
      <td><code>neo4j</code></td>
      <td><code>7474, 7687</code></td>
      <td>Graph database storing entity-relationship topologies (IP $\rightarrow$ Account $\rightarrow$ Process).</td>
    </tr>
    <tr>
      <td><code>qdrant</code></td>
      <td><code>6333</code></td>
      <td>Vector store providing dense similarity indexing for RAG context retrieval & IoC matching.</td>
    </tr>
    <tr>
      <td><code>redis</code></td>
      <td><code>6379</code></td>
      <td>In-memory data structure store used for API caching, session tokens, and Celery task broker.</td>
    </tr>
    <tr>
      <td><code>minio</code></td>
      <td><code>9000, 9001</code></td>
      <td>S3-compatible object storage repository for uploaded binary evidence files (PCAP, EVTX, ZIP).</td>
    </tr>
  </tbody>
</table>

<!-- SECTION 3 -->
<h1 id="sec3">3. Evidence Ingestion & Forensic Parsing Pipeline</h1>
<p>Evidence files uploaded by investigators pass through an automated multi-stage processing pipeline:</p>

<ol>
  <li><strong>Upload & Storage:</strong> File is streamed to MinIO S3 object storage; SHA-256 hash is calculated to ensure evidentiary chain of custody.</li>
  <li><strong>Format Identification:</strong> MIME type and file extension routing select the appropriate parser module.</li>
  <li><strong>Extraction & Transformation:</strong> Specialized python parsers extract timestamps, source/destination IPs, usernames, command lines, and event IDs into a unified <code>ForensicEvent</code> structure.</li>
  <li><strong>Feature Vectorization & Anomaly Scoring:</strong> Text features are passed to PyOD ML models to assign an anomaly score between <code>0.0</code> (Normal) and <code>1.0</code> (Highly Suspicious).</li>
  <li><strong>Graph & Vector DB Sync:</strong> Entities (IPs, Users, Hosts) are ingested into Neo4j graph nodes, while text summaries are converted into dense vector embeddings in Qdrant.</li>
</ol>

<h3>Parser Modules Summary</h3>
<table>
  <thead>
    <tr>
      <th>Parser File</th>
      <th>Supported Extensions</th>
      <th>Extracted Fields & Key Indicators</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>evtx_parser.py</code></td>
      <td><code>.evtx</code></td>
      <td>Event ID (4624 logon, 4625 failed logon, 7045 service creation, 1102 log cleared), TargetUser, Workstation, IP Address.</td>
    </tr>
    <tr>
      <td><code>pcap_parser.py</code></td>
      <td><code>.pcap, .pcapng</code></td>
      <td>Source/Dest IP, Source/Dest Port, Protocol (TCP/UDP/DNS/HTTP), Packet length, DNS queries, Payload strings.</td>
    </tr>
    <tr>
      <td><code>browser_parser.py</code></td>
      <td><code>.sqlite, .db</code></td>
      <td>Chrome/Firefox/Edge History: URL, Visit Time, Page Title, Visit Count, Search Queries.</td>
    </tr>
    <tr>
      <td><code>csv_parser.py</code> / <code>json_parser.py</code></td>
      <td><code>.csv, .json, .jsonl</code></td>
      <td>Structured logs: Automated column mapping, Timestamp normalization, Custom field extraction.</td>
    </tr>
    <tr>
      <td><code>text_parser.py</code></td>
      <td><code>.txt, .log</code></td>
      <td>Syslog & Auth logs: Regex extraction for IPv4/IPv6, Email addresses, File paths, MD5/SHA256 hashes.</td>
    </tr>
  </tbody>
</table>

<div class="page-break"></div>

<!-- SECTION 4 -->
<h1 id="sec4">4. Machine Learning & Anomaly Detection Engine</h1>
<p>ForenSight AI incorporates unsupervised machine learning via PyOD to detect anomalous activities without requiring pre-labeled training datasets.</p>

<h3>Algorithm: Histogram-based Outlier Score (HBOS)</h3>
<p>HBOS constructs univariate histograms for each feature and calculates an anomaly score based on bin densities. It operates in $O(N)$ time complexity, making it ideal for real-time processing of high-volume log streams.</p>

<pre>
# Anomaly Scoring Execution Flow (app/services/intelligence/anomaly.py)
from pyod.models.hbos import HBOS
import numpy as np

def evaluate_events(feature_matrix):
    model = HBOS(n_bins=10, contamination=0.05)
    model.fit(feature_matrix)
    scores = model.decision_scores_  # Raw anomaly scores
    return scores
</pre>

<h3>Threat Detection Rules</h3>
<ul>
  <li><strong>Brute Force Attempt:</strong> High frequency of Windows Event ID <code>4625</code> (Failed Logon) within a 5-minute rolling window.</li>
  <li><strong>Privilege Escalation:</strong> Windows Event ID <code>4672</code> (Special Privileges Assigned) immediately following a logon event from an external IP.</li>
  <li><strong>Log Tampering:</strong> Windows Event ID <code>1102</code> (Audit Log Cleared) or abrupt timestamp gaps in syslog streams.</li>
  <li><strong>DNS Tunneling / Exfiltration:</strong> Excessive volume of high-entropy TXT domain queries captured in PCAP streams.</li>
</ul>

<!-- SECTION 5 -->
<h1 id="sec5">5. Knowledge Graph & Cross-Case Vector Intelligence</h1>

<h3>Neo4j Entity-Relationship Topology</h3>
<p>Entities extracted from evidence files are converted into Neo4j graph nodes and relationships using Cypher queries.</p>

<pre>
(User:UserAccount {username: "administrator"})
    -[:LOGGED_INTO {timestamp: "2026-08-04T01:00:00Z"}]-> (Host:Workstation {hostname: "DC-01"})
    -[:GENERATED_EVENT]-> (Event:ForensicEvent {event_id: 4672, severity: "CRITICAL"})
    -[:COMMUNICATED_WITH]-> (IP:IPAddress {address: "192.168.1.105"})
</pre>

<h3>Qdrant Vector Embedding & Cross-Case Intelligence</h3>
<p>Events are embedded into a 384-dimensional vector space using <code>sentence-transformers/all-MiniLM-L6-v2</code>. When a new case is analyzed, Qdrant runs a cosine similarity search across all historical cases to find matching Indicators of Compromise (IoCs) or identical attack vectors.</p>

<div class="page-break"></div>

<!-- SECTION 6 -->
<h1 id="sec6">6. AI Copilot & Natural Language Forensic Querying (RAG)</h1>
<p>The <strong>ForenSight AI Copilot</strong> uses a Retrieval-Augmented Generation (RAG) pipeline powered by the Google Gemini API SDK (<code>google-generativeai</code>).</p>

<pre>
+---------------------+     +--------------------------+     +------------------------+
| User Query          | --> | Retrieval Engine         | --> | Gemini Prompt Context  |
| "Show suspicious    |     | Fetch top-5 Qdrant vectors|     | System safety rule +   |
| logons for admin"   |     | & Neo4j graph sub-tree   |     | Evidence JSON context  |
+---------------------+     +--------------------------+     +-----------+------------+
                                                                         |
                                                                         v
                                                             +------------------------+
                                                             | Gemini Response        |
                                                             | Structured answer with |
                                                             | evidence citations     |
                                                             +------------------------+
</pre>

<!-- SECTION 7 -->
<h1 id="sec7">7. Frontend SPA Architecture & User Workflows</h1>
<p>The frontend is built with **React 18**, **Vite**, **Tailwind CSS**, and **Lucide React** icons, featuring a sleek slate/navy dark mode theme designed for high-density information display.</p>

<h3>Page Hierarchy</h3>
<ul>
  <li><code>LoginPage.jsx</code> / <code>RegisterPage.jsx</code>: Multi-tenant user login and onboarding.</li>
  <li><code>DashboardPage.jsx</code>: High-level metrics, active investigations summary, global threat feed, and storage monitor.</li>
  <li><code>CaseDetailPage.jsx</code>: Interactive workspace containing 7 specialized investigation tabs:
    <ul>
      <li><strong>Overview Tab:</strong> Case metadata, assigned investigators, severity rating.</li>
      <li><strong>Evidence Tab:</strong> Drag-and-drop file uploader, file status list, SHA-256 verifier.</li>
      <li><strong>Timeline Tab:</strong> Interactive event timeline filterable by timestamp, severity, and event type.</li>
      <li><strong>Graph View Tab:</strong> Interactive canvas rendering the Neo4j entity relationship graph.</li>
      <li><strong>Cross-Case Intelligence Tab:</strong> Vector similarity search displaying matching historical cases.</li>
      <li><strong>AI Copilot Tab:</strong> Natural language chat interface with context memory and evidence attachment.</li>
      <li><strong>Reports Tab:</strong> One-click automated forensic report generator.</li>
    </ul>
  </li>
  <li><code>UsersPage.jsx</code> & <code>OrganizationSetupPage.jsx</code>: Admin panel for user management and RBAC.</li>
</ul>

<div class="page-break"></div>

<!-- SECTION 8 -->
<h1 id="sec8">8. Database Schemas & Data Models</h1>

<h3>MongoDB Collection Schemas</h3>

<h4>Collection: <code>users</code></h4>
<pre>
{
  "_id": ObjectId("..."),
  "username": "investigator_alice",
  "email": "alice@forensight.io",
  "hashed_password": "$2b$12$e8Zb...",
  "role": "Investigator",  // Admin, Investigator, Analyst, Viewer
  "organization_id": "org_cyber_sec_01",
  "created_at": ISODate("2026-08-04T01:00:00Z")
}
</pre>

<h4>Collection: <code>cases</code></h4>
<pre>
{
  "_id": ObjectId("..."),
  "case_number": "CASE-2026-0804",
  "title": "Ransomware Intrusion - Finance Workstation",
  "status": "Active", // Active, Archived, Closed
  "severity": "HIGH", // LOW, MEDIUM, HIGH, CRITICAL
  "organization_id": "org_cyber_sec_01",
  "created_by": "investigator_alice",
  "created_at": ISODate("2026-08-04T01:05:00Z")
}
</pre>

<h4>Collection: <code>evidence</code></h4>
<pre>
{
  "_id": ObjectId("..."),
  "case_id": "CASE-2026-0804",
  "filename": "Security_Logs_DC01.evtx",
  "file_size_bytes": 15420800,
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "minio_object_path": "evidence/CASE-2026-0804/Security_Logs_DC01.evtx",
  "parser_type": "evtx",
  "status": "PARSED", // UPLOADED, PROCESSING, PARSED, ERROR
  "parsed_events_count": 4120
}
</pre>

<!-- SECTION 9 -->
<h1 id="sec9">9. Complete REST API Reference</h1>

<table>
  <thead>
    <tr>
      <th>HTTP Method</th>
      <th>Endpoint Route</th>
      <th>Auth Required</th>
      <th>Description & Usage</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><span class="badge badge-post">POST</span></td>
      <td><code>/api/auth/token</code></td>
      <td>No</td>
      <td>Authenticates user and returns OAuth2 JWT access token.</td>
    </tr>
    <tr>
      <td><span class="badge badge-post">POST</span></td>
      <td><code>/api/auth/register</code></td>
      <td>No</td>
      <td>Registers a new user profile within an organization.</td>
    </tr>
    <tr>
      <td><span class="badge badge-get">GET</span></td>
      <td><code>/api/cases/</code></td>
      <td>Yes</td>
      <td>Retrieves list of cases for the authenticated user's organization.</td>
    </tr>
    <tr>
      <td><span class="badge badge-post">POST</span></td>
      <td><code>/api/cases/</code></td>
      <td>Yes</td>
      <td>Creates a new forensic investigation case.</td>
    </tr>
    <tr>
      <td><span class="badge badge-post">POST</span></td>
      <td><code>/api/evidence/upload/{case_id}</code></td>
      <td>Yes</td>
      <td>Streams evidence file upload to MinIO and triggers async parsing.</td>
    </tr>
    <tr>
      <td><span class="badge badge-get">GET</span></td>
      <td><code>/api/events/{case_id}</code></td>
      <td>Yes</td>
      <td>Fetches parsed forensic events with optional filters (severity, date).</td>
    </tr>
    <tr>
      <td><span class="badge badge-post">POST</span></td>
      <td><code>/api/chat/message</code></td>
      <td>Yes</td>
      <td>Sends investigative query to AI Copilot RAG pipeline.</td>
    </tr>
    <tr>
      <td><span class="badge badge-get">GET</span></td>
      <td><code>/api/graph/{case_id}</code></td>
      <td>Yes</td>
      <td>Queries Neo4j and returns graph node/edge JSON for UI visualization.</td>
    </tr>
    <tr>
      <td><span class="badge badge-get">GET</span></td>
      <td><code>/api/similarity/{evidence_id}</code></td>
      <td>Yes</td>
      <td>Queries Qdrant for top cross-case matching evidence vectors.</td>
    </tr>
    <tr>
      <td><span class="badge badge-post">POST</span></td>
      <td><code>/api/reports/generate/{case_id}</code></td>
      <td>Yes</td>
      <td>Generates comprehensive PDF / HTML investigation report.</td>
    </tr>
  </tbody>
</table>

<div class="page-break"></div>

<!-- SECTION 10 -->
<h1 id="sec10">10. Security, RBAC & Multi-Tenant Isolation</h1>
<p>ForenSight AI enforces defense-in-depth security principles across all system layers:</p>

<ul>
  <li><strong>Authentication & Passwords:</strong> Passwords are hashed using <code>bcrypt</code> with a cost factor of 12. Authentication uses OAuth2 Bearer Tokens (JWT with HS256 algorithm).</li>
  <li><strong>Role-Based Access Control (RBAC):</strong>
    <ul>
      <li><code>Admin</code>: Complete system configuration, user role management, audit log access.</li>
      <li><code>Investigator</code>: Case creation, evidence upload, AI Copilot querying, report generation.</li>
      <li><code>Analyst</code>: Evidence viewing, timeline filtering, event annotation.</li>
      <li><code>Viewer</code>: Read-only access to published reports and executive dashboards.</li>
    </ul>
  </li>
  <li><strong>Multi-Tenant Data Isolation:</strong> Every MongoDB query and Neo4j Cypher lookup includes an explicit <code>organization_id</code> filter, preventing cross-tenant data leaks.</li>
</ul>

<!-- SECTION 11 -->
<h1 id="sec11">11. Production Deployment & Operations Blueprint</h1>

<h3>Docker Compose Orchestration</h3>
<pre>
# Execute from project root (d:/ForenSight/ForenSight)
# 1. Copy environment template
cp backend/.env.example backend/.env

# 2. Build and launch all 7 services in background
docker compose up -d --build

# 3. Verify healthy container status
docker compose ps
</pre>

<h3>System Verification Matrix</h3>
<table>
  <thead>
    <tr>
      <th>Service Component</th>
      <th>Access URL / Endpoint</th>
      <th>Health Check Criteria</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Web Interface</strong></td>
      <td><code>http://localhost:80</code></td>
      <td>React SPA loads clean login screen.</td>
    </tr>
    <tr>
      <td><strong>FastAPI Docs</strong></td>
      <td><code>http://localhost:8000/docs</code></td>
      <td>Interactive Swagger UI loads all routes.</td>
    </tr>
    <tr>
      <td><strong>MinIO Console</strong></td>
      <td><code>http://localhost:9001</code></td>
      <td>Admin console accessible with <code>MINIO_ROOT_USER</code> credentials.</td>
    </tr>
    <tr>
      <td><strong>Neo4j Browser</strong></td>
      <td><code>http://localhost:7474</code></td>
      <td>Cypher query terminal connects to <code>bolt://localhost:7687</code>.</td>
    </tr>
  </tbody>
</table>

<br/><hr/><br/>
<p style="text-align: center; color: var(--text-muted); font-size: 9pt;">
  &copy; 2026 ForenSight AI. All rights reserved. End of Document.
</p>

</body>
</html>
"""

def generate_pdf():
    os.makedirs(os.path.dirname(HTML_DOC_PATH), exist_ok=True)
    with open(HTML_DOC_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML Documentation written to: {HTML_DOC_PATH}")

    # Check for Edge headless on Windows
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    
    edge_bin = None
    for path in edge_paths:
        if os.path.exists(path):
            edge_bin = path
            break

    if edge_bin:
        print(f"Found Microsoft Edge at: {edge_bin}")
        cmd = [
            edge_bin,
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={PDF_DOC_PATH}",
            HTML_DOC_PATH
        ]
        print(f"Executing PDF conversion command: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.exists(PDF_DOC_PATH) and os.path.getsize(PDF_DOC_PATH) > 0:
            print(f"SUCCESS: PDF generated at: {PDF_DOC_PATH} (Size: {os.path.getsize(PDF_DOC_PATH)} bytes)")
            return True
        else:
            print(f"Edge PDF generation warning/error: {res.stderr}")

    # Fallback to WeasyPrint if available
    try:
        from weasyprint import HTML
        print("Rendering PDF using WeasyPrint...")
        HTML(HTML_DOC_PATH).write_pdf(PDF_DOC_PATH)
        if os.path.exists(PDF_DOC_PATH) and os.path.getsize(PDF_DOC_PATH) > 0:
            print(f"SUCCESS: PDF generated via WeasyPrint at: {PDF_DOC_PATH}")
            return True
    except ImportError:
        print("WeasyPrint not installed in current environment.")
    except Exception as e:
        print(f"WeasyPrint error: {e}")

    print("HTML documentation file generated successfully. Open the HTML file in any browser to Save as PDF.")
    return False

if __name__ == "__main__":
    generate_pdf()
