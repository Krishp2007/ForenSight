"""
Directly trigger pipeline for all uploaded/failed evidence.
Run: python trigger_reprocess.py
"""
import asyncio, sys
sys.path.insert(0, 'd:/ForenSight/ForenSight')

from backend.app.db.mongodb import connect_to_mongo, db_client
from backend.app.services.ingestion.processing_pipeline import _run_full_pipeline

async def main():
    await connect_to_mongo()
    evs = await db_client.db['evidence'].find(
        {'status': {'$in': ['uploaded', 'failed', 'queued']}}
    ).to_list(20)
    
    if not evs:
        print('No stuck evidence found.')
        return
    
    print(f'Processing {len(evs)} evidence file(s)...')
    for e in evs:
        eid = str(e['_id'])
        org = str(e['organization_id'])
        print(f'  Starting: {e["filename"]} ({eid})')
        await _run_full_pipeline(eid, org)
        # Re-check status
        updated = await db_client.db['evidence'].find_one({'_id': e['_id']})
        print(f'  Done: status = {updated.get("status")} | error = {updated.get("error_message")}')

asyncio.run(main())
