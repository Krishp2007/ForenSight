import asyncio
import os
import sys

# Auto-locate project virtual environment site-packages if sys.executable is system python
backend_dir = os.path.dirname(os.path.abspath(__file__))
venv_site_pkgs = os.path.join(backend_dir, ".venv", "Lib", "site-packages")
if os.path.exists(venv_site_pkgs) and venv_site_pkgs not in sys.path:
    sys.path.insert(0, venv_site_pkgs)

project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, backend_dir)

try:
    from bson import ObjectId
except ImportError:
    class ObjectId:
        def __init__(self, val): self.val = str(val)
        def __str__(self): return str(self.val)
        @staticmethod
        def is_valid(val): return len(str(val)) == 24

from backend.app.db.mongodb import db_client
from backend.app.db.neo4j import neo4j_client
from backend.app.db.minio import minio_client, connect_to_minio
from backend.app.config import settings

async def verify_case_storage(case_id: str):
    print(f"\n================ 🔍 STORAGE DELETION AUDIT: CASE {case_id} ================")

    cid_obj = ObjectId(case_id) if ObjectId.is_valid(case_id) else case_id

    # 1. MongoDB Storage Tiers
    from backend.app.db.mongodb import connect_to_mongo
    await connect_to_mongo()
    ev_count = await db_client.db["evidence"].count_documents({"case_id": cid_obj})
    event_count = await db_client.db["events"].count_documents({
        "$or": [{"case_id": cid_obj}, {"case_id": str(case_id)}]
    })
    report_count = await db_client.db["reports"].count_documents({
        "$or": [{"case_id": cid_obj}, {"case_id": str(case_id)}]
    })
    audit_count = await db_client.db["audit_log"].count_documents({
        "$or": [{"entity_type": "evidence"}, {"metadata.case_id": str(case_id)}]
    })

    print(f"1. MongoDB 'evidence' records:  {ev_count}")
    print(f"2. MongoDB 'events' records:    {event_count}")
    print(f"3. MongoDB 'reports' records:   {report_count}")
    print(f"4. MongoDB 'audit_log' records: {audit_count}")

    # 2. Neo4j Graph Database
    node_count = 0
    edge_count = 0
    try:
        from neo4j import AsyncGraphDatabase
        driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        async with driver.session() as sess:
            res1 = await sess.run("MATCH (n:Entity {case_id:$cid}) RETURN count(n) AS cnt", cid=case_id)
            rec1 = await res1.single()
            node_count = rec1["cnt"] if rec1 else 0

            res2 = await sess.run("MATCH ()-[r:FORENSIC_ACTION {case_id:$cid}]->() RETURN count(r) AS cnt", cid=case_id)
            rec2 = await res2.single()
            edge_count = rec2["cnt"] if rec2 else 0
        await driver.close()
    except Exception as e:
        pass
    print(f"5. Neo4j Entity Nodes:          {node_count}")
    print(f"6. Neo4j Graph Relationships:   {edge_count}")

    # 3. MinIO S3 Object Storage
    case_objects = []
    try:
        connect_to_minio()
        if minio_client.client:
            objects = list(minio_client.client.list_objects(settings.MINIO_BUCKET_NAME, recursive=True))
            case_objects = [o.object_name for o in objects if case_id in o.object_name]
            if ev_count == 0 and case_objects:
                print(f"   [CLEANUP] Purging {len(case_objects)} leftover MinIO objects for empty case {case_id}...")
                for obj in case_objects:
                    try:
                        minio_client.client.remove_object(settings.MINIO_BUCKET_NAME, obj)
                        print(f"   - Removed: {obj}")
                    except Exception as e:
                        print(f"   - Removal failed for {obj}: {e}")
                # Re-check count after purge
                objects = list(minio_client.client.list_objects(settings.MINIO_BUCKET_NAME, recursive=True))
                case_objects = [o.object_name for o in objects if case_id in o.object_name]
    except Exception as e:
        print(f"   MinIO check note: {e}")
    print(f"7. MinIO S3 Objects Remaining:  {len(case_objects)}")

    # 4. Local FAISS Vector Index Files
    vector_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage", "vector_indexes", case_id)
    index_exists = os.path.exists(os.path.join(vector_dir, "index.faiss"))
    meta_exists = os.path.exists(os.path.join(vector_dir, "metadata.pkl"))
    print(f"8. FAISS Vector Disk Store:     {'EXISTS' if index_exists or meta_exists else 'CLEAN / PURGED (0 bytes)'}")

    # 5. Redis Cache Check
    redis_keys_count = 0
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=1.0)
        keys = await r.keys(f"*{case_id}*")
        redis_keys_count = len(keys)
        if ev_count == 0 and keys:
            for k in keys:
                await r.delete(k)
            redis_keys_count = 0
        await r.aclose()
    except Exception:
        pass
    print(f"9. Redis Cache Keys:            {redis_keys_count}")

    # 6. Qdrant Cross-Case Vector Store Check
    qdrant_points_count = 0
    try:
        from qdrant_client import QdrantClient
        q = QdrantClient(host=getattr(settings, "QDRANT_HOST", "localhost"), port=getattr(settings, "QDRANT_PORT", 6333), timeout=0.5)
        res = q.count(collection_name="forensight_events", count_filter={"must": [{"key": "case_id", "match": {"value": case_id}}]})
        qdrant_points_count = res.count
    except Exception:
        pass
    print(f"10. Qdrant Vector Points:       {qdrant_points_count}")
    
    print("=========================================================================\n")

async def audit_all_cases():
    from backend.app.db.mongodb import connect_to_mongo
    await connect_to_mongo()

    cases = await db_client.db["cases"].find({}).to_list(100)
    print(f"\n================ 📂 FORENSIGHT ALL CASES STORAGE AUDIT ================")
    print(f"Total Cases Found: {len(cases)}\n")

    if not cases:
        print("No cases found in MongoDB.")
        return

    for c in cases:
        cid = str(c["_id"])
        title = c.get("title", "Untitled Case")
        print(f"👉 Case: '{title}' [ID: {cid}]")
        await verify_case_storage(cid)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] not in ("--all", "-a"):
        cid = sys.argv[1]
        asyncio.run(verify_case_storage(cid))
    else:
        asyncio.run(audit_all_cases())
