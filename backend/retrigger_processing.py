"""Re-trigger Celery processing for all stuck 'uploaded' evidence — no scapy import."""
import asyncio, sys, os

# Point scapy cache to a writable temp dir before any import
os.environ['SCAPY_CACHE_DIR'] = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'scapy_cache')
os.makedirs(os.environ['SCAPY_CACHE_DIR'], exist_ok=True)

sys.path.insert(0, 'd:/ForenSight/ForenSight')

from backend.app.db.mongodb import connect_to_mongo, db_client
from backend.app.db.redis import connect_to_redis
import redis as redis_sync

async def run():
    await connect_to_mongo()

    stuck = await db_client.db['evidence'].find({'status': 'uploaded'}).to_list(50)
    print(f"Found {len(stuck)} stuck evidence records")

    if not stuck:
        print("Nothing to process.")
        return

    # Push tasks directly to Redis/Celery queue without importing scapy
    r = redis_sync.from_url("redis://localhost:6379/0")
    import json, uuid

    for e in stuck:
        eid = str(e['_id'])
        oid = str(e['organization_id'])
        fname = e.get('filename', 'unknown')
        print(f"  Queuing: {fname} (id={eid})")

        # Celery task message format
        task_id = str(uuid.uuid4())
        msg = {
            "id": task_id,
            "task": "backend.app.worker.parser_tasks.process_evidence_task",
            "args": [eid, oid],
            "kwargs": {},
            "retries": 0,
            "eta": None,
            "expires": None,
            "utc": True,
            "callbacks": None,
            "errbacks": None,
            "timelimit": [None, None],
            "taskset": None,
            "chord": None,
        }
        r.lpush("celery", json.dumps(msg))
        print(f"    -> Task {task_id} pushed to Celery queue")

    print(f"\nDone — {len(stuck)} task(s) queued. Check Celery worker window.")

asyncio.run(run())
