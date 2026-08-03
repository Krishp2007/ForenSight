import asyncio
import sys
import os

# Adjust path to import backend modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.app.db.mongodb import connect_to_mongo, close_mongo_connection, db_client
from backend.app.db.neo4j import connect_to_neo4j, close_neo4j_connection, neo4j_client
from backend.app.db.redis import connect_to_redis, close_redis_connection, redis_client
from backend.app.db.minio import connect_to_minio, minio_client
from io import BytesIO

async def test_mongodb_crud():
    print("\n--- Testing MongoDB CRUD ---")
    await connect_to_mongo()
    db = db_client.db
    collection = db["test_collection"]
    
    # Write
    doc = {"name": "Test Organization", "purpose": "ForenSight Testing"}
    insert_result = await collection.insert_one(doc)
    doc_id = insert_result.inserted_id
    print(f"[OK] MongoDB Write Successful. Document ID: {doc_id}")
    
    # Read
    retrieved = await collection.find_one({"_id": doc_id})
    print(f"[OK] MongoDB Read Successful. Data: {retrieved}")
    
    # Clean up
    delete_result = await collection.delete_one({"_id": doc_id})
    print(f"[OK] MongoDB Cleanup Successful. Deleted count: {delete_result.deleted_count}")
    
    await close_mongo_connection()

async def test_neo4j_crud():
    print("\n--- Testing Neo4j CRUD ---")
    await connect_to_neo4j()
    driver = neo4j_client.driver
    
    # Write node and read back in one transaction
    async with driver.session() as session:
        result = await session.run(
            "CREATE (u:User {name: $name}) RETURN u.name AS name",
            name="Alice Investigator"
        )
        record = await result.single()
        print(f"[OK] Neo4j Write & Read Successful. Created user: {record['name']}")
        
        # Clean up
        cleanup_result = await session.run(
            "MATCH (u:User {name: $name}) DETACH DELETE u RETURN count(u) as count",
            name="Alice Investigator"
        )
        cleanup_record = await cleanup_result.single()
        print(f"[OK] Neo4j Cleanup Successful. Deleted nodes: {cleanup_record['count']}")
        
    await close_neo4j_connection()

async def test_redis_crud():
    print("\n--- Testing Redis CRUD ---")
    await connect_to_redis()
    client = redis_client.client
    
    # Write
    await client.set("test_key", "redis_working_fine", ex=10) # 10s expiry
    print("[OK] Redis Write Successful.")
    
    # Read
    value = await client.get("test_key")
    print(f"[OK] Redis Read Successful. Key value: {value}")
    
    # Clean up
    await client.delete("test_key")
    print("[OK] Redis Cleanup Successful.")
    
    await close_redis_connection()

def test_minio_crud():
    print("\n--- Testing MinIO CRUD ---")
    connect_to_minio()
    client = minio_client.client
    bucket = "forensight-evidence"
    
    # Write
    dummy_data = b"Forensic evidence placeholder contents."
    data_stream = BytesIO(dummy_data)
    client.put_object(
        bucket,
        "test_dummy_file.txt",
        data_stream,
        length=len(dummy_data),
        content_type="text/plain"
    )
    print("[OK] MinIO Upload Successful.")
    
    # Read (Check metadata)
    obj_info = client.stat_object(bucket, "test_dummy_file.txt")
    print(f"[OK] MinIO Read Successful. File size: {obj_info.size} bytes.")
    
    # Clean up
    client.remove_object(bucket, "test_dummy_file.txt")
    print("[OK] MinIO Cleanup Successful.")

async def main():
    print("Starting full database read/write integration tests...")
    try:
        await test_mongodb_crud()
        await test_neo4j_crud()
        await test_redis_crud()
        test_minio_crud()
        print("\nALL DATABASE READ/WRITE INTEGRATION TESTS PASSED PERFECTLY!")
        sys.exit(0)
    except Exception as e:
        print(f"\nIntegration test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
