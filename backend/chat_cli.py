import os
import sys
import asyncio
import io

import warnings

# Suppress harmless third-party and HuggingFace Hub warnings
warnings.filterwarnings("ignore")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Force UTF-8 terminal encoding on Windows stdout/stderr to print emojis safely
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Adjust path to import backend modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.db.mongodb import connect_to_mongo, close_mongo_connection, db_client
from backend.app.db.neo4j import connect_to_neo4j, close_neo4j_connection
from backend.app.db.redis import connect_to_redis, close_redis_connection
from backend.app.services.ai.copilot import CopilotService

async def start_interactive_chat():
    print("==================================================")
    print("      FORENSIGHT AI COPILOT INTERACTIVE CHAT      ")
    print("==================================================")
    print("Connecting to databases...")
    await connect_to_mongo()
    await connect_to_neo4j()
    await connect_to_redis()
    
    try:
        # Find the latest case in the database to chat about
        latest_case = await db_client.db["cases"].find_one({}, sort=[("created_at", -1)])
        
        if not latest_case:
            print("\n[ERROR] No cases found in the database. Please run 'py save_demo_report.py' first to build a case with logs.")
            return
            
        case_id = str(latest_case["_id"])
        org_id = str(latest_case["organization_id"])
        
        print(f"\n[Active Case]: '{latest_case['title']}'")
        print(f"[Case ID]: {case_id}")
        print("--------------------------------------------------")
        print("Welcome! Type your forensic query below (e.g. 'Show me the PowerShell anomalies' or 'What processes spawned slack.exe?').")
        print("Type 'exit' or 'quit' to close the chat.")
        print("--------------------------------------------------")
        
        while True:
            try:
                # Ask user for prompt
                user_question = input("\nInvestigator > ").strip()
                if not user_question:
                    continue
                if user_question.lower() in ("exit", "quit"):
                    print("Goodbye!")
                    break
                    
                print("\nAI Copilot is thinking...")
                response_text = await CopilotService.analyze_case_timeline(
                    case_id=case_id,
                    org_id=org_id,
                    question=user_question
                )
                
                print("\n------------------ Copilot Response ------------------")
                print(response_text)
                print("------------------------------------------------------")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\n[ERROR] Chat invocation error: {e}")
                
    finally:
        await close_mongo_connection()
        await close_neo4j_connection()
        await close_redis_connection()

if __name__ == "__main__":
    try:
        asyncio.run(start_interactive_chat())
    except KeyboardInterrupt:
        pass
