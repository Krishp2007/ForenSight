import logging
import asyncio
from neo4j import AsyncGraphDatabase, AsyncDriver
from backend.app.config import settings

logger = logging.getLogger(__name__)

class Neo4jDB:
    def __init__(self):
        self._drivers = {}

    @property
    def driver(self) -> AsyncDriver:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop not in self._drivers:
            logger.info(f"Creating new Neo4j AsyncDriver connection for loop {id(loop)}")
            self._drivers[loop] = AsyncGraphDatabase.driver(
                settings.NEO4J_URL,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
        return self._drivers[loop]

neo4j_client = Neo4jDB()

async def connect_to_neo4j():
    logger.info("Initializing Neo4j connection...")
    try:
        driver = neo4j_client.driver
        await driver.verify_connectivity()
        logger.info("Successfully connected to Neo4j!")

        # Ensure indexes exist so MERGE operations are fast (not full graph scans)
        try:
            async with driver.session() as session:
                await session.run(
                    "CREATE INDEX entity_lookup IF NOT EXISTS "
                    "FOR (n:Entity) ON (n.name, n.case_id, n.organization_id)"
                )
            logger.info("Neo4j Entity index ensured.")
        except Exception as idx_err:
            logger.warning(f"Neo4j index creation skipped (non-fatal): {idx_err}")

    except Exception as e:
        logger.warning(
            f"Neo4j unavailable — graph features disabled. Start Neo4j to enable them. ({e})"
        )

async def close_neo4j_connection():
    logger.info("Closing Neo4j connections...")
    loop_keys = list(neo4j_client._drivers.keys())
    for loop in loop_keys:
        try:
            await neo4j_client._drivers[loop].close()
            del neo4j_client._drivers[loop]
        except Exception:
            pass
    logger.info("All Neo4j connections closed.")
