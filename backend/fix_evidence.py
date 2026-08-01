"""
One-shot script — resets all stuck evidence and re-triggers processing.
Run with: python fix_evidence.py
"""
import asyncio
import sys
sys.path.insert(0, 'd:/ForenSight/ForenSight')

from backend.app.db.mongodb import connect_to_mongo, db_client


async def main():
    await connect_to_mongo()

    # Reset every stuck record back to 'uploaded' so pipeline will re-run
    result = await db_client.db['evidence'].update_many(
        {'status': {'$in': ['queued', 'parsing']}},
        {'$set': {'status': 'uploaded', 'error_message': None}}
    )
    print(f"Reset {result.modified_count} stuck evidence records -> 'uploaded'")

    # Show all evidence
    evs = await db_client.db['evidence'].find({}).sort('created_at', -1).limit(20).to_list(20)
    print("\nAll evidence:")
    for e in evs:
        print(f"  {e.get('filename'):30s}  status={e.get('status'):10s}  "
              f"id={str(e['_id'])}  case={str(e['case_id'])}")

    print("\nDone. Now use the Re-process button in the Evidence tab for each file.")

asyncio.run(main())
