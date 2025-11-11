# ABS-CDSS - Lokale Installationsanleitung

## Übersicht

> **💡 Neu hier?** Schauen Sie sich die [Quick-Start Anleitung](QUICKSTART.md) für eine vereinfachte 7-Schritte-Installation an!

Diese Anleitung führt Sie Schritt für Schritt durch die lokale Installation und den Start der ABS-CDSS (Antibiotic Stewardship - Clinical Decision Support System) Anwendung.

Die Anwendung besteht aus:

- **Backend**: FastAPI-Server (Python) mit RAG-System und FHIR-Anbindung
- **Frontend**: React-Anwendung (Node.js) mit zwei Modi (Admin & Enduser)
- **Datenbank**: PostgreSQL zur Speicherung von Therapieempfehlungen

### Installationsablauf (vereinfacht)

```
1. Software installieren          2. Code herunterladen        3. .env konfigurieren
   (Git, Python, Node, PostgreSQL)    (git clone)                  (API-Keys eintragen)
            ↓                              ↓                              ↓
4. setup.bat ausführen            5. start_all_services.bat    6. Browser öffnen
   (installiert alles automatisch)    (startet Backend+Frontend)   (localhost:3000/4000)
```

---

## Voraussetzungen

### Systemanforderungen

- **Betriebssystem**: Windows 10/11, macOS oder Linux
- **RAM**: Mindestens 8 GB (16 GB empfohlen, besonders bei GPU-Nutzung)
- **Festplattenspeicher**: Mindestens 5 GB freier Speicherplatz

### Zu installierende Software

1. **Git** (für den Download des Codes)
2. **Python 3.11** oder höher
3. **Node.js** (empfohlen: Version 18 LTS oder höher)
4. **PostgreSQL** (Version 14 oder höher)
5. Optional: **NVIDIA CUDA Toolkit** (nur für GPU-Beschleunigung)

---

## Schritt 1: Erforderliche Software installieren

### 1.1 Git installieren

**Windows:**

1. Laden Sie Git von [https://git-scm.com/download/win](https://git-scm.com/download/win) herunter
2. Führen Sie das Installationsprogramm aus und folgen Sie den Anweisungen
3. Verwenden Sie die Standardeinstellungen

**macOS:**

```bash
# Mit Homebrew (falls installiert)
brew install git

# Oder laden Sie von https://git-scm.com/download/mac herunter
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install git
```

**Überprüfung:**

```bash
git --version
```

### 1.2 Python installieren

**Windows:**

1. Laden Sie Python 3.11 oder höher von [https://www.python.org/downloads/](https://www.python.org/downloads/) herunter
2. **WICHTIG**: Aktivieren Sie während der Installation die Option "Add Python to PATH"
3. Führen Sie das Installationsprogramm aus

**macOS:**

```bash
# Mit Homebrew
brew install python@3.11
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**Überprüfung:**

```bash
python --version
# oder
python3 --version
```

### 1.3 Node.js installieren

1. Laden Sie Node.js LTS von [https://nodejs.org/](https://nodejs.org/) herunter
2. Führen Sie das Installationsprogramm aus
3. Folgen Sie den Installationsanweisungen

**Überprüfung:**

```bash
node --version
npm --version
```

### 1.4 PostgreSQL installieren

**Windows:**

1. Laden Sie PostgreSQL von [https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/) herunter
2. Führen Sie das Installationsprogramm aus
3. **Merken Sie sich das Passwort**, das Sie für den Benutzer `postgres` festlegen!
4. Standardport: `5432` (beibehalten)

**macOS:**

```bash
# Mit Homebrew
brew install postgresql@14
brew services start postgresql@14
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Überprüfung:**

```bash
psql --version
```

### 1.5 PostgreSQL Datenbank einrichten

**Öffnen Sie die PostgreSQL-Kommandozeile:**

**Windows:**

- Suchen Sie im Startmenü nach "SQL Shell (psql)" und öffnen Sie es
- Drücken Sie Enter für Server, Datenbank, Port und Benutzername (Standardwerte)
- Geben Sie das Passwort ein, das Sie bei der Installation festgelegt haben

**macOS/Linux:**

```bash
sudo -u postgres psql
```

**Erstellen Sie die Datenbank:**

```sql
CREATE DATABASE abs_cdss;
\q
```

(Mit `\q` verlassen Sie die PostgreSQL-Konsole)

---

## Schritt 2: Code von GitHub herunterladen

1. **Öffnen Sie ein Terminal/Command Prompt:**

   - **Windows**: Drücken Sie `Windows + R`, tippen Sie `cmd` und drücken Sie Enter
   - **macOS**: Öffnen Sie Terminal (Spotlight: `Cmd + Space`, dann "Terminal")
   - **Linux**: Öffnen Sie Ihr bevorzugtes Terminal

2. **Navigieren Sie zu dem Ordner, in dem Sie das Projekt speichern möchten:**

```bash
cd Documents
# oder ein anderer Ordner Ihrer Wahl
```

3. **Klonen Sie das Repository:**

```bash
git clone https://github.com/IHR_GITHUB_BENUTZERNAME/ABS-CDSS.git
cd ABS-CDSS/Prototyp
```

---

## Schritt 3: Umgebungsvariablen konfigurieren

**Erstellen Sie eine `.env` Datei im `backend`-Ordner:**

1. **Navigieren Sie zum Backend-Ordner:**

```bash
cd backend
```

2. **Erstellen oder bearbeiten Sie die `.env` Datei:**

Erstellen Sie eine Datei namens `.env` im `backend`-Ordner mit folgendem Inhalt:

```env
# Environment Configuration
ENVIRONMENT=development

# API Configuration
API_HOST=127.0.0.1
API_PORT=8000

# RAG Configuration
ENABLE_RAG=true
EMBEDDING_MODEL=NeuML/pubmedbert-base-embeddings
CHUNK_SIZE=8000
CHUNK_OVERLAP=500
DEFAULT_TOP_K=5

# Storage Paths
DATA_DIR=data
EMBEDDINGS_DIR=data/embeddings
GUIDELINES_DIR=data/guidelines

# FAISS Configuration
FAISS_INDEX_TYPE=IndexFlatIP

# Logging
LOG_LEVEL=INFO

# Novita AI LLM Configuration
NOVITA_API_KEY=IHR_NOVITA_API_KEY_HIER
NOVITA_API_BASE_URL=https://api.novita.ai/openai
NOVITA_MODEL=openai/gpt-oss-120b
NOVITA_MAX_TOKENS=32768
NOVITA_TEMPERATURE=0.6

# Novita AI Embedding Configuration
NOVITA_EMBEDDING_URL=https://api.novita.ai/openai/v1/embeddings
NOVITA_EMBEDDING_MODEL=qwen/qwen3-embedding-8b
USE_ONLINE_EMBEDDINGS=false

# Rate Limiting Configuration
EMBEDDING_REQUESTS_PER_MINUTE=45
EMBEDDING_MAX_RETRIES=3
EMBEDDING_RETRY_DELAY=2

# Database Configuration
DATABASE_URL=postgresql://postgres:IHR_POSTGRES_PASSWORT@localhost:5432/abs_cdss
```

**WICHTIG - Ersetzen Sie folgende Werte:**

- `IHR_NOVITA_API_KEY_HIER`: Ihr Novita AI API-Schlüssel (erhalten Sie von [https://novita.ai](https://novita.ai))
- `IHR_POSTGRES_PASSWORT`: Das Passwort, das Sie bei der PostgreSQL-Installation festgelegt haben

**Gehen Sie zurück zum Hauptverzeichnis:**

```bash
cd ..
```

(Sie sollten jetzt im `Prototyp`-Ordner sein)

---

## Schritt 4: Automatische Installation

### Option A: Automatisches Setup-Script (EMPFOHLEN)

**Das Setup-Script installiert automatisch alle Abhängigkeiten!**

**Windows:**

```bash
setup.bat
```

**macOS/Linux:**

```bash
chmod +x setup.sh
./setup.sh
```

Das Script wird:

- ✅ Python und Node.js Version überprüfen
- ✅ Python Virtual Environment erstellen
- ✅ Alle Backend-Abhängigkeiten installieren (mit oder ohne GPU)
- ✅ Alle Frontend-Abhängigkeiten installieren
- ✅ Datenbankverbindung testen (optional)
- ✅ Alle benötigten Verzeichnisse erstellen

**Nach Abschluss des Scripts können Sie direkt mit [Schritt 5: Anwendung starten](#schritt-5-anwendung-starten) fortfahren!**

---

### Option B: Manuelle Installation (alle Plattformen)

Falls Sie das automatische Script nicht verwenden möchten:

#### 4.1 Python Virtual Environment erstellen

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

Nach der Aktivierung sollte `(venv)` am Anfang Ihrer Kommandozeile erscheinen.

#### 4.2 Backend-Abhängigkeiten installieren

**Variante A: Ohne GPU-Unterstützung (Standard):**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Variante B: Mit GPU-Unterstützung (NVIDIA CUDA erforderlich):**

```bash
pip install --upgrade pip
cd backend
pip install -r requirements_gpu.txt
cd ..

# Für NVIDIA GPU:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Hinweis zur GPU-Installation:**

- GPU-Beschleunigung ist optional und bietet schnellere Verarbeitung
- Erfordert eine NVIDIA-Grafikkarte mit CUDA-Unterstützung
- CUDA Toolkit muss separat installiert werden: [https://developer.nvidia.com/cuda-downloads](https://developer.nvidia.com/cuda-downloads)

#### 4.3 Frontend-Abhängigkeiten installieren

```bash
cd frontend
npm install
cd ..
```

Dieser Vorgang kann einige Minuten dauern.

#### 4.4 Datenbanktabellen erstellen

## Die Datenbanktabellen werden automatisch beim ersten Start des Backends erstellt.

## Schritt 5: Anwendung starten

### 5.1 Alle Services auf einmal starten (Windows)

**Nachdem Sie `setup.bat` ausgeführt haben, können Sie einfach starten:**

```bash
start_all_services.bat
```

Dieses Script öffnet automatisch drei separate Fenster für:

- ✅ Backend API-Server (Port 8000)
- ✅ Admin-Frontend (Port 3000)
- ✅ Endbenutzer-Frontend (Port 4000)

**Die Anwendung ist dann verfügbar unter:**

- Backend API: `http://localhost:8000`
- Admin-Frontend: `http://localhost:3000`
- Endbenutzer-Frontend: `http://localhost:4000`
- API-Dokumentation: `http://localhost:8000/docs`

**Das war's! Sie können direkt mit [Schritt 6: Anwendung verwenden](#schritt-6-anwendung-verwenden) fortfahren.**

---

### 5.2 Services einzeln starten (Alternative)

Falls Sie die Services lieber einzeln starten möchten:

#### Backend starten

**Windows:**

```bash
start_backend_venv.bat
```

**Oder manuell:**

```bash
cd backend
venv\Scripts\activate
python main.py
```

**macOS/Linux:**

```bash
cd backend
source venv/bin/activate
python main.py
```

Das Backend sollte jetzt unter `http://127.0.0.1:8000` laufen.

**Erfolgsmeldung:**

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

#### Frontend starten

**Windows - Admin-Frontend:**

```bash
start_frontend.bat
```

**Windows - Endbenutzer-Frontend:**

```bash
start_enduser_frontend.bat
```

**Oder manuell (alle Plattformen):**

```bash
cd frontend

# Admin-Frontend:
npm start

# Endbenutzer-Frontend:
npm run start:enduser
```

Das Frontend öffnet sich automatisch im Browser unter:

- **Admin-Modus**: `http://localhost:3000`
- **Endbenutzer-Modus**: `http://localhost:4000`

---

```bash
start_all_services.bat
```

Dieses Script startet:

- Backend
- Admin-Frontend
- Endbenutzer-Frontend

---

## Schritt 6: Anwendung verwenden

### Erste Schritte

1. **Öffnen Sie Ihren Browser** und navigieren Sie zu:

   - Admin-Interface: `http://localhost:3000`
   - Endbenutzer-Interface: `http://localhost:4000`

2. **API-Dokumentation** (Swagger UI):

   - Öffnen Sie `http://127.0.0.1:8000/docs` für die interaktive API-Dokumentation

3. **Testen Sie die Verbindung**:
   - Die Anwendung sollte automatisch eine Verbindung zum FHIR-Server herstellen
   - Die Datenbankverbindung wird beim ersten API-Aufruf initialisiert

---

## Quick-Start Zusammenfassung (Windows)

Für die schnellste Installation:

1. **Software installieren**: Git, Python 3.11+, Node.js 18+, PostgreSQL 14+
2. **Datenbank erstellen**: `CREATE DATABASE abs_cdss;` in PostgreSQL
3. **Code herunterladen**: `git clone ... && cd ABS-CDSS/Prototyp`
4. **`.env` konfigurieren**: Datei im `backend`-Ordner mit API-Keys erstellen
5. **Setup ausführen**: `setup.bat` (installiert alle Abhängigkeiten automatisch)
6. **Starten**: `start_all_services.bat`
7. **Fertig!** Browser öffnet sich unter `http://localhost:3000` oder `http://localhost:4000`

---

## Fehlerbehebung

### Problem: "Python not found" oder "python: command not found"

**Lösung:**

- Stellen Sie sicher, dass Python korrekt installiert ist
- Windows: Überprüfen Sie, ob Python zum PATH hinzugefügt wurde
- Versuchen Sie `python3` statt `python`

### Problem: "pip: command not found"

**Lösung:**

```bash
python -m pip install --upgrade pip
# oder
python3 -m pip install --upgrade pip
```

### Problem: PostgreSQL-Verbindungsfehler

**Lösung:**

1. Überprüfen Sie, ob PostgreSQL läuft:

   - **Windows**: Öffnen Sie "Dienste" und suchen Sie nach "postgresql"
   - **macOS/Linux**: `sudo systemctl status postgresql`

2. Überprüfen Sie die `DATABASE_URL` in der `.env` Datei:

   - Format: `postgresql://BENUTZER:PASSWORT@HOST:PORT/DATENBANKNAME`
   - Standardmäßig: `postgresql://postgres:IHR_PASSWORT@localhost:5432/abs_cdss`

3. Stellen Sie sicher, dass die Datenbank `abs_cdss` existiert:

```bash
# PostgreSQL-Konsole öffnen
psql -U postgres
# Datenbanken auflisten
\l
# Falls nicht vorhanden, erstellen:
CREATE DATABASE abs_cdss;
```

### Problem: Port bereits belegt

**Symptom:** `Address already in use` oder ähnlicher Fehler

**Lösung:**

- **Backend (Port 8000)**: Ändern Sie `API_PORT` in der `.env` Datei
- **Frontend (Port 3000/4000)**: Ändern Sie den Port in der `package.json` oder beim Start:

  ```bash
  # Windows
  set PORT=3001 && npm start

  # macOS/Linux
  PORT=3001 npm start
  ```

### Problem: Module nicht gefunden

**Lösung:**

```bash
# Aktivieren Sie das Virtual Environment erneut
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Installieren Sie die Abhängigkeiten erneut
pip install -r requirements.txt
```

### Problem: Frontend startet nicht

**Lösung:**

```bash
# Löschen Sie node_modules und installieren Sie neu
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

### Problem: CORS-Fehler im Browser

**Lösung:**

- Stellen Sie sicher, dass das Backend läuft (`http://127.0.0.1:8000`)
- Überprüfen Sie die `proxy` Einstellung in `frontend/package.json` (sollte `"http://localhost:8000"` sein)
- Starten Sie beide Services neu

### Problem: Novita API-Fehler

**Lösung:**

- Überprüfen Sie Ihren `NOVITA_API_KEY` in der `.env` Datei
- Stellen Sie sicher, dass Sie über ausreichend API-Credits verfügen
- Testen Sie die API-Verbindung: `http://127.0.0.1:8000/docs` → `/test` Endpoint

---

## Erweiterte Konfiguration

### FHIR-Server konfigurieren

Die Standardkonfiguration verwendet einen externen FHIR-Server. Wenn Sie einen eigenen FHIR-Server verwenden möchten, können Sie die URL im Code anpassen:

Datei: `backend/fhir_service.py` - Suchen Sie nach der `FHIR_BASE_URL` Variable.

### RAG-System konfigurieren

Die RAG (Retrieval-Augmented Generation) Konfiguration finden Sie in der `.env` Datei:

- `ENABLE_RAG`: RAG-System aktivieren/deaktivieren
- `EMBEDDING_MODEL`: Verwendetes Embedding-Modell
- `CHUNK_SIZE`: Größe der Textchunks für die Verarbeitung
- `DEFAULT_TOP_K`: Anzahl der relevantesten Dokumente, die abgerufen werden

### Offline-Modus

Das System kann auch offline arbeiten, indem lokale Embeddings verwendet werden:

```env
USE_ONLINE_EMBEDDINGS=false
```

In diesem Modus werden Embeddings lokal berechnet, was keine Internet-Verbindung erfordert, aber langsamer sein kann.

---

## Produktions-Deployment

Für ein Produktions-Deployment sollten Sie:

1. **Sichere Umgebungsvariablen** verwenden
2. **HTTPS** aktivieren
3. **Reverse Proxy** (z.B. Nginx) einrichten
4. **PostgreSQL** mit einem sicheren Passwort konfigurieren
5. **Firewall-Regeln** einrichten
6. **Backup-Strategie** für die Datenbank implementieren

Siehe `koyeb.toml` und `Dockerfile` für Beispiele eines Container-basierten Deployments.

---

## Projekt-Struktur

```
Prototyp/
├── backend/                    # Python FastAPI Backend
│   ├── main.py                # Haupt-API-Server
│   ├── database.py            # Datenbank-Modelle und Verbindung
│   ├── rag_service_advanced.py # RAG-System Implementation
│   ├── fhir_service.py        # FHIR-Server Integration
│   ├── therapy_llm_service.py # LLM-Service für Therapieempfehlungen
│   ├── requirements.txt       # Python-Abhängigkeiten (ohne GPU)
│   ├── requirements_gpu.txt   # Python-Abhängigkeiten (mit GPU)
│   └── data/                  # Daten-Verzeichnis
│       ├── guidelines/        # Medizinische Leitlinien
│       ├── embeddings/        # Vorberechnete Embeddings
│       └── additional_info/   # Zusätzliche Informationen
│
├── frontend/                  # React Frontend
│   ├── src/                   # Quellcode
│   │   ├── App.js            # Admin-App
│   │   ├── EnduserApp.js     # Endbenutzer-App
│   │   ├── components/       # React-Komponenten
│   │   ├── pages/            # Seiten-Komponenten
│   │   └── services/         # API-Services
│   ├── package.json          # Node.js-Abhängigkeiten
│   └── public/               # Statische Dateien
│
├── README.md                  # Diese Anleitung
├── requirements.txt          # Backend-Abhängigkeiten (Root)
├── Dockerfile               # Docker-Container-Definition
└── *.bat                    # Windows-Startscripts
```

---

## Nützliche Befehle

### Backend

```bash
# Virtual Environment aktivieren (Windows)
venv\Scripts\activate

# Virtual Environment aktivieren (macOS/Linux)
source venv/bin/activate

# Backend starten
python main.py

# Abhängigkeiten aktualisieren
pip install -r requirements.txt --upgrade

# Virtual Environment deaktivieren
deactivate
```

### Frontend

```bash
# Admin-Frontend starten
npm start

# Endbenutzer-Frontend starten
npm run start:enduser

# Produktions-Build erstellen
npm run build

# Abhängigkeiten aktualisieren
npm update
```

### Datenbank

```bash
# PostgreSQL-Konsole öffnen
psql -U postgres -d abs_cdss

# Datenbank-Backup erstellen
pg_dump -U postgres abs_cdss > backup.sql

# Backup wiederherstellen
psql -U postgres abs_cdss < backup.sql
```

---

## Weitere Hilfe und Support

### Dokumentation

- **FastAPI Docs**: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
- **React Docs**: [https://react.dev/](https://react.dev/)
- **PostgreSQL Docs**: [https://www.postgresql.org/docs/](https://www.postgresql.org/docs/)

### API-Dokumentation

Nach dem Start des Backends ist die interaktive API-Dokumentation verfügbar unter:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

### Logs überprüfen

Logs werden in der Konsole ausgegeben. Bei Problemen:

1. Überprüfen Sie die Backend-Konsole auf Fehlermeldungen
2. Überprüfen Sie die Browser-Konsole (F12) auf Frontend-Fehler
3. Setzen Sie `LOG_LEVEL=DEBUG` in der `.env` für detailliertere Logs

---

## Installierte Dateien Übersicht

Nach der Installation mit `setup.bat` / `setup.sh`:

```
Prototyp/
├── setup.bat                  # Windows Setup-Script (NEU)
├── setup.sh                   # macOS/Linux Setup-Script (NEU)
├── start_all_services.bat     # Startet alle Services (Windows)
├── start_backend_venv.bat     # Startet nur Backend (Windows)
├── start_frontend.bat         # Startet Admin-Frontend (Windows)
├── start_enduser_frontend.bat # Startet Enduser-Frontend (Windows)
├── README.md                  # Diese Anleitung
├── QUICKSTART.md              # Vereinfachte Schnellanleitung (NEU)
├── requirements.txt           # Backend-Dependencies (ohne GPU)
├── Dockerfile                 # Docker-Container Definition
│
├── venv/                      # Python Virtual Environment (erstellt durch setup)
│   ├── Scripts/              # (Windows)
│   └── bin/                  # (macOS/Linux)
│
├── backend/
│   ├── .env                  # Umgebungsvariablen (WICHTIG - manuell erstellen)
│   ├── main.py               # Haupt-API-Server
│   ├── database.py           # Datenbank-Konfiguration
│   ├── rag_service_advanced.py
│   ├── fhir_service.py
│   ├── therapy_llm_service.py
│   ├── requirements.txt      # Backend-Dependencies
│   ├── requirements_gpu.txt  # Backend-Dependencies mit GPU
│   └── data/                 # Daten-Verzeichnis (erstellt durch setup)
│       ├── embeddings/
│       ├── guidelines/
│       ├── additional_info/
│       └── dose_info/
│
└── frontend/
    ├── package.json          # Frontend-Dependencies
    ├── node_modules/         # NPM-Pakete (erstellt durch setup)
    ├── public/
    │   └── index.html
    └── src/
        ├── App.js            # Admin-App
        ├── EnduserApp.js     # Enduser-App
        ├── components/
        ├── pages/
        └── services/
```

---

## Lizenz und Kontakt

Dieses Projekt ist ein medizinisches Entscheidungsunterstützungssystem. Bitte verwenden Sie es verantwortungsvoll und in Übereinstimmung mit den geltenden medizinischen Richtlinien.

**Viel Erfolg bei der Installation!** 🚀

Bei Fragen oder Problemen erstellen Sie bitte ein Issue im GitHub-Repository.
