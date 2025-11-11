#!/bin/bash

echo "===================================================="
echo "ABS-CDSS - Automatische Einrichtung"
echo "===================================================="
echo ""
echo "Dieses Script richtet die komplette Anwendung ein:"
echo "- Erstellt Python Virtual Environment"
echo "- Installiert Backend-Abhängigkeiten"
echo "- Installiert Frontend-Abhängigkeiten"
echo "- Prüft PostgreSQL-Verbindung"
echo ""
echo "Voraussetzungen:"
echo "- Python 3.11+ installiert"
echo "- Node.js 18+ installiert"
echo "- PostgreSQL installiert und Datenbank 'abs_cdss' erstellt"
echo "- .env Datei im backend Ordner konfiguriert"
echo ""
read -p "Drücken Sie Enter zum Fortfahren..."
echo ""

# ====================================================
# 1. Python-Installation prüfen
# ====================================================
echo "[1/6] Prüfe Python-Installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python ist nicht installiert oder nicht im PATH"
    echo ""
    echo "Bitte installieren Sie Python 3.11 oder höher:"
    echo "- macOS: brew install python@3.11"
    echo "- Ubuntu/Debian: sudo apt install python3.11 python3.11-venv python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION gefunden"
echo ""

# ====================================================
# 2. Node.js-Installation prüfen
# ====================================================
echo "[2/6] Prüfe Node.js-Installation..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js ist nicht installiert oder nicht im PATH"
    echo ""
    echo "Bitte installieren Sie Node.js von:"
    echo "https://nodejs.org/"
    echo ""
    echo "- macOS: brew install node"
    echo "- Ubuntu/Debian: sudo apt install nodejs npm"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✅ Node.js $NODE_VERSION gefunden"
echo ""

# ====================================================
# 3. Virtual Environment erstellen
# ====================================================
echo "[3/6] Erstelle Python Virtual Environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual Environment existiert bereits"
    read -p "Möchten Sie es neu erstellen? (j/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[JjYy]$ ]]; then
        echo "Lösche bestehendes Virtual Environment..."
        rm -rf venv
        echo "Erstelle neues Virtual Environment..."
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            echo "❌ Fehler beim Erstellen des Virtual Environment"
            exit 1
        fi
    fi
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Fehler beim Erstellen des Virtual Environment"
        echo ""
        echo "Versuchen Sie:"
        echo "  python3 -m pip install --upgrade pip"
        echo "  python3 -m pip install virtualenv"
        exit 1
    fi
fi
echo "✅ Virtual Environment bereit"
echo ""

# ====================================================
# 4. Backend-Abhängigkeiten installieren
# ====================================================
echo "[4/6] Installiere Backend-Abhängigkeiten..."
echo ""
echo "Aktiviere Virtual Environment..."
source venv/bin/activate

echo "Aktualisiere pip..."
python -m pip install --upgrade pip --quiet

echo ""
echo "Installiere Abhängigkeiten (dies kann einige Minuten dauern)..."
echo ""

# Prüfen ob GPU-Version gewünscht
read -p "Möchten Sie GPU-Unterstützung installieren? (Erfordert NVIDIA GPU mit CUDA) (j/n): " -n 1 -r
echo ""
echo ""

if [[ $REPLY =~ ^[JjYy]$ ]]; then
    echo "Installiere Backend mit GPU-Unterstützung..."
    cd backend
    pip install -r requirements_gpu.txt
    if [ $? -ne 0 ]; then
        echo "❌ Fehler bei der Installation der GPU-Abhängigkeiten"
        cd ..
        exit 1
    fi
    echo ""
    echo "Installiere PyTorch mit CUDA-Unterstützung..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    cd ..
else
    echo "Installiere Backend ohne GPU-Unterstützung..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Fehler bei der Installation der Backend-Abhängigkeiten"
        exit 1
    fi
fi

echo "✅ Backend-Abhängigkeiten installiert"
echo ""

# ====================================================
# 5. Frontend-Abhängigkeiten installieren
# ====================================================
echo "[5/6] Installiere Frontend-Abhängigkeiten..."
echo "(dies kann einige Minuten dauern)..."
echo ""
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo "❌ Fehler bei der Installation der Frontend-Abhängigkeiten"
    cd ..
    exit 1
fi
cd ..
echo "✅ Frontend-Abhängigkeiten installiert"
echo ""

# ====================================================
# 6. Konfiguration prüfen
# ====================================================
echo "[6/6] Prüfe Konfiguration..."
echo ""

# .env Datei prüfen
if [ ! -f "backend/.env" ]; then
    echo "⚠️  WARNUNG: backend/.env Datei nicht gefunden!"
    echo ""
    echo "Bitte erstellen Sie die .env Datei mit folgenden Einstellungen:"
    echo "- NOVITA_API_KEY: Ihr Novita AI API-Schlüssel"
    echo "- DATABASE_URL: PostgreSQL Verbindungs-URL"
    echo ""
    echo "Beispiel:"
    echo "DATABASE_URL=postgresql://postgres:IHR_PASSWORT@localhost:5432/abs_cdss"
    echo "NOVITA_API_KEY=sk_..."
    echo ""
    echo "Siehe README.md für Details."
    echo ""
else
    echo "✅ .env Datei gefunden"
fi

# Datenverzeichnisse erstellen
echo ""
echo "Erstelle Datenverzeichnisse..."
mkdir -p backend/data/embeddings
mkdir -p backend/data/guidelines
mkdir -p backend/data/additional_info
mkdir -p backend/data/dose_info
echo "✅ Datenverzeichnisse erstellt"
echo ""

# PostgreSQL-Verbindung testen (optional)
read -p "Möchten Sie die PostgreSQL-Verbindung testen? (j/n): " -n 1 -r
echo ""
echo ""

if [[ $REPLY =~ ^[JjYy]$ ]]; then
    echo "Teste Datenbankverbindung..."
    source venv/bin/activate
    python -c "from sqlalchemy import create_engine; import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); engine = create_engine(os.getenv('DATABASE_URL', 'postgresql://postgres:123@localhost:5432/abs_cdss')); conn = engine.connect(); print('✅ Datenbankverbindung erfolgreich'); conn.close()" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "⚠️  Datenbankverbindung fehlgeschlagen"
        echo ""
        echo "Bitte stellen Sie sicher, dass:"
        echo "- PostgreSQL läuft"
        echo "- Die Datenbank 'abs_cdss' existiert"
        echo "- Die DATABASE_URL in der .env korrekt ist"
        echo ""
        echo "Sie können die Anwendung trotzdem starten, aber einige"
        echo "Funktionen (Speichern von Empfehlungen) funktionieren nicht."
        echo ""
    else
        echo "✅ Datenbankverbindung erfolgreich"
        echo ""
    fi
fi

echo ""
echo "===================================================="
echo "✅ Installation abgeschlossen!"
echo "===================================================="
echo ""
echo "Nächste Schritte:"
echo ""
echo "1. Stellen Sie sicher, dass PostgreSQL läuft"
echo "2. Starten Sie die Services:"
echo ""
echo "   Backend:"
echo "     cd backend"
echo "     source ../venv/bin/activate"
echo "     python main.py"
echo ""
echo "   Frontend (in neuem Terminal):"
echo "     cd frontend"
echo "     npm start                    # Admin-Frontend"
echo "     npm run start:enduser         # Endbenutzer-Frontend"
echo ""
echo "Nach dem Start verfügbar unter:"
echo "   - Backend API:        http://localhost:8000"
echo "   - Admin-Frontend:     http://localhost:3000"
echo "   - Enduser-Frontend:   http://localhost:4000"
echo "   - API-Dokumentation:  http://localhost:8000/docs"
echo ""
echo "===================================================="
echo ""
