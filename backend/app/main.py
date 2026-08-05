import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from backend.app.config import settings
from backend.app.db.mongodb import connect_to_mongo, close_mongo_connection
from backend.app.db.neo4j import connect_to_neo4j, close_neo4j_connection
from backend.app.db.redis import connect_to_redis, close_redis_connection
from backend.app.db.minio import connect_to_minio

# Configure logger logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def _recover_stuck_evidence():
    """
    On startup, find any evidence stuck in 'queued' or 'parsing' state
    from a previous crash and automatically re-run the pipeline for them.
    Runs as a background task so it doesn't block startup.
    """
    try:
        # Small delay to let the event loop settle after startup
        await asyncio.sleep(3)
        from backend.app.db.mongodb import db_client
        from backend.app.services.ingestion.processing_pipeline import _run_full_pipeline

        stuck = await db_client.db["evidence"].find(
            {"status": {"$in": ["uploaded", "queued", "parsing", "processing", "analyzing", "building_graph", "correlating"]}}
        ).to_list(50)

        if not stuck:
            logger.info("[RECOVERY] No stuck evidence found.")
            return

        logger.warning(f"[RECOVERY] Found {len(stuck)} stuck evidence file(s) — re-processing...")
        for ev in stuck:
            evidence_id = str(ev["_id"])
            org_id      = str(ev["organization_id"])
            filename    = ev.get("filename", evidence_id)
            logger.info(f"[RECOVERY] Re-processing: {filename} ({evidence_id})")
            # Reset to uploaded so the pipeline starts fresh
            await db_client.db["evidence"].update_one(
                {"_id": ev["_id"]},
                {"$set": {"status": "uploaded", "error_message": None}}
            )
            asyncio.create_task(_run_full_pipeline(evidence_id, org_id))

        logger.info(f"[RECOVERY] Scheduled {len(stuck)} recovery pipeline(s).")
    except Exception as e:
        logger.error(f"[RECOVERY] Startup recovery failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing infrastructure database clients...")
    try:
        await connect_to_mongo()
        logger.info("MongoDB successfully connected during application startup!")
    except Exception as e:
        logger.warning(f"MongoDB connection warning on startup (database queries may fail until connected): {e}")

    try:
        await connect_to_neo4j()
        logger.info("Neo4j successfully connected!")
    except Exception as e:
        logger.warning(f"Neo4j connection warning (graph queries disabled): {e}")

    try:
        await connect_to_redis()
        logger.info("Redis successfully connected!")
    except Exception as e:
        logger.warning(f"Redis connection warning (caching/pubsub disabled): {e}")

    try:
        connect_to_minio()
        logger.info("MinIO/S3 successfully connected!")
    except Exception as e:
        logger.warning(f"MinIO/S3 connection warning (file uploads disabled): {e}")

    logger.info("FastAPI Application Startup Complete!")

    from backend.app.utils.memory_profiler import log_memory
    log_memory("application_startup_idle")

    # ── Recovery: re-queue any evidence stuck in queued/parsing from a previous crash
    asyncio.create_task(_recover_stuck_evidence())

    yield

    # Shutdown actions
    logger.info("Closing infrastructure database connections...")
    await close_mongo_connection()
    await close_neo4j_connection()
    await close_redis_connection()
    logger.info("All connections closed cleanly. Goodbye!")

app = FastAPI(
    title="ForenSight AI Backend API",
    description="Event-Driven Modular Digital Forensics & AI Copilot Analysis Platform",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,   # prevents 307 redirects that strip Authorization header
)

# Set up CORS and GZip compression middleware rules
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Import and include API routers
from backend.app.api.auth import router as auth_router
from backend.app.api.organizations import router as org_router
from backend.app.api.cases import router as cases_router
from backend.app.api.evidence import router as evidence_router
from backend.app.api.events import router as events_router
from backend.app.api.graph import router as graph_router
from backend.app.api.chat import router as chat_router
from backend.app.api.similarity import router as similarity_router
from backend.app.api.reports import router as reports_router
from backend.app.api.audit import router as audit_router
from backend.app.api.correlations import router as correlations_router
from backend.app.api.users import router as users_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(org_router, prefix="/api/v1")
app.include_router(cases_router, prefix="/api/v1")
app.include_router(evidence_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")
app.include_router(graph_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(similarity_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(correlations_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Check for frontend dist directory
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa_frontend(full_path: str):
        if full_path.startswith("api/") or full_path in ("docs", "redoc", "openapi.json"):
            return None
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"status": "healthy", "service": "ForenSight AI Backend", "documentation": "/docs"}
else:
    @app.api_route("/", methods=["GET", "HEAD"])
    def get_root():
        return {
            "status": "healthy",
            "service": "ForenSight AI Backend",
            "documentation": "/docs"
        }

