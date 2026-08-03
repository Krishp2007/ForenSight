# ForenSight AI Backend Services

ForenSight AI is a next-generation forensic investigation platform incorporating machine learning anomaly detection, graph analytics, semantic log search, and generative AI Copilot helpers to accelerate cybersecurity incident response.

This directory houses the ForenSight AI backend services, modularized to optimize extensibility, separation of concerns, and clean testing boundaries.

---

## 📁 Repository Structure

```
backend/
├── app/
│   ├── api/                   # Router endpoints (Similarity, Copilot, Case, Auth)
│   ├── auth/                  # RBAC authorization & JWT sessions
│   ├── db/                    # Connections/Clients for MongoDB, Neo4j, Redis, MinIO
│   ├── knowledge/             # Mappers to security frameworks (e.g. MITRE ATT&CK)
│   │   └── mitre_mapper.py    # Matches cmd execution scripts to ATT&CK techniques
│   ├── pipeline/              # Ingestion queues & events broadcasting
│   │   └── event_stream.py    # Publish-subscribe log streamer
│   ├── repositories/          # Database query wrappers
│   │   ├── case_repository.py
│   │   ├── event_repository.py
│   │   ├── evidence_repository.py
│   │   └── report_repository.py # Stores compiled HTML case outputs
│   ├── schemas/               # Pydantic serialization definitions
│   ├── services/
│   │   ├── ai/                # Vector extraction & FAISS semantic store wrappers
│   │   ├── context/           # Assembles structured contexts for AI prompting
│   │   │   ├── anomaly_context.py
│   │   │   ├── graph_context.py
│   │   │   ├── report_context.py
│   │   │   └── timeline_context.py
│   │   ├── copilot/           # LLM Providers (Gemini, Ollama, dynamic routing)
│   │   ├── graph/             # Neo4j building, pathfinding registry, and visualizers
│   │   ├── ingestion/         # Evidence upload pipeline
│   │   │   └── upload_service.py # Streamlines MinIO upload & metadata checks
│   │   ├── intelligence/      # Unsupervised outlier analysis & word representations
│   │   │   ├── anomaly/       # Isolation Forest, LOF, One-Class SVM, HBOS, & Evaluator
│   │   │   ├── embeddings/    # MiniLM, BGE, E5 wrappers, & Pairwise Evaluator
│   │   │   └── similarity_service.py # Computes case centroid & case-to-case cosine similarity
│   │   └── processing/        # Forensic timeline cleaning & feature metrics
│   │       ├── feature_builder.py # Extracts matrix arrays for PyOD model fitting
│   │       ├── rule_filter.py    # Noise filter lists to avoid alert fatigue
│   │       └── timeline_builder.py
│   ├── utils/                 # General helpers (hashing, constants, exceptions)
│   └── worker/                # Celery background workers (Celery app, async upload task)
│       ├── parser_tasks.py
│       └── upload_tasks.py    # Copying files locally to MinIO asynchronously
```

---

## ⚙️ Key Backend Technologies

* **Core Framework**: FastAPI (Uvicorn server)
* **Metadata Database**: MongoDB (Motor async driver)
* **Graph DB**: Neo4j (Cypher querying and analytics)
* **Message Broker & Task Queue**: Celery (Redis broker)
* **Object Store**: Cloudflare R2 / MinIO (S3-compatible API)
* **Machine Learning**: Scikit-Learn / PyOD (Isolation Forest, LOF, One-Class SVM, HBOS)
* **Embeddings**: SentenceTransformers (MiniLM, BAAI/BGE, Intfloat/E5)
* **AI Copilot**: Google Gemini API / Local Ollama (fallback heuristic engine)
* **Security & Auth**: bcrypt password hashing, JWT access tokens, role-based access control (RBAC)

---

## 🚀 Running Verification Suites

All test files located at the root of `backend/` and inside the `tests/` directory are standalone verification pipelines and demonstration suites. The main application is completely self-contained and isolated within the `app/` folder.

To run the verification test suites, execute the following commands from the `backend` directory:

### 1. Offline Modular Showcase
Runs unsupervised anomaly model fitting, SentenceTransformers embeddings generation, pairwise cosine similarity metrics, ForensicFeatureBuilder, and MITRE mapping rules:
```bash
.\.venv\Scripts\python.exe -X utf8 showcase_modules.py
```

### 2. Case Similarity Integration Test
Verifies the `SimilarityService` calculation of case centroid overlap scoring and the `/api/v1/cases/{case_id}/similar-cases` API route mappings:
```bash
.\.venv\Scripts\python.exe -X utf8 tests/test_services/test_similarity.py
```

### 3. Synchronous Integration Test Suite
Verifies the FastAPI endpoints, database storage integrity, HTML/PDF reporting compliance, and database state cleanup:
```bash
.\.venv\Scripts\python.exe -X utf8 test_full_integration.py
```

### 4. Asynchronous Celery Queue Test Suite
Verifies Redis broker task routing, multi-process Celery worker scheduling, and polling client updates.
*(Note: Requires a running Celery worker instance: `celery -A backend.app.worker.celery_app worker --loglevel=info -P threads`)*
```bash
.\.venv\Scripts\python.exe -X utf8 test_async_pipeline.py
```
