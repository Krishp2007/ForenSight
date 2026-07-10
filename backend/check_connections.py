import asyncio
import sys
import os

# Adjust path to import backend modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.db.mongodb import connect_to_mongo, close_mongo_connection, db_client
from backend.app.db.neo4j import connect_to_neo4j, close_neo4j_connection, neo4j_client
from backend.app.db.redis import connect_to_redis, close_redis_connection, redis_client
from backend.app.db.minio import connect_to_minio, minio_client

async def test_all_connections():
    print("Testing backend connection modules...")
    all_ok = True
    
    # 1. Test Mongo
    try:
        await connect_to_mongo()
        print("[OK] MongoDB module connected successfully!")
        await close_mongo_connection()
    except Exception as e:
        print(f"[FAIL] MongoDB module failed: {e}")
        all_ok = False
        
    # 2. Test Neo4j
    try:
        await connect_to_neo4j()
        print("[OK] Neo4j module connected successfully!")
        await close_neo4j_connection()
    except Exception as e:
        print(f"[FAIL] Neo4j module failed: {e}")
        all_ok = False
        
    # 3. Test Redis
    try:
        await connect_to_redis()
        print("[OK] Redis module connected successfully!")
        await close_redis_connection()
    except Exception as e:
        print(f"[FAIL] Redis module failed: {e}")
        all_ok = False
        
    # 4. Test MinIO
    try:
        connect_to_minio()
        print("[OK] MinIO module connected successfully!")
    except Exception as e:
        print(f"[FAIL] MinIO module failed: {e}")
        all_ok = False

    if all_ok:
        print("\nAll database connector modules successfully validated!")
        sys.exit(0)
    else:
        print("\nSome connection modules failed validation.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_all_connections())
