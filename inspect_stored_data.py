import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["forensight"]
    
    cases = await db.cases.find({}).to_list(100)
    print("=== CASES IN MONGODB ===")
    for c in cases:
        print(f"Case ID: {c.get('_id')} | Title: {c.get('title')} | Status: {c.get('status')}")

    evidence = await db.evidence.find({}).to_list(100)
    print("\n=== EVIDENCE FILES IN MONGODB ===")
    for e in evidence:
        case_id = str(e.get("case_id"))
        ev_id = str(e.get("_id"))
        filename = e.get("filename")
        file_type = e.get("file_type")
        status = e.get("status")
        duration = e.get("scan_duration_ms")
        
        # Count events for this evidence
        ev_count = await db.events.count_documents({"evidence_id": e.get("_id")})
        if ev_count == 0:
            ev_count = await db.events.count_documents({"evidence_id": str(e.get("_id"))})
            
        print(f"Evidence ID: {ev_id} | Case: {case_id} | File: {filename} ({file_type}) | Status: {status} | Duration: {duration}ms | Event Count: {ev_count}")

    print("\n=== TOTAL EVENTS COLLECTION COUNT ===")
    total_events = await db.events.count_documents({})
    print(f"Total events in MongoDB: {total_events}")

if __name__ == "__main__":
    asyncio.run(main())
