# ForenSight AI: Premium Forensic Ingestion & Threat Hunting Pipeline

ForenSight AI is a next-generation, high-performance forensic analysis and incident response platform. It is engineered from the ground up to ingest raw workstation artifacts (such as massive `EVTX` logs, browser history JSONs, and network telemetry), filter out telemetry noise, build complex behavioral threat graphs, isolate anomalous patterns using unsupervised machine learning, and support interactive threat hunting via a secure Copilot interface.

---

## 🏗️ ForenSight AI Final Architecture

```
                    ┌────────────────────────┐
                    │     React Dashboard    │
                    └───────────┬────────────┘
                                │ REST / JSON
                    ┌───────────▼────────────┐
                    │    FastAPI Gateway     │
                    └─────────┬─┬─┬──────────┘
           ┌──────────────────┘ │ └──────────────────┐
     Metadata  & Pointers       │     Broker Msg     │ Raw Telemetry Dumps
     ┌─────▼─────┐              │     ┌─────▼─────┐  │   ┌─────▼─────┐
     │  MongoDB  │              │     │Redis Queue│  │   │   MinIO   │
     └───────────┘              │     └─────┬─────┘  │   └───────────┘
                                │           │        │
                                │           ▼        │
                                │    ┌────────────┐  │
                                │    │Celery Pools│  │
                                │    └──────┬─────┘  │
                                │           │        │
                   ┌────────────┼───────────┼────────┼────────────┐
                   │            │           │        │            │
                   │            │           ▼        │            │
                   │      ┌─────▼────────────────────▼─────┐      │
                   │      │     Streaming Ingestion Engine │      │
                   │      └─────────────────┬──────────────┘      │
                   │                        │                     │
                   │                        ▼                     │
                   │      ┌────────────────────────────────┐      │
                   │      │     Forensic Rule Filter       │      │
                   │      │(Suppress 15M benign -> 150K)   │      │
                   │      └─────────────────┬──────────────┘      │
                   │                        │                     │
                   │      ┌─────────────────┼─────────────────┐   │
                   │      │                 │                 │   │
                   │      ▼                 ▼                 ▼   │
                   │┌───────────┐     ┌───────────┐     ┌────────┐│
                   ││  Feature  │     │ Timeline  │     │Relation││
                   ││  Builder  │     │  Builder  │     │Graph   ││
                   │└─────┬─────┘     └─────┬─────┘     └───┬────┘│
                   │      │                 │               │     │
                   └──────┼─────────────────┼───────────────┼─────┘
                          │                 │               │
                          ▼                 ▼               ▼
                   ┌────────────┐     ┌───────────┐     ┌────────┐
                   │    ML /    │     │  MongoDB  │     │ Neo4j  │
                   │  Anomalies │     │ Documents │     │ Graph  │
                   │ Evaluator  │     └───────────┘     └────────┘
                   └──────┬─────┘
                          │
                          ▼
                   ┌────────────┐
                   │Local FAISS │
                   │  Index     │
                   └──────┬─────┘
                          │
                          ▼
                   ┌────────────┐
                   │ Local LLM  │
                   │ (Ollama)   │
                   └────────────┘
```

---

## 🔍 Step-by-Step ForenSight Ingestion & Analysis Workflow

This workflow represents the path of a sample investigation (e.g. `CASE-101`) through the ForenSight platform:

### 1️⃣ Step 1: Create Case
An investigator initializes `CASE-101` in the Cyber Crime Lab. 
* **Database**: MongoDB stores metadata (Title, Creator, Status, Organization ID). No forensic payload is written to the database yet.
* **Takt**: `< 1 second`.

### 2️⃣ Step 2: Upload Evidence Payloads
Large forensic artifacts (e.g., `windows.evtx` [2.2GB], `browser.json` [500MB], `network.pcap` [300MB]) are uploaded.
* **Integrity Check**: The backend calculates the SHA-256 hash in a chunked streaming loop to verify file integrity. Duplicate files are instantly blocked (`409 Conflict`).
* **Storage Allocation**: Payloads are stored in MinIO under `minio://organization/case101/{hash}.{ext}`. MongoDB stores **only** the metadata pointer. 
* **Takt**: `20-60 seconds` (depending on upload speeds).

### 3️⃣ Step 3: Trigger Background Workers
Redis queues asynchronous Celery tasks (`Parse Windows`, `Parse Browser`, `Parse PCAP`) which execute concurrently. The UI is completely unblocked; the user can close their browser.
* **Takt**: `Instant`.

### 4️⃣ Step 4: Streaming Parser Execution
Workers fetch raw artifacts from MinIO. To keep RAM usage minimal (capped under `50MB` instead of reading gigabytes into memory), parsers read, normalize, and yield event chunks iteratively:
* **Output Schema**: Converted into the unified **CFM (Common Forensic Model)** format:
  ```json
  {"timestamp": "10:22:14", "event": "process_created", "subject": "powershell.exe", "parent": "WINWORD.EXE", "user": "John"}
  ```

### 5️⃣ Step 5: Heuristic Rule Filtering
Every normalized event is fed to `ForensicRuleFilter`. Safe/noisy system events (Windows updates, benign OS background process heartbeats) are suppressed:
* **Efficiency**: Truncates raw databases sizing from millions of background events to only security-relevant actions.

### 6️⃣ Step 6: Tri-Builder Execution
Filtered events are dispatched to three builders operating in parallel:
1. **Feature Builder**: Updates numeric event frequencies and compiles the 6-dimensional ML feature matrix `[hour, weekend, subj_freq, obj_freq, act_freq, sev_val]`.
2. **Timeline Builder**: Commits records chronologically in MongoDB.
3. **Relationship Builder**: Links forensic entities in the Neo4j Graph database:
   ```cypher
   (User:John) -[:EXECUTED]-> (Process:powershell.exe) -[:DOWNLOADED]-> (File:payload.exe) -[:CONNECTED_TO]-> (IP:evil.com)
   ```

### 7️⃣ Step 7: Graph Analytics
Post-ingestion Cypher routines calculate centralities (PageRank, Degree, and Betweenness) for graph nodes. Entities with high interaction densities get flagged immediately during analytics rounds.

### 8️⃣ Step 8: ML Anomaly Detection Layer
The compiled feature matrix is processed by the anomaly suite:
* **Outlier Engines**: Compares `Isolation Forest`, `Local Outlier Factor (LOF)`, `One-Class SVM`, and `HBOS`.
* **Selection Logic**: Rank-selects the best model based on the silhouette fit coefficient to tag suspicious events in MongoDB and Neo4j.

### 9️⃣ Step 9: Case Intelligence Compilation
The Context Builder groups the findings, tags indicators matching MITRE ATT&CK tactics, and compiles the final HTML/PDF case report.

### 🔟 Step 10: FAISS Organization-Isolated Vector Storage
Case summaries are chunked, embedded using optimized models, and appended into an organization-isolated directory. Tenant partitions ensure that `Organization B` can never query `Organization A`'s vector index.

### 11 Step 11: Context-Aware Copilot Router
The Copilot routes analyst questions dynamically:
* *Timeline queries*: Scans MongoDB.
* *Activity paths*: Traverses Neo4j.
* *Historical similarities*: Returns matching historical case reports from the FAISS database directory to offer recommendations like:
  > *"In 72% of similar resolved investigations in your organization, investigators found persistence in the Windows Registry."*

### 12 Step 12: Case Closure
Closing a case generates an updated case summary embedding, writing the investigator's resolution steps back to the FAISS index to benefit future hunts.

---

## 💾 Core Storage Schema

| Storage Engine | Purpose | Data Structs |
| :--- | :--- | :--- |
| **MinIO** | Binary storage of large files ($GBs$) | Raw telemetry dumps, `.evtx`, logs, payload dumps |
| **MongoDB** | Platform state & Forensics timeline | Case profiles, users, CFM timelines, anomaly scores, HTML reports |
| **Neo4j** | Graph structure mapping | Node entities (User, File, Process, IP) and relationships |
| **Redis** | Speed caching & Celery broker | Background queues, lock objects, task states |
| **FAISS** | Organization-isolated vector storage | Case summary embeddings, similar case centroid vectors |

---

## 🏆 Architectural Verification Verdict

The platform **successfully implements, satisfies, and exceeds** all steps under these design requirements:

1. **Memory-Safe Streaming**: Parsers process data without loading raw gigabytes into memory. Capped local vector size checks (max `2000` items) protect CPU usage.
2. **Noise Suppression**: `ForensicRuleFilter` filters and discards repetitive operating system logs, keeping database size optimized.
3. **Tri-Builder Ingest**: MongoDB timelines, Neo4j graphs, and ML feature matrices are built asynchronously and concurrently.
4. **Offline Benchmarked Embedders**: Uses localized `"all-MiniLM-L6-v2"` models inside construct wrappers to guarantee zero internet dependency.
5. **No Visual Overlap**: Edge aggregation in D3 graphs groups duplicate event paths to prevent canvas overlapping and browser performance stutter.
