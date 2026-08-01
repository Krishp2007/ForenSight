import asyncio, sys
sys.path.insert(0, 'd:/ForenSight/ForenSight')

from backend.app.db.mongodb import connect_to_mongo, db_client
from backend.app.auth.password import hash_password
from datetime import datetime
from bson import ObjectId

async def run():
    await connect_to_mongo()

    # Use first org
    org = await db_client.db['organizations'].find_one({})
    if not org:
        print("ERROR: No org found. Create one first.")
        return

    email = "admin@forensight.com"
    password = "Admin@12345"

    # Remove existing if any
    await db_client.db['users'].delete_one({"email": email})

    now = datetime.utcnow()
    doc = {
        "email": email,
        "username": "admin",
        "organization_id": org["_id"],
        "role": "admin",
        "hashed_password": hash_password(password),
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    result = await db_client.db['users'].insert_one(doc)
    print("Created user:")
    print("  Email   : %s" % email)
    print("  Password: %s" % password)
    print("  Org     : %s (%s)" % (org.get('name'), str(org['_id'])))
    print("  ID      : %s" % str(result.inserted_id))

asyncio.run(run())
