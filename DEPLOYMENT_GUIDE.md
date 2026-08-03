# 🚀 ForenSight AI — Production Deployment Blueprint

This guide provides step-by-step instructions to deploy the complete **ForenSight AI Digital Forensics & AI Copilot Platform** in production.

---

## 📋 Recommended Production System Requirements

| Component | Minimum Spec | Recommended Enterprise Spec |
| :--- | :--- | :--- |
| **CPU** | 4 vCPU Cores | 8+ vCPU Cores |
| **RAM** | 8 GB RAM | 16 GB - 32 GB RAM |
| **Disk Storage** | 50 GB SSD | 500 GB+ NVMe SSD |
| **OS** | Ubuntu 22.04 LTS / Debian 12 / RHEL 9 | Ubuntu 22.04 LTS / Debian 12 |

---

## ⚡ Option 1: Docker Compose Deployment (Recommended)

ForenSight includes a production-ready multi-container `docker-compose.yml` that orchestrates all 7 services automatically:

### Services Orchestrated:
- 🌐 **Web Frontend**: Nginx serving optimized React SPA (`Port 80`)
- ⚡ **Backend API**: FastAPI ASGI Server with 2 worker processes (`Port 8000`)
- 🍃 **MongoDB 6.0**: Evidence metadata & audit logs (`Port 27017`)
- 🕸️ **Neo4j 5.12**: Knowledge Graph engine with APOC (`Port 7474 / 7687`)
- 🎯 **Qdrant Vector DB**: AI similarity search (`Port 6333`)
- 🔴 **Redis 7.0**: Cache & Pub/Sub event bus (`Port 6379`)
- 🪣 **MinIO**: S3-compatible evidence object storage (`Port 9000 / 9001`)

---

### 🚀 One-Command Deployment Steps

#### Step 1: Clone Repository & Navigate to Directory
```bash
git clone https://github.com/your-org/ForenSight.git
cd ForenSight
```

#### Step 2: Configure Production Environment Variables
Create your production `.env` file from the template:

```bash
cp backend/.env.example backend/.env
```

Update critical secrets in `backend/.env`:
```ini
JWT_SECRET_KEY=change-this-to-a-secure-random-secret-key-in-production
ENVIRONMENT=production
ALLOWED_ORIGINS=https://forensight.yourdomain.com
MONGODB_URL=mongodb://mongodb:27017
NEO4J_URL=bolt://neo4j:7687
NEO4J_AUTH=neo4j/your_secure_neo4j_password
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=minio:9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your_secure_minio_password
```

#### Step 3: Build & Launch Containers
```bash
docker compose up -d --build
```

#### Step 4: Verify Service Health
```bash
docker compose ps
```

All 7 containers should report `(healthy)` status.

- **Web Dashboard**: `http://<YOUR-SERVER-IP>`
- **API Documentation**: `http://<YOUR-SERVER-IP>:8000/docs`
- **MinIO S3 Console**: `http://<YOUR-SERVER-IP>:9001`
- **Neo4j Graph Browser**: `http://<YOUR-SERVER-IP>:7474`

---

## 🔒 Step 5: SSL / TLS Certificate Setup with Nginx & Let's Encrypt

To secure traffic with HTTPS:

```bash
sudo apt update && sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d forensight.yourdomain.com
```

---

## 🛠️ Essential Production Commands

| Action | Command |
| :--- | :--- |
| **View Live API Logs** | `docker compose logs -f api` |
| **View Live Worker Logs** | `docker compose logs -f web` |
| **Restart Backend Service** | `docker compose restart api` |
| **Stop All Containers** | `docker compose down` |
| **Check System Resource Usage** | `docker stats` |
