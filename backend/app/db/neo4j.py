import logging
from backend.app.services.graph.neo4j_service import neo4j_service

logger = logging.getLogger(__name__)


class Neo4jDB:
    @property
    def driver(self):
        return neo4j_service.get_driver()


neo4j_client = Neo4jDB()


async def connect_to_neo4j():
    logger.info("Initializing Neo4j connection...")
    try:
        ok = await neo4j_service.verify_connection()
        if ok:
            await neo4j_service.init_constraints_and_indexes()
            logger.info("Successfully connected to Neo4j and initialized schema!")
        else:
            logger.warning("Neo4j unavailable — graph features disabled.")
    except Exception as e:
        logger.warning(
            f"Neo4j unavailable — graph features disabled. Start Neo4j to enable them. ({e})"
        )


async def close_neo4j_connection():
    await neo4j_service.close()

