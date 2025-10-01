# Koyeb Deployment Strategie für ABS-CDSS

## Architektur-Analyse

Ihre aktuelle Anwendung besteht aus:

- **Backend (FastAPI)**: Port 8000 - API Server
- **Admin Frontend (React)**: Port 3000 - Admin-Interface für Leitlinien-Upload
- **Enduser Frontend (React)**: Port 4000 - Benutzeroberfläche für Therapie-Empfehlungen

## 🎯 Finale Empfehlung: GitHub Integration mit Docker

**Warum GitHub + Docker die beste Lösung für Sie ist:**

✅ **Behalten Sie Ihren bewährten GitHub-Workflow bei**  
✅ **Ein Service = kostenlos auf Koyeb**  
✅ **Automatisches Deployment bei Push zu main**  
✅ **Alle drei Komponenten in einer Anwendung**  
✅ **Optimale Resource-Nutzung der kostenlosen Tier**

### 🏗️ Implementierte Lösung:

```
┌─ Koyeb Service (Port 8000) ────────────────────┐
│                                                │
│  ┌─ Backend (FastAPI) ─────────────────────┐   │
│  │ ├─ /api/* → API Endpoints               │   │
│  │ ├─ /docs → Swagger Documentation        │   │
│  │ └─ /health → Health Check               │   │
│  └─────────────────────────────────────────┘   │
│                                                │
│  ┌─ Admin Frontend ───────────────────────┐    │
│  │ └─ /admin/* → Leitlinien-Management    │    │
│  └─────────────────────────────────────────┘    │
│                                                │
│  ┌─ Enduser Frontend ─────────────────────┐    │
│  │ └─ /* → Therapie-Empfehlungen          │    │
│  └─────────────────────────────────────────┘    │
└────────────────────────────────────────────────┘
```

### 📁 Erstellte Dateien:

1. **`Dockerfile`** - Multi-stage Build für optimale Performance
2. **`koyeb.toml`** - Koyeb-Konfiguration mit allen Settings
3. **`backend/requirements-prod.txt`** - Cloud-optimierte Dependencies
4. **`.dockerignore`** - Minimale Container-Größe
5. **`prepare_deployment.py`** - Automatisierte Vorbereitung
6. **Erweiterte `main.py`** - Frontend-Routing integriert

### 🚀 Deployment-Process:

1. **Lokale Vorbereitung:**

   ```bash
   python prepare_deployment.py
   ```

2. **Koyeb Setup:**

   - Repository verbinden
   - Environment Variables konfigurieren
   - Auto-Deploy aktivieren

3. **Git Push:**

   ```bash
   git add .
   git commit -m "Ready for Koyeb deployment"
   git push origin main
   ```

4. **Automatisches Deployment** durch Koyeb

### 💰 Kostenoptimierung erreicht:

- **Ein Service** statt drei = **0€ monatlich**
- **CPU-optimierte Builds** (keine GPU-Dependencies)
- **Minimaler Memory-Footprint** (<512MB)
- **Effiziente Online-Embeddings** statt lokaler Modelle

## 🏗️ Multi-Service Koyeb Setup

### Option 1: Mono-Service Approach (Empfohlen für kostenlose Tier)

**Ein Service mit allem zusammen:**

```
Backend (FastAPI) + Zwei Frontend Builds + Reverse Proxy
└── Port 8000 (extern zugänglich)
    ├── /api/* → FastAPI Backend
    ├── /admin/* → Admin Frontend (statische Dateien)
    └── /* → Enduser Frontend (statische Dateien)
```

**Vorteile:**

- ✅ Nur eine Koyeb-Instanz (kostenlos)
- ✅ Keine CORS-Probleme
- ✅ Einfaches Routing
- ✅ Alle Services immer verfügbar

### Option 2: Multi-Service Approach (kostenpflichtig)

**Drei separate Services:**

- Service 1: Backend (Port 8000)
- Service 2: Admin Frontend (Port 3000)
- Service 3: Enduser Frontend (Port 4000)

**Nachteile:**

- ❌ 3× Kosten
- ❌ CORS-Konfiguration nötig
- ❌ Service Discovery zwischen Services

## 🚀 Empfohlene Implementierung: Mono-Service

### Dockerfile-Struktur:

```dockerfile
# Multi-stage build
FROM node:18-alpine as frontend-builder

# Build Admin Frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build
RUN mv build admin-build

# Build Enduser Frontend
RUN npm run build:enduser
RUN mv build enduser-build

# Python Backend Stage
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy built frontends
COPY --from=frontend-builder /app/frontend/admin-build ./static/admin
COPY --from=frontend-builder /app/frontend/enduser-build ./static/enduser

# Create data directories
RUN mkdir -p data/embeddings data/guidelines

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### FastAPI Routing-Anpassungen:

```python
# In main.py erweitern:
from fastapi.staticfiles import StaticFiles

# Serve static frontends
app.mount("/admin", StaticFiles(directory="static/admin", html=True), name="admin")
app.mount("/static", StaticFiles(directory="static/enduser/static"), name="static")

# Enduser frontend als default (root)
@app.get("/{full_path:path}")
async def serve_enduser_frontend(full_path: str):
    # API routes haben Priorität
    if full_path.startswith("api/"):
        raise HTTPException(404)

    # Admin route
    if full_path.startswith("admin"):
        return FileResponse("static/admin/index.html")

    # Default: Enduser frontend
    return FileResponse("static/enduser/index.html")
```

## 🔧 Technische Umsetzung

### 1. Repository-Struktur für Koyeb:

```
├── Dockerfile                 # Multi-stage build
├── .dockerignore             # Optimierte Builds
├── koyeb.toml               # Koyeb-Konfiguration
├── backend/
│   ├── requirements-prod.txt # Nur Production-Dependencies
│   ├── main.py              # Erweitert um Static-Serving
│   └── ...
└── frontend/
    ├── package.json         # Scripts für beide Builds
    └── ...
```

### 2. Production Requirements (backend/requirements-prod.txt):

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
python-dotenv==1.0.0
aiofiles==23.2.1
requests>=2.31.0
fhir.resources>=7.0.0
faiss-cpu==1.7.4
numpy>=1.24.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0  # Für PostgreSQL
```

### 3. Koyeb-Konfiguration (koyeb.toml):

```toml
[app]
name = "abs-cdss"

[app.env]
USE_ONLINE_EMBEDDINGS = "true"
ENVIRONMENT = "production"
API_HOST = "0.0.0.0"
API_PORT = "8000"

[build]
type = "docker"
dockerfile = "Dockerfile"

[deploy]
instance_type = "nano"  # Kostenlose Tier
regions = ["fra"]       # Frankfurt
autoscaling = { min = 1, max = 1 }

[deploy.ports]
port = 8000
protocol = "http"
public = true

[deploy.health_check]
path = "/health"
```

### 4. Environment Variables in Koyeb:

**Secrets (in Koyeb UI konfigurieren):**

- `NOVITA_API_KEY`: Ihr API-Key
- `DATABASE_URL`: PostgreSQL Connection String

**Public Variables:**

- `USE_ONLINE_EMBEDDINGS=true`
- `ENVIRONMENT=production`
- `EMBEDDING_REQUESTS_PER_MINUTE=45`

## 📊 Resource-Optimierungen für kostenlose Tier

### Memory-Optimierungen:

```dockerfile
# Kleinere Base Images
FROM python:3.11-slim  # statt python:3.11

# Multi-stage builds
FROM node:18-alpine as builder  # Build-Stage
FROM python:3.11-slim as runtime  # Runtime-Stage

# Nur Production-Dependencies
RUN pip install --no-cache-dir -r requirements-prod.txt

# Cleanup nach Installation
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
```

### Startup-Optimierungen:

```python
# Lazy Loading von schweren Services
@app.on_event("startup")
async def startup_event():
    # RAG Service nur bei Bedarf initialisieren
    global rag_service
    rag_service = None

def get_rag_service():
    global rag_service
    if rag_service is None:
        rag_service = AdvancedRAGService()
    return rag_service
```

## 🔄 Deployment-Workflow

### 1. GitHub Repository Setup:

```bash
# Branching-Strategie
main              # Production (auto-deploy zu Koyeb)
├── develop       # Development
├── feature/*     # Feature-Branches
```

### 2. Koyeb Auto-Deploy:

- **Trigger**: Push zu `main` Branch
- **Build**: Docker-basiert
- **Deploy**: Automatisch mit Health-Checks

### 3. Database Migration:

```python
# In main.py startup
@app.on_event("startup")
async def create_db_tables():
    # Automatische Tabellen-Erstellung bei Start
    create_tables()
```

## 💰 Kostenlose Tier Limits

**Koyeb Free Tier:**

- ✅ 1 Service kostenlos
- ✅ 512MB RAM, 1 vCPU
- ✅ 100GB Traffic/Monat
- ✅ Automatisches SSL
- ✅ Custom Domain

**Mit Mono-Service Approach:**

- ✅ Backend + 2 Frontends in einem Service
- ✅ Bleibt unter Resource-Limits
- ✅ Optimale Performance durch lokales Serving

## 🎯 Nächste Schritte

1. **✅ Dockerfile erstellen** (Multi-stage für Frontend + Backend)
2. **✅ FastAPI für Static-Serving erweitern**
3. **✅ Production Requirements definieren**
4. **✅ Koyeb-Konfiguration** (koyeb.toml)
5. **✅ Environment Variables** in Koyeb UI
6. **✅ Database Setup** (PostgreSQL)
7. **✅ GitHub Auto-Deploy** aktivieren

Diese Strategie nutzt die kostenlosen Koyeb-Tier optimal aus und Sie können bei GitHub bleiben! 🚀
