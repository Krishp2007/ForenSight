import asyncio, sys
sys.path.insert(0, 'd:/ForenSight/ForenSight')
from backend.app.db.mongodb import connect_to_mongo, db_client

async def run():
    await connect_to_mongo()
    evs = await db_client.db['evidence'].find({}).sort('created_at', -1).limit(10).to_list(10)
    for e in evs:
        cnt = await db_client.db['events'].count_documents({'evidence_id': e['_id']})
        print(f"{e.get('filename'):30s} status={e.get('status'):10s} events={cnt:6d} err={e.get('error_message')}")

asyncio.run(run())
