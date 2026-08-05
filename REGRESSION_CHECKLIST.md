# ForenSight Feature Invariants & Regression Checklist

This document tracks all permanent feature invariants and regression verification checks for the **ForenSight** forensic investigation platform. Every future feature modification must preserve these invariants without exception.

---

## 📌 Permanent Feature Invariants

### 1. Evidence Live Scan Timer Stopwatch
* **Active Scanning**: Immediately when evidence processing starts (`parsing`, `queued`, `uploaded`, `processing`, `analyzing`, `building_graph`, `correlating`), the scan time updates live every 1 second: `0s → 1s → 2s → 3s ...`.
* **Terminal Status Freeze**: When processing completes (`parsed`, `completed`, `failed`, `cancelled`), the timer **STOPS** and freezes permanently at the exact measured duration (e.g. `47s`).
* **No Infinite Live Clock on Parsed Files**: A `parsed` or `completed` file must **NEVER** calculate `Date.now() - processing_started_at` (which causes timers to climb to 1900s, 2000s, etc.).
* **Page Refresh & Case Switch Persistence**: Refreshing the page or switching cases 10 minutes later must display the frozen final duration (e.g. `47s`).

### 2. Evidence Re-Processing Idempotency & Clean-Up
* **Preserve Original Physical File**: Clicking **Re-process** must NEVER delete or replace the raw evidence file stored in MinIO S3.
* **Scoped Derived Data Purge**: Purges old MongoDB `events` and old Neo4j `Event` nodes for the target `evidence_id` **BEFORE** newly parsed events are inserted.
* **No Event Duplication**: Re-processing the same evidence file 1 or 5 times leaves event, anomaly, critical event, and graph correlation counts equal to a single run ($4,013 \rightarrow 4,013$).
* **Timer Reset**: Clicking Re-process resets completion timestamps (`processing_finished_at = null`, `scan_duration_ms = null`), updates `processing_started_at = current_time`, sets `status = "parsing"`, and restarts the live stopwatch at `0s`.

### 3. Complete Case & Evidence Data Isolation
* **Case Tenant Boundary**: Every case (`case_id`) is a strict investigation boundary. Case A data must never bleed into Case B.
* **Neo4j Domain Node Case Isolation**: All Neo4j domain nodes (`Process`, `User`, `Host`, `IPAddress`, `Domain`, `Port`, `RegistryKey`, `File`) have primary composite IDs scoped by `case_id` (e.g., `Process` = `{case_id}:{hostname}:{pid}:{proc_name}`, `IPAddress` = `{case_id}:{address}`). Multi-hop graph traversals for Case 1 will **never** physically cross into Case 2.
* **Evidence-Level vs Case-Level Reports & Stats**: Viewing an individual evidence file displays statistics for that evidence file only. Viewing the Case Dashboard displays aggregated totals across all evidence belonging to that case.
* **AI Copilot & Report Isolation**: All AI Copilot context retrieval and Report compilation queries receive and enforce `case_id` and `organization_id` at the database/backend level.

---

## 📋 Pre-Flight Regression Verification Checklist

Run these checks after making any modification:

- [x] **Check 1: Live Scan Time**: Active upload/parsing ticks `0s → 1s → 2s ...`.
- [x] **Check 2: Timer Freezes at Parsed**: Parsed evidence freezes at final duration (e.g. `47s`) and does NOT climb to 1900s+.
- [x] **Check 3: Refresh Preserves Final Time**: Refreshing a page with parsed evidence displays `47s`.
- [x] **Check 4: Re-process Restarts Timer**: Clicking Re-process resets scan time to `0s` and ticks live.
- [x] **Check 5: Re-process Event Deduplication**: Re-processing does not double event, anomaly, or graph counts.
- [x] **Check 6: Cases Remain Isolated**: Case A events/graph nodes never appear in Case B dashboard or graph views.
- [x] **Check 7: Evidence Derived Data Isolated**: Re-processing Evidence A1 does not touch Evidence A2 or Evidence B1.
- [x] **Check 8: Neo4j Graph Case-Scoped**: Traversals in Case A do not traverse through shared IPs into Case B.
- [x] **Check 9: AI Copilot Case-Scoped**: AI responses for Case A include only Case A evidence files and citations.
