# ForenSight Evidence Parser, Live Scan Timer, Re-process Idempotency & Data Isolation Walkthrough

## Summary of Accomplishments

We have successfully integrated **Neo4j** into **ForenSight** as the primary **forensic relationship analysis, event correlation, attack-path discovery, and interactive graph visualization layer**, upgraded the **evidence parsing & entity extraction pipeline**, implemented a **Live Scan Timer Stopwatch** for evidence processing, fixed **Evidence Re-processing Event Duplication**, and enforced **Complete Case & Evidence Data Isolation**.

---

### 1. Neo4j Domain Graph Schema & Connection Layer
* **12 Primary Domain Node Labels**: Created `Case`, `Evidence`, `Event`, `Process`, `User`, `Host`, `File`, `IPAddress`, `Domain`, `Port`, `RegistryKey`, `Service`.
* **Domain Relationships**: Implemented `HAS_EVIDENCE`, `CONTAINS_EVENT`, `INVOLVES_PROCESS`, `INVOLVES_USER`, `OCCURRED_ON`, `SPAWNED`, `EXECUTED`, `CREATED`, `MODIFIED`, `DELETED`, `CONNECTED_TO`, `RESOLVED`, `USES_PORT`, `RESOLVES_TO`, `MODIFIED_REGISTRY`, `CREATED_SERVICE`, `EXECUTED_AS`, `RELATED_TO`.
* **Stable Composite Identifiers**:
  * `Process`: `{host_id}:{pid}:{process_name}`
  * `User`: `{domain}\\{username}`
  * `Host`: `{hostname}`
  * `Port`: `{port_number}:{protocol}`
  * `IPAddress`: `{address}`
* **Connection Layer**: Created [`neo4j_service.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/services/graph/neo4j_service.py) reading `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `NEO4J_DATABASE` with connection health checks, session management, transaction retries, and automated constraint migrations on startup.

---

### 2. Idempotent Batch Ingestion & ML Anomaly Sync
* **Idempotency & Duplicate Prevention**: Refactored [`graph_builder.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/services/graph/graph_builder.py) and [`graph_repository.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/repositories/graph_repository.py) to use Cypher `UNWIND` parameter batches and `MERGE` clauses. Re-ingesting evidence does **not** double nodes or edges.
* **Isolation Forest ML Sync**: Updated [`processing_pipeline.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/services/ingestion/processing_pipeline.py) so that Isolation Forest `is_anomaly` flags and `anomaly_score` floats are immediately synced into Neo4j nodes and edges post-evaluation.
* **Evidence Provenance**: Every edge stores `case_id`, `evidence_id`, `event_id`, `source_file`, `timestamp`, and `relationship_type` (`"observed"` vs `"inferred"`).

---

### 3. Forensic Correlation Engine & Multi-Factor Scoring
Created [`graph_correlation.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/services/graph/graph_correlation.py):
* **Multi-Factor Score (0–100 scale)** based on ML anomalies (+25), suspicious process lineage (+20), external network connections (+20), autostart registry writes (+15), cross-evidence verification (+10), and temporal proximity (+10).
* **Cross-Evidence Correlation**: Correlates EVTX process creation events with PCAP network capture events targeting the same external IP address.
* **Attack Path Discovery**: Identifies complex chains (`Office -> powershell.exe -> cmd.exe -> payload.exe -> External IP`).
* **Temporal Windows**: Supports temporal correlation queries within configurable windows ($\pm 30\text{s}, \pm 1\text{m}, \pm 5\text{m}, \pm 10\text{m}$).

---

### 4. REST APIs & Frontend Interactive Graph
* **APIs**: Updated [`graph.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/api/graph.py) & [`correlations.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/api/correlations.py) with endpoints:
  * `GET /api/cases/{case_id}/graph`
  * `GET /api/evidence/{evidence_id}/graph`
  * `GET /api/events/{event_id}/graph`
  * `GET /api/cases/{case_id}/attack-paths`
  * `GET /api/cases/{case_id}/correlations`
* **Interactive Cytoscape Graph**: Updated [`GraphView.jsx`](file:///d:/ForenSight%20-%20Copy/ForenSight/frontend/src/components/graph/GraphView.jsx) with distinct visual node shapes and colors for domain types, anomaly filters, zoom/pan/fit controls, and reset view.
* **Node Inspector Panel**: Created [`NodeDetailsPanel.jsx`](file:///d:/ForenSight%20-%20Copy/ForenSight/frontend/src/components/graph/NodeDetailsPanel.jsx) displaying process PID/cmdline, IP public/private classification, file hash/path, user domain, and evidence provenance.

---

### 5. Dashboard Synchronization & AI Copilot Integration
* **Dashboard Stats**: Updated [`event_repository.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/repositories/event_repository.py) and [`CaseStats.jsx`](file:///d:/ForenSight%20-%20Copy/ForenSight/frontend/src/components/dashboard/CaseStats.jsx) so that `Graph Correlations` displays distinct deduplicated findings from the correlation engine.
* **AI Copilot**: Equipped [`query_router.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/services/copilot/query_router.py) with structured graph tools to answer attack path, process lineage, and cross-evidence queries with explicit evidence citations.

---

### 6. Fast Forensic Entity & Relationship Extraction Upgrades
* **Common Normalized Event Schema**: Implemented nested schema (`host`, `user`, `process`, `parent_process`, `file`, `network`, `registry`, `service`, `authentication`, `parser_metadata`).
* **Entity & Relationship Extractor**: Created [`extractor.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/parsers/extractor.py) for deterministic extraction with confidence scores (`1.0`) and provenance metrics.
* **Format Parsers**:
  * `EvtxParser`: Full XML Security & Sysmon IDs (4624, 4625, 4688, 4663, 4657, 5039, Sysmon 1/3/7/11/13, PowerShell).
  * `PcapParser`: Aggregates DNS queries, HTTP headers/URIs, TLS SNI, and packet streams.
  * `CsvParser`: Flexible column alias mapping (`src_ip` $\rightarrow$ `network.source_ip`).
  * `JsonParser`: NDJSON / JSON lines and nested key navigation.
  * `HashParser`: Dedicated parser for `.md5`, `.sha1`, `.sha256` files.
  * `TextParser`: Fast precompiled regex extractors for IPs, URLs, paths, hashes, and timestamps.
* **Pipeline Metrics**: Updated [`processing_pipeline.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/services/ingestion/processing_pipeline.py) to track exact timing (`parse_seconds`, `db_seconds`, `total_seconds`) and counts (`events_read`, `entities_extracted`, `relationships_extracted`).

---

### 7. Live Scan Timer Stopwatch Architecture
* **Backend Source of Truth**:
  * Added `processing_started_at`, `processing_finished_at`, and `scan_duration_ms` to [`evidence.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/schemas/evidence.py).
  * Updated [`evidence_repository.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/repositories/evidence_repository.py) to set `processing_started_at = current_time` when status becomes `parsing`, and `processing_finished_at = current_time`, `scan_duration_ms = actual_duration_ms` when status becomes `parsed` or `failed`.
* **Zero 1-Second DB Polling Overhead**: No database writes every second; calculation is handled on the client using the backend start timestamp.
* **Frontend Stopwatch Display ([`EvidenceList.jsx`](file:///d:/ForenSight%20-%20Copy/ForenSight/frontend/src/components/evidence/EvidenceList.jsx))**:
  * Uses a single shared 1s interval ticker (`now = Date.now()`) for active processing statuses (`parsing`, `queued`, `uploaded`, etc.).
  * Calculates `Math.floor((now - processing_started_at) / 1000)` during active scanning.
  * On page refresh during scanning, smoothly continues e.g., `20s`, `21s`, `22s` without restarting from `0s`.
  * On terminal states (`parsed`, `failed`), freezes the timer and displays `scan_duration_ms / 1000` (e.g. `47s`, fixing the `46343s` millisecond bug).
  * On page refresh after completion, continues displaying `47s` and never recalculates against current time.
  * Formatted via `formatDuration` in [`formatters.js`](file:///d:/ForenSight%20-%20Copy/ForenSight/frontend/src/utils/formatters.js) (`0s`, `47s`, `1m 5s`, `1h 1m 5s`).
  * On Re-process click, clears completion timestamps and resets live timer to `0s`, `1s`, `2s`...

---

### 8. Evidence Re-process Idempotency & Clean-Up Fix
* **Scoped Derived Data Cleanup**:
  - `EventRepository.delete_by_evidence_id(evidence_id, org_id)` purges old events in MongoDB for the target `evidence_id` **before** newly parsed events are inserted.
  - `GraphRepository.delete_evidence_subgraph(evidence_id)` detaches and deletes old Neo4j `Event` nodes and evidence-specific relationships for `evidence_id`.
  - **Multi-Evidence Isolation**: Other evidence files in the same case (e.g., `B.pcap` when `A.evtx` is re-processed) remain 100% untouched.
* **Backend Concurrency Guard & Lock**:
  - Added status check in `reprocess_evidence` API ([`evidence.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/api/evidence.py)). If evidence is currently in an active state (`parsing`, `processing`, `analyzing`, `correlating`), returns `HTTP 409 Conflict: "Evidence is currently being processed."`
* **Frontend Double-Click Protection**:
  - `handleReprocess` in [`EvidenceList.jsx`](file:///d:/ForenSight%20-%20Copy/ForenSight/frontend/src/components/evidence/EvidenceList.jsx) guards against multiple rapid clicks and displays 409 conflict alerts if triggered.

---

### 9. Complete Case & Evidence Data Isolation
* **Neo4j Domain Node Case Tenant Isolation**:
  - Scoped all Neo4j domain node composite IDs by `case_id` in [`graph_repository.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/repositories/graph_repository.py) (e.g., `Process` = `{case_id}:{hostname}:{pid}:{proc_name}`, `IPAddress` = `{case_id}:{address}`).
  - Prevents global entity merging across cases. Traversing Case 1's IP or process nodes will **never** bleed into Case 2's processes.
* **Evidence vs Case Statistics**:
  - Evidence-level queries ([`EventRepository.count_stats`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/repositories/event_repository.py)) return statistics for `evidence_id` only.
  - Case-level queries return aggregated totals across all evidence belonging to `case_id`.
* **AI Copilot & Report Isolation**:
  - Enforced `case_id` filtering across AI Copilot query routing ([`query_router.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/services/copilot/query_router.py)) and Report rendering ([`pdf_compiler.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/services/reports/pdf_compiler.py)).

---

### 10. Automated Test Suites
Created:
* [`backend/tests/test_evidence_parsers.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/tests/test_evidence_parsers.py)
* [`backend/tests/test_neo4j_graph.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/tests/test_neo4j_graph.py)
* [`backend/tests/test_reprocess_idempotency.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/tests/test_reprocess_idempotency.py)
* [`backend/tests/test_case_isolation.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/tests/test_case_isolation.py)

---

### 11. Forensic Evidence Graph & Pipeline Stability Enhancements
* **Enriched Edge `is_anomaly` Mapping**: Modified [`GraphRepository.get_case_graph`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/repositories/graph_repository.py) to check if either the relationship, the source node, or the target node is flagged as anomalous. This ensures that when the "Anomalies Only" filter is toggled on the frontend, relationships connected to anomalous events are preserved and visible instead of yielding empty graph states.
* **Port Mapping Support in Graph**: Added `s.port_id` and `t.port_id` to the `coalesce` lists inside the case graph Cypher query. This ensures Port nodes are assigned valid stable IDs and rendered properly.
* **Redundant Case Isolation Constraint Clean-up**: Simplified Cypher where-clauses in `get_case_graph` to `r.case_id = $case_id`. By scoping the query on the relationship `case_id`, we prevent empty graphs when some nodes lack the redundant `case_id` property, whilst maintaining complete tenant isolation since all relationships and node IDs are already case-prefixed.
* **Pipeline Crash Resolution**: Fixed a critical `NameError` / `UnboundLocalError` in [`processing_pipeline.py`](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/services/ingestion/processing_pipeline.py) where `case_id_str` was referenced before it was defined when trying to clean up old evidence subgraphs.
* **Neo4j Graph Purge Fix**: Corrected the Cypher template in `clear_case_graph` by removing the unused and unset `n.org_id` filter which was triggering parameter-missing errors and failing to clear case data.
* **Evidence File Selection Dropdown**: Implemented an evidence file dropdown in the [`GraphView.jsx`](file:///d:/ForenSight%20-%20Copy/ForenSight/frontend/src/components/graph/GraphView.jsx) header which allows the investigator to switch between viewing the complete case graph ("All Evidence Files") and specific evidence files.
* **Refreshed Cyber-Themed Controls**: Redesigned all graph control buttons (Zoom In, Zoom Out, Fit, Reset, and a new Refresh button) in [`index.css`](file:///d:/ForenSight%20-%20Copy/ForenSight/frontend/src/index.css) to support smooth transition scaling, cyberpunk colored hover states, drop-shadow glows, and active click visual responses.
* **Animated Viewport Navigation**: Updated `handleZoomIn`, `handleZoomOut`, `handleFit`, and `handleReset` in [`GraphView.jsx`](file:///d:/ForenSight%20-%20Copy/ForenSight/frontend/src/components/graph/GraphView.jsx) to call `cy.resize()` (preventing viewport sizing issues when tabs mount) and trigger smooth `ease-out-cubic` / `ease-in-out-sine` layout animations instead of doing immediate, static jumps.

