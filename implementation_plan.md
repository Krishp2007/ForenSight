# ForenSight - Correlations, Focus Neighborhood Toggle, Timelines, & Single File Upload UI Plan

## Overview
This implementation plan addresses four core user requests:
1. **Why Correlations Are Not Showing / Capped at 3**: Root cause analysis and expansion of graph correlation engine rules.
2. **Focus Neighborhood Button Toggle**: Implementation of 2-state toggle ("Focus Neighborhood" / "Cancel Focus Neighborhood") in `NodeDetailsPanel` & `GraphView`.
3. **Why Timelines Are Not Showing**: Restoring top-level navigation tab for Timeline in `CaseDetailPage` and hardening backend event response mapping.
4. **Remove Multi-File Support from UI**: Enforcing single-file uploads in `EvidenceUpload.jsx` UI and file handler.

---

## User Review Required

> [!IMPORTANT]
> - **Correlation Engine Rules**: New correlation rules will be added (e.g. suspicious LOLBin process execution, registry run key persistence, C2 domain resolutions, external IP connections, and anomalous event clusters) so that evidence files generate rich, multi-category correlations rather than returning 0 or being capped at 3.
> - **UI Navigation**: The top tab bar in `CaseDetailPage.jsx` will now display all feature tabs (Dashboard, Evidence Scope, Timeline, Knowledge Graph, Correlations, AI Assistant, Report, Audit Log) so users can directly view and switch to the Timeline tab from the main navigation bar.

---

## Proposed Changes

### 1. Backend Correlation Engine & API
Expand Cypher queries and correlation rules in `GraphCorrelationEngine` to support diverse forensic evidence and generate unlimited granular findings.

#### [MODIFY] [graph_correlation.py](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/services/graph/graph_correlation.py)
- Add new correlation rules:
  - `detect_suspicious_lolbin_execution`: Detect execution of suspicious tools (PowerShell, Cmd, WScript, CScript, Mshta, Certutil, Rundll32, Regsvr32).
  - `detect_registry_persistence`: Detect registry run key modifications (`MODIFIED_REGISTRY`).
  - `detect_domain_c2_resolutions`: Detect domain resolutions to external IP addresses.
  - `detect_anomalous_event_clusters`: Detect clusters of high-severity ML-anomalous events.
- Update `get_all_case_correlations` to aggregate and return all findings across all active rules without artificial limits.

#### [MODIFY] [events.py](file:///d:/ForenSight%20-%20Copy/ForenSight/backend/app/api/events.py)
- Safely populate missing standard fields (subject, action, object, evidence_id, organization_id) when returning event responses so Pydantic serialization never throws 500 errors.

---

### 2. Frontend Graph View & Focus Neighborhood Toggle

#### [MODIFY] [NodeDetailsPanel.jsx](file:///d:/ForenSight%20-%20Copy/ForenSight/frontend/src/components/graph/NodeDetailsPanel.jsx)
- Introduce `isFocused` state to manage the button toggle state.
- 1st click on "Focus Neighborhood":
  - Triggers neighborhood highlighting via `onExpandNeighbors(node)`.
  - Updates button label to **"Cancel Focus Neighborhood"** with active styling.
- 2nd click:
  - Calls `onCancelFocus` handler to clear `.faded` class from all graph elements.
  - Reverts button label back to **"Focus Neighborhood"**.
- Reset `isFocused` state whenever `node.id` changes.

#### [MODIFY] [GraphView.jsx](file:///d:/ForenSight%20-%20Copy/ForenSight/frontend/src/components/graph/GraphView.jsx)
- Pass `onCancelFocus` prop to `NodeDetailsPanel` which executes `cyRef.current.elements().removeClass('faded')`.

---

### 3. Frontend Timeline & Case Detail Navigation

#### [MODIFY] [CaseDetailPage.jsx](file:///d:/ForenSight%20-%20Copy/ForenSight/frontend/src/pages/CaseDetailPage.jsx)
- Update `TAB_CONFIG` to include all tabs: `dashboard`, `evidence`, `timeline`, `graph`, `correlations`, `chat`, `report`, `audit`.
- Fix tab navigation bar so clicking "Timeline" properly highlights and displays the `EventTimeline` component.

#### [MODIFY] [EventTimeline.jsx](file:///d:/ForenSight%20-%20Copy/ForenSight/frontend/src/components/timeline/EventTimeline.jsx)
- Handle API error boundaries gracefully and show informative empty states when no events exist for a filter.

---

### 4. File Upload UI (Single File Support)

#### [MODIFY] [EvidenceUpload.jsx](file:///d:/ForenSight%20-%20Copy/ForenSight/frontend/src/components/evidence/EvidenceUpload.jsx)
- Remove `multiple` attribute from the `<input type="file" />` element.
- Update `handleFiles` logic to accept and upload only a single file (`fileList[0]`).
- Update UI copy:
  - Header: `"Drop an evidence file or click to browse"` (removing `(Multiple Files Supported)`).
  - Subtitle: `"Select a PCAP, SQLite, CSV, JSON, LOG, or TXT file"`.
  - Progress label: `"Uploading <filename> (<progress>%)"`.

---

## Verification Plan

### Automated Tests
- Run backend verification scripts / test suite if available:
  `python -m pytest backend/tests` (or verify via FastAPI endpoints).

### Manual Verification
1. **Correlations Verification**:
   - Open case details -> Correlations tab.
   - Click "Re-run Rules". Verify multiple derived relationships are listed across different rule categories (not capped at 3).
2. **Focus Neighborhood Toggle**:
   - Click a graph node in Knowledge Graph view.
   - Click "Focus Neighborhood": verify target node & neighbors remain clear while other nodes fade, and button text changes to "Cancel Focus Neighborhood".
   - Click "Cancel Focus Neighborhood": verify all nodes return to normal opacity and button text changes back to "Focus Neighborhood".
3. **Timeline Display**:
   - Verify "Timeline" tab is present in the top navigation bar of the Case Detail page.
   - Click "Timeline" tab: verify forensic timeline events load and render chronologically with severity tags.
4. **Single File Upload UI**:
   - Navigate to Evidence Scope tab.
   - Verify file upload box displays single-file text.
   - Test selecting/dropping a single file and verify upload completes cleanly.

