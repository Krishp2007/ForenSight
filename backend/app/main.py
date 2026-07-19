import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing infrastructure database clients...")
    try:
        await connect_to_mongo()
        await connect_to_neo4j()
        await connect_to_redis()
        connect_to_minio()
        logger.info("All services successfully connected during application startup!")
    except Exception as e:
        logger.error(f"Startup infrastructure initialization failed: {e}")
        raise e
        
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
    lifespan=lifespan
)

# Set up CORS middleware rules
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include API routers
from backend.app.api.auth import router as auth_router
from backend.app.api.organizations import router as org_router
from backend.app.api.cases import router as cases_router
from backend.app.api.evidence import router as evidence_router
from backend.app.api.events import router as events_router
from backend.app.api.graph import router as graph_router
from backend.app.api.chat import router as chat_router
from backend.app.api.similarity import router as similarity_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(org_router, prefix="/api/v1")
app.include_router(cases_router, prefix="/api/v1")
app.include_router(evidence_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")
app.include_router(graph_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(similarity_router, prefix="/api/v1")

@app.get("/")
def get_root():
    return {
        "status": "healthy",
        "service": "ForenSight AI Backend",
        "documentation": "/docs"
    }
