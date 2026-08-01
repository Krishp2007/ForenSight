import asyncio
import sys
sys.path.insert(0, 'd:/ForenSight/ForenSight')

from backend.app.db.mongodb import connect_to_mongo, db_client

async def run():
    await connect_to_mongo()

    users = await db_client.db['users'].find({}).to_list(20)
    print("=== USERS (%d) ===" % len(users))
    for u in users:
        print("  email=%s | username=%s | role=%s | active=%s" % (
            u.get('email'), u.get('username'), u.get('role'), u.get('is_active')
        ))

    orgs = await db_client.db['organizations'].find({}).to_list(10)
    print("=== ORGS (%d) ===" % len(orgs))
    for o in orgs:
        print("  id=%s | name=%s" % (str(o['_id']), o.get('name')))

asyncio.run(run())
