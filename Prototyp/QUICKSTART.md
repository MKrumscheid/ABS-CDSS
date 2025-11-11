# 🚀 Quick-Start Guide - ABS-CDSS

**Schnellanleitung für die Installation in 7 einfachen Schritten**

---

## ✅ Checkliste: Was Sie brauchen

Vor dem Start bitte installieren:

- [ ] **Git** - [Download](https://git-scm.com/downloads)
- [ ] **Python 3.11+** - [Download](https://www.python.org/downloads/) ⚠️ "Add to PATH" aktivieren!
- [ ] **Node.js 18+** - [Download](https://nodejs.org/)
- [ ] **PostgreSQL 14+** - [Download](https://www.postgresql.org/download/)
- [ ] **Novita AI Account** - [Registrieren](https://novita.ai) (für API-Key)

---

## 📝 Schritt 1: PostgreSQL einrichten

1. Öffnen Sie **SQL Shell (psql)** (im Startmenü nach "psql" suchen)
2. Drücken Sie 4x Enter (für Standard-Einstellungen)
3. Geben Sie Ihr PostgreSQL-Passwort ein
4. Führen Sie aus:
   ```sql
   CREATE DATABASE abs_cdss;
   \q
   ```

**Merken Sie sich Ihr Passwort - Sie brauchen es später!**

---

## 📥 Schritt 2: Code herunterladen

1. Öffnen Sie **Command Prompt** (Windows + R → `cmd` → Enter)
2. Gehen Sie zu Ihrem gewünschten Ordner:
   ```bash
   cd Documents
   ```
3. Laden Sie den Code herunter:
   ```bash
   git clone https://github.com/IHR_GITHUB_BENUTZERNAME/ABS-CDSS.git
   cd ABS-CDSS\Prototyp
   ```

---

## 🔧 Schritt 3: Konfiguration erstellen

1. Öffnen Sie den `backend` Ordner
2. Erstellen Sie eine neue Datei namens `.env` (ja, nur `.env`, kein Name davor!)
3. Kopieren Sie folgenden Inhalt hinein:

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
NOVITA_API_KEY=HIER_IHR_NOVITA_API_KEY
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
DATABASE_URL=postgresql://postgres:HIER_IHR_POSTGRES_PASSWORT@localhost:5432/abs_cdss
```

4. **WICHTIG**: Ersetzen Sie:
   - `HIER_IHR_NOVITA_API_KEY` → Ihr Novita AI API-Key
   - `HIER_IHR_POSTGRES_PASSWORT` → Ihr PostgreSQL-Passwort aus Schritt 1

---

## ⚙️ Schritt 4: Automatische Installation

**Im Command Prompt (im `Prototyp` Ordner):**

```bash
setup.bat
```

Das Script fragt Sie:

- "GPU-Unterstützung installieren?" → **N** drücken (außer Sie haben eine NVIDIA GPU)
- "Datenbankverbindung testen?" → **J** drücken

**Das Script installiert jetzt alles automatisch - das dauert 5-10 Minuten!** ☕

---

## 🚀 Schritt 5: Anwendung starten

Nachdem das Setup fertig ist:

```bash
start_all_services.bat
```

**Das war's!** Drei Fenster öffnen sich automatisch für:

- Backend
- Admin-Frontend
- Endbenutzer-Frontend

---

## 🌐 Schritt 6: Im Browser öffnen

Nach ca. 30 Sekunden öffnen Sie Ihren Browser:

- **Admin-Interface**: [http://localhost:3000](http://localhost:3000)
- **Endbenutzer-Interface**: [http://localhost:4000](http://localhost:4000)
- **API-Dokumentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🎉 Schritt 7: Fertig!

Die Anwendung läuft jetzt!

**Zum Beenden:**

- Drücken Sie `Strg + C` in jedem Fenster
- Oder schließen Sie die Fenster

**Nächstes Mal starten:**

1. Gehen Sie zum `Prototyp` Ordner
2. Führen Sie `start_all_services.bat` aus

---

## ❗ Probleme?

### "Python not found"

- Python wurde nicht zum PATH hinzugefügt
- Deinstallieren & neu installieren mit "Add to PATH" ✅

### "pip: command not found"

```bash
python -m pip install --upgrade pip
```

### "Datenbankverbindung fehlgeschlagen"

- PostgreSQL läuft nicht → Im Startmenü nach "Services" suchen → "postgresql" starten
- Passwort falsch → `.env` Datei überprüfen

### Port bereits belegt

- Schließen Sie andere Anwendungen auf Port 3000, 4000 oder 8000
- Oder ändern Sie die Ports in der Konfiguration

### Frontend startet nicht

```bash
cd frontend
rmdir /s node_modules
del package-lock.json
npm install
npm start
```

---

## 📚 Mehr Informationen

Detaillierte Anleitung: [README.md](README.md)

---

**Viel Erfolg! 🚀**
