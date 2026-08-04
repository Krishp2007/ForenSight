# 🗑️ ForenSight AI — Complete Evidence Cascade Cleanup Plan (`EVIDENCE_DELETE_FIX_PLAN.md`)

## Executive Summary
This document specifies the complete multi-store cascading deletion architecture for ForenSight AI. Deleting an evidence file executes a guaranteed 10-point cleanup sequence across MongoDB, Neo4j, MinIO, FAISS vector store, Qdrant, Redis, and audit logs.

---

## 1. Current Evidence Ingestion Architecture

```text
User Uploads File (.evtx, .pcapng, .sqlite, .csv)
                    ↓
Evidence Upload API (POST /api/v1/cases/{case_id}/evidence)
                    ↓
1. Raw binary saved to MinIO S3 Object Storage
2. Metadata record inserted into MongoDB 'evidence' collection (status="processing")
3. Background Parsing Pipeline:
   ├─ Parser extracts normalized forensic events
   ├─ Inserted into MongoDB 'events' collection (evidence_id, case_id, org_id)
   ├─ Isolation Forest ML anomaly scoring applied
   ├─ Cypher batch import pushes nodes & edges to Neo4j Graph DB
   └─ VectorStore embeds event text into 384-d FAISS index (/storage/vector_indexes/{case_id}/)
4. Evidence status updated to "parsed"
```

---

## 2. Root Cause Analysis of Stale Data

1. **Async Race Window**: Previously, the delete route returned `HTTP 204` instantly while offloading cleanup to FastAPI `BackgroundTasks`. If the user immediately switched tabs (Graph, Audit Log, Correlations) before the background task completed, stale data rendered.
2. **BSON Type Mismatch**: Some database records stored `evidence_id` as BSON `ObjectId`, while others stored it as a string `"6a6d..."`. Cleanups matching only one format left records behind.
3. **Collection Name Discrepancy**: Audit logs were saved in `audit_log` (singular), but deletion attempted cleanup on `audit_logs` (plural).

---

## 3. Storage Systems & Evidence Lineage Inventory

| Storage System | Collection / Location | Evidence Identifier Field | Deletion Strategy |
| :--- | :--- | :--- | :--- |
| **MongoDB Evidence** | `evidence` collection | `_id: ObjectId(evidence_id)` | Delete primary document |
| **MongoDB Events** | `events` collection | `evidence_id` (`ObjectId` & `str`) | `delete_many` matching `evidence_id` |
| **MongoDB Reports** | `reports` collection | `evidence_id` & `case_id` | `delete_many` cached HTML/Markdown |
| **MongoDB Audit Logs** | `audit_log` & `audit_logs` | `entity_id` & `metadata.evidence_id` | `delete_many` matching ID & filename |
| **Neo4j Graph DB** | Relationships & Nodes | `r.evidence_id` & `n.case_id` | Delete `FORENSIC_ACTION` edges; purge orphan nodes; `DETACH DELETE` case if 0 files remain |
| **FAISS Vector Store** | `/storage/vector_indexes/{case_id}/` | Scoped by `case_id` | Rebuild FAISS index; delete `index.faiss` file if 0 events remain |
| **MinIO S3 Store** | `forensight-evidence` bucket | `minio_object_name` | Remove object from bucket |
| **Redis Cache** | In-Memory (if configured) | `evidence:{id}:*` & `case:{id}:*` | Invalidate & flush keys matching case ID |

---

## 4. Multi-Store Synchronous Cascading Deletion Sequence

```text
                             SYNCHRONOUS EVIDENCE CASCADE DELETION

                                   Delete Request (Frontend)
                                               │
                                               ▼
                              POST /api/v1/cases/{id}/evidence/{eid}
                                               │
                                      Auth & RBAC Check
                                               │
                                               ▼
                                 Step 1: Fetch Evidence Record
                                               │
                                               ▼
                                  Step 2: Delete MinIO Object
                                               │
                                               ▼
                                Step 3: Delete MongoDB Events ($or ObjectId/str)
                                               │
                                               ▼
                                Step 4: Delete Neo4j Edges & Purge Orphans
                                (If 0 files remain → DETACH DELETE ALL case nodes)
                                               │
                                               ▼
                                Step 5: Rebuild / Purge FAISS Vector Store
                                               │
                                               ▼
                                Step 6: Delete Cached MongoDB Reports
                                               │
                                               ▼
                                Step 7: Purge Audit Logs (audit_log & audit_logs)
                                               │
                                               ▼
                                Step 8: Delete Primary Evidence Record
                                               │
                                               ▼
                                 Step 9: Invalidate Redis Cache
                                               │
                                               ▼
                                 Step 10: Return Success JSON
```

---

## 5. Implementation Roadmap & Verification

### Files to Modify:
1. **`backend/app/api/evidence.py`**: Make `_cleanup_evidence_resources` synchronous and execute full 10-point cleanup before deleting primary evidence record.
2. **`backend/app/services/ai/vector_store.py`**: Delete `index.faiss` and `metadata.pkl` files from disk when 0 events remain.
3. **`frontend/src/components/evidence/EvidenceList.jsx`**: Show loading spinner state on deletion and re-fetch backend state immediately after response.

### Verification Checklist:
- [x] **Test 1: Single File Deletion**: Upload single `.evtx` file, delete it, and verify MongoDB events, Neo4j graph, FAISS vectors, and audit logs are 100% clean.
- [x] **Test 2: Multi-File Isolation**: Upload `fileA.evtx` and `fileB.csv`. Delete `fileA.evtx`. Verify `fileB.csv` data remains 100% intact.
- [x] **Test 3: Shared Graph Entities**: Verify shared IP/Host nodes remain if referenced by `fileB.csv`.
- [x] **Test 4: Zero Evidence Reset**: Delete all evidence files and verify Dashboard stats, Knowledge Graph, Correlations, and Audit Trail reset to clean empty states.
