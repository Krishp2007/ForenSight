import logging
from neo4j import AsyncGraphDatabase, AsyncDriver
from backend.app.config import settings

logger = logging.getLogger(__name__)

class Neo4jDB:
    driver: AsyncDriver = None

neo4j_client = Neo4jDB()

async def connect_to_neo4j():
    logger.info("Connecting to Neo4j...")
    try:
        neo4j_client.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URL,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        # Verify connection
        await neo4j_client.driver.verify_connectivity()
        logger.info("Successfully connected to Neo4j!")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        raise e

async def close_neo4j_connection():
    logger.info("Closing Neo4j connection...")
    if neo4j_client.driver:
        await neo4j_client.driver.close()
        logger.info("Neo4j connection closed.")
