import asyncio, sys
sys.path.insert(0, 'd:/ForenSight/ForenSight')
from backend.app.db.mongodb import connect_to_mongo, db_client

async def run():
    await connect_to_mongo()
    # Clear stale error_message from all parsed evidence
    result = await db_client.db['evidence'].update_many(
        {'status': 'parsed'},
        {'$set': {'error_message': None}}
    )
    print(f"Cleared error_message from {result.modified_count} parsed evidence records")

asyncio.run(run())
