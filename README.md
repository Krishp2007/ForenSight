# ForenSight AI: Incident Response & Threat Hunting Copilot

ForenSight AI is an intelligent forensic analysis and threat hunting platform designed to ingest raw system logs (CSV/JSON), extract key cybersecurity entities, build transaction graphs (Neo4j), isolate abnormal patterns using unsupervised machine learning models, and compile professional incident summaries using a Gemini/Ollama generative AI Copilot.

---

## 🏗️ Architecture Overview

ForenSight AI separates its functionality into specialized backend service modules:
* **Ingestion Layer**: Ingests raw evidence files, performs SHA-256 duplicate verification, maps metadata, and uploads to MinIO S3 bucket storage.
* **Processing & Normalization Pipeline**: Filters execution noise, builds chronological timelines, and translates system events into readable English logs.
* **Graph Synthesis Engine**: Populates a Neo4j instance to link processes, files, registry keys, network endpoints, and users, mapping execution paths.
* **Unsupervised Outlier Analytics**: Passes numeric feature vectors (time, frequency, severity) into Isolation Forest, LOF, One-Class SVM, or HBOS to identify anomalies.
* **Copilot & Semantic Search Engine**: Index logs into a FAISS vector store for semantic searches, routing analytical questions to Gemini or Ollama models.
* **Report compiler**: Generates clean HTML/PDF forensics reports complete with MITRE ATT&CK mappings, anomaly tables, and AI-powered executive summaries.

---

## 🛠️ Quick Start Guide

### 1. Prerequisites
Ensure you have Docker, Docker Compose, and Python 3.10+ installed on your system.

### 2. Launch Local Infrastructures
Clone the repository and start the Docker containers:

```bash
docker-compose up -d
```
This spins up:
* **MongoDB**: Timeline and case metadata storage (port `27017`)
* **Neo4j**: Attack graph storage (port `7474` HTTP, `7687` Bolt)
* **Redis**: Celery message broker (port `6379`)
* **MinIO**: S3 Object storage (port `9000` API, `9001` Console)

### 3. Setup Virtual Environment
Run the setup in the backend folder:

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run Backend Tests
You can run automated E2E integration verification tests or individual modular scripts:

```bash
# E2E integration runner:
.\.venv\Scripts\python.exe test_full_integration.py

# Offline modular demo:
.\.venv\Scripts\python.exe -X utf8 test_modular_demo.py
```
