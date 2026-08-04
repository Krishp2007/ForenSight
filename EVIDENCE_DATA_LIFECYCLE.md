# 🔄 ForenSight AI — Evidence Data Lifecycle & Cascade Deletion (`EVIDENCE_DATA_LIFECYCLE.md`)

## 1. Complete Evidence Ingestion & Storage Lifecycle

```text
                                INGESTION & PROCESSING LIFECYCLE

                                      Upload File (Frontend)
                                                │
                                                ▼
                               POST /api/v1/cases/{id}/evidence
                                                │
                                                ▼
                              1. Save Binary Stream to MinIO
                                                │
                                                ▼
                            2. Create MongoDB 'evidence' Record
                                                │
                                                ▼
                             3. Async Ingestion Pipeline Run
                                 /      |       |      \
                                /       |       |       \
                               ▼        ▼       ▼        ▼
                          MongoDB    PyOD ML  Neo4j   FAISS Index
                          'events'   Anomaly  Graph   /storage/vector_indexes/
```

---

## 2. Evidence Cascade Deletion Architecture

```text
                                CASCADE DELETION LIFECYCLE

                                 DELETE Evidence Request
                                            │
                                            ▼
                           DELETE /api/v1/cases/{cid}/evidence/{eid}
                                            │
                                            ▼
                             1. Delete MongoDB Evidence Record
                                            │
                                            ▼
                           2. Delete MinIO S3 Binary Object
                                            │
                                            ▼
                           3. Delete MongoDB 'events' Records
                              ($or ObjectId & String matching)
                                            │
                                            ▼
                           4. Delete Neo4j Edges & Purge Orphans
                              (If 0 files remain → DETACH DELETE Case)
                                            │
                                            ▼
                           5. Rebuild FAISS Vector Store Index
                              (If 0 events remain → Delete disk files)
                                            │
                                            ▼
                           6. Purge Cached Reports from MongoDB
                                            │
                                            ▼
                           7. Purge Evidence & Case Audit Logs
                              (From both 'audit_log' & 'audit_logs')
                                            │
                                            ▼
                           8. Invalidate Redis & Case Stats Cache
                                            │
                                            ▼
                           9. Return HTTP 204 Success Response
```

---

## 3. Storage System Inventory & Deletion Mapping

| Storage System | Component Name | Evidence ID Field | Deletion Command |
| :--- | :--- | :--- | :--- |
| **MongoDB** | `evidence` collection | `_id: ObjectId(id)` | `delete_one({"_id": ObjectId(id)})` |
| **MongoDB** | `events` collection | `evidence_id` | `delete_many({"$or": [{"evidence_id": id}, {"evidence_id": ObjectId(id)}]})` |
| **MongoDB** | `reports` collection | `evidence_id` & `case_id` | `delete_many({"$or": [{"evidence_id": id}, {"case_id": case_id}]})` |
| **MongoDB** | `audit_log` & `audit_logs` | `entity_id` & `metadata.evidence_id` | `delete_many(...)` matching evidence ID and filename |
| **Neo4j** | `FORENSIC_ACTION` edges | `r.evidence_id` | `MATCH ()-[r:FORENSIC_ACTION]->() WHERE r.evidence_id = $eid DELETE r` |
| **Neo4j** | Orphan Entity Nodes | `n.case_id` | `MATCH (n {case_id:$cid}) WHERE NOT (n)--() DELETE n` |
| **Neo4j** | Empty Case Reset | `n.case_id` | `MATCH (n {case_id:$cid}) DETACH DELETE n` (if 0 files remain) |
| **FAISS** | Disk Vector Store | `/vector_indexes/{case_id}/` | Rebuild index; remove `index.faiss` & `metadata.pkl` if 0 events |
| **MinIO** | `forensight-evidence` bucket | `minio_object_name` | `minio_client.remove_object(...)` |

---

## 4. Shared Data vs Evidence Data Distinction

1. **Global Data (Preserved)**: MITRE ATT&CK technique definitions, system configuration, system users.
2. **Shared Nodes (Preserved until orphaned)**: Process types, IPs, Users referenced by multiple evidence files.
3. **Evidence Data (Deleted)**: Raw binary file, parsed events, file-specific audit logs, cached reports.

---

## 5. Authoritative Status & Scan Time Lifecycle

```text
                               STATUS & TIMESTAMP LIFECYCLE

      Frontend Upload          POST /evidence          Pipeline Starts          Pipeline Finishes
            │                        │                        │                         │
            ▼                        ▼                        ▼                         ▼
    Status: "uploading"     Status: "uploaded"        Status: "parsing"         Status: "parsed"
      Scan Time: —         created_at = server      parsing_started_at = server   parsed_at = server
                              Scan Time: 0s            Scan Time: Live ⏳        Scan Time: Frozen Duration
```

### Server Fields:
* `status`: `"uploaded"` → `"parsing"` → `"parsed"` (or `"failed"`)
* `created_at`: Backend server UTC timestamp when file binary is received.
* `parsing_started_at`: Backend server UTC timestamp when parser thread starts.
* `parsed_at`: Backend server UTC timestamp when event bulk-insert completes.
* `scan_duration`: Server duration calculated as `parsed_at - parsing_started_at`.

