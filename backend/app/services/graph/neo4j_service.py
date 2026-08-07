"""
Neo4j Service Layer — ForenSight
=================================
Manages Neo4j connections, sessions, parameterized transactions, retry logic,
graceful shutdown, and database constraint migrations for domain nodes.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from backend.app.config import settings

logger = logging.getLogger(__name__)


class Neo4jService:
    """
    Singleton-style service encapsulating official Neo4j Python AsyncDriver.
    Ensures per-event-loop driver caching and thread-safe session acquisition.
    """

    def __init__(self):
        self._drivers: Dict[asyncio.AbstractEventLoop, AsyncDriver] = {}

    @property
    def uri(self) -> str:
        return settings.NEO4J_URI or settings.NEO4J_URL

    @property
    def username(self) -> str:
        return settings.NEO4J_USERNAME or settings.NEO4J_USER

    @property
    def password(self) -> str:
        return settings.NEO4J_PASSWORD

    @property
    def database(self) -> str:
        return settings.NEO4J_DATABASE or "neo4j"

    def get_driver(self) -> Optional[AsyncDriver]:
        """Obtain or initialize the AsyncDriver for the current running event loop."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

        if loop not in self._drivers or self._drivers[loop] is None:
            logger.info(f"[Neo4jService] Connecting to Neo4j at {self.uri} (DB: {self.database})")
            try:
                self._drivers[loop] = AsyncGraphDatabase.driver(
                    self.uri,
                    auth=(self.username, self.password),
                )
            except Exception as err:
                logger.error(f"[Neo4jService] Driver creation failed: {err}")
                return None

        return self._drivers[loop]

    async def verify_connection(self) -> bool:
        """Verify Neo4j server reachability and credentials."""
        driver = self.get_driver()
        if not driver:
            return False
        try:
            await driver.verify_connectivity()
            logger.info("[Neo4jService] ✅ Connection verified successfully.")
            return True
        except Exception as e:
            logger.warning(f"[Neo4jService] ⚠️ Connectivity check failed: {e}")
            return False

    async def init_constraints_and_indexes(self) -> None:
        """Ensure uniqueness constraints and performance indexes for all 12 domain node types."""
        driver = self.get_driver()
        if not driver:
            return

        constraints = [
            "CREATE CONSTRAINT case_id_unique IF NOT EXISTS FOR (c:Case) REQUIRE c.case_id IS UNIQUE",
            "CREATE CONSTRAINT evidence_id_unique IF NOT EXISTS FOR (e:Evidence) REQUIRE e.evidence_id IS UNIQUE",
            "CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (ev:Event) REQUIRE ev.event_id IS UNIQUE",
            "CREATE CONSTRAINT browser_visit_event_id_unique IF NOT EXISTS FOR (v:BrowserVisit) REQUIRE v.event_id IS UNIQUE",
            "CREATE CONSTRAINT domain_id_unique IF NOT EXISTS FOR (d:Domain) REQUIRE d.domain_id IS UNIQUE",
            "CREATE CONSTRAINT process_id_unique IF NOT EXISTS FOR (p:Process) REQUIRE p.process_id IS UNIQUE",
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
            "CREATE CONSTRAINT host_id_unique IF NOT EXISTS FOR (h:Host) REQUIRE h.host_id IS UNIQUE",
            "CREATE CONSTRAINT file_id_unique IF NOT EXISTS FOR (f:File) REQUIRE f.file_id IS UNIQUE",
            "CREATE CONSTRAINT ip_id_unique IF NOT EXISTS FOR (ip:IPAddress) REQUIRE ip.ip_id IS UNIQUE",
            "CREATE CONSTRAINT port_id_unique IF NOT EXISTS FOR (pt:Port) REQUIRE pt.port_id IS UNIQUE",
            "CREATE CONSTRAINT registry_key_id_unique IF NOT EXISTS FOR (r:RegistryKey) REQUIRE r.reg_id IS UNIQUE",
            "CREATE CONSTRAINT service_id_unique IF NOT EXISTS FOR (s:Service) REQUIRE s.service_id IS UNIQUE",
        ]

        indexes = [
            # Event indexes
            "CREATE INDEX event_timestamp_idx IF NOT EXISTS FOR (ev:Event) ON (ev.timestamp)",
            "CREATE INDEX event_case_idx IF NOT EXISTS FOR (ev:Event) ON (ev.case_id)",
            "CREATE INDEX event_evidence_idx IF NOT EXISTS FOR (ev:Event) ON (ev.evidence_id)",
            # BrowserVisit indexes
            "CREATE INDEX browser_visit_case_idx IF NOT EXISTS FOR (v:BrowserVisit) ON (v.case_id)",
            "CREATE INDEX browser_visit_evidence_idx IF NOT EXISTS FOR (v:BrowserVisit) ON (v.evidence_id)",
            "CREATE INDEX browser_visit_domain_idx IF NOT EXISTS FOR (v:BrowserVisit) ON (v.case_id, v.evidence_id)",
            # Domain indexes
            "CREATE INDEX domain_case_idx IF NOT EXISTS FOR (d:Domain) ON (d.case_id)",
            "CREATE INDEX domain_name_idx IF NOT EXISTS FOR (d:Domain) ON (d.domain_name)",
            # Process indexes
            "CREATE INDEX process_name_idx IF NOT EXISTS FOR (p:Process) ON (p.process_name)",
            "CREATE INDEX process_case_idx IF NOT EXISTS FOR (p:Process) ON (p.case_id)",
            # IPAddress, User, Host, File, Port, RegistryKey, Service indexes
            "CREATE INDEX ip_case_idx IF NOT EXISTS FOR (ip:IPAddress) ON (ip.case_id)",
            "CREATE INDEX user_case_idx IF NOT EXISTS FOR (u:User) ON (u.case_id)",
            "CREATE INDEX host_case_idx IF NOT EXISTS FOR (h:Host) ON (h.case_id)",
            "CREATE INDEX file_case_idx IF NOT EXISTS FOR (f:File) ON (f.case_id)",
            "CREATE INDEX port_case_idx IF NOT EXISTS FOR (pt:Port) ON (pt.case_id)",
            "CREATE INDEX registry_case_idx IF NOT EXISTS FOR (r:RegistryKey) ON (r.case_id)",
            "CREATE INDEX service_case_idx IF NOT EXISTS FOR (s:Service) ON (s.case_id)",
        ]

        try:
            async with driver.session(database=self.database) as session:
                for c in constraints:
                    try:
                        await session.run(c)
                    except Exception as ce:
                        logger.debug(f"[Neo4jService] Constraint notice: {ce}")
                for idx in indexes:
                    try:
                        await session.run(idx)
                    except Exception as ie:
                        logger.debug(f"[Neo4jService] Index notice: {ie}")
            logger.info("[Neo4jService] ✅ Domain constraints and indexes verified.")
        except Exception as err:
            logger.warning(f"[Neo4jService] Schema constraint setup skipped: {err}")

    async def execute_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Run a parameterized Cypher read/write query safely inside an async session."""
        driver = self.get_driver()
        if not driver:
            return []

        parameters = parameters or {}
        try:
            async with driver.session(database=self.database) as session:
                result = await session.run(query, parameters)
                records = await result.data()
                # Always consume() to ensure write transactions are fully committed.
                # For queries with no RETURN clause, data() returns [] immediately
                # without flushing the write — consume() forces the server to execute.
                await result.consume()
                return records
        except Exception as e:
            logger.error(f"[Neo4jService] Query execution error: {e}\nQuery: {query[:200]}")
            return []

    async def execute_write_batch(
        self, query: str, batch: List[Dict[str, Any]]
    ) -> int:
        """Run a parameterized UNWIND batch query."""
        if not batch:
            return 0
        driver = self.get_driver()
        if not driver:
            return 0

        try:
            async with driver.session(database=self.database) as session:
                result = await session.run(query, batch=batch)
                summary = await result.consume()
                return summary.counters.nodes_created + summary.counters.relationships_created
        except Exception as e:
            logger.error(f"[Neo4jService] Batch write error: {e}")
            return 0

    async def close(self) -> None:
        """Gracefully close all active driver instances."""
        logger.info("[Neo4jService] Closing driver connections...")
        loop_keys = list(self._drivers.keys())
        for loop in loop_keys:
            try:
                drv = self._drivers[loop]
                if drv:
                    await drv.close()
                del self._drivers[loop]
            except Exception:
                pass
        logger.info("[Neo4jService] All connections closed.")


neo4j_service = Neo4jService()
