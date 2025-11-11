@echo off
setlocal enabledelayedexpansion

echo ====================================================
echo ABS-CDSS - Automatische Einrichtung
echo ====================================================
echo.
echo Dieses Script richtet die komplette Anwendung ein:
echo - Erstellt Python Virtual Environment
echo - Installiert Backend-Abhängigkeiten
echo - Installiert Frontend-Abhängigkeiten
echo - Prüft PostgreSQL-Verbindung
echo.
echo Voraussetzungen:
echo - Python 3.11+ installiert und im PATH
echo - Node.js 18+ installiert und im PATH
echo - PostgreSQL installiert und Datenbank 'abs_cdss' erstellt
echo - .env Datei im backend Ordner konfiguriert
echo.
pause
echo.

REM ====================================================
REM 1. Python-Installation prüfen
REM ====================================================
echo [1/6] Prüfe Python-Installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python ist nicht installiert oder nicht im PATH
    echo.
    echo Bitte installieren Sie Python 3.11 oder höher von:
    echo https://www.python.org/downloads/
    echo.
    echo WICHTIG: Aktivieren Sie bei der Installation "Add Python to PATH"
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% gefunden
echo.

REM ====================================================
REM 2. Node.js-Installation prüfen
REM ====================================================
echo [2/6] Prüfe Node.js-Installation...
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js ist nicht installiert oder nicht im PATH
    echo.
    echo Bitte installieren Sie Node.js von:
    echo https://nodejs.org/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
echo ✅ Node.js %NODE_VERSION% gefunden
echo.

REM ====================================================
REM 3. Virtual Environment erstellen
REM ====================================================
echo [3/6] Erstelle Python Virtual Environment...
if exist venv (
    echo ⚠️  Virtual Environment existiert bereits
    echo Möchten Sie es neu erstellen? (Alle installierten Pakete gehen verloren)
    choice /C JN /M "Virtual Environment neu erstellen?"
    if !ERRORLEVEL! EQU 1 (
        echo Lösche bestehendes Virtual Environment...
        rmdir /s /q venv
        echo Erstelle neues Virtual Environment...
        python -m venv venv
        if !ERRORLEVEL! NEQ 0 (
            echo ❌ Fehler beim Erstellen des Virtual Environment
            pause
            exit /b 1
        )
    )
) else (
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Fehler beim Erstellen des Virtual Environment
        echo.
        echo Versuchen Sie:
        echo   python -m pip install --upgrade pip
        echo   python -m pip install virtualenv
        pause
        exit /b 1
    )
)
echo ✅ Virtual Environment bereit
echo.

REM ====================================================
REM 4. Backend-Abhängigkeiten installieren
REM ====================================================
echo [4/6] Installiere Backend-Abhängigkeiten...
echo.
echo Aktiviere Virtual Environment...
call venv\Scripts\activate.bat

echo Aktualisiere pip...
python -m pip install --upgrade pip --quiet

echo.
echo Installiere Abhängigkeiten (dies kann einige Minuten dauern)...
echo.

REM Prüfen ob GPU-Version gewünscht
echo Möchten Sie GPU-Unterstützung installieren?
echo (Erfordert NVIDIA GPU mit CUDA)
echo.
choice /C JN /M "GPU-Unterstützung installieren?"
echo.

if !ERRORLEVEL! EQU 1 (
    echo Installiere Backend mit GPU-Unterstützung...
    cd backend
    pip install -r requirements_gpu.txt
    if !ERRORLEVEL! NEQ 0 (
        echo ❌ Fehler bei der Installation der GPU-Abhängigkeiten
        cd ..
        pause
        exit /b 1
    )
    echo.
    echo Installiere PyTorch mit CUDA-Unterstützung...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    cd ..
) else (
    echo Installiere Backend ohne GPU-Unterstützung...
    pip install -r requirements.txt
    if !ERRORLEVEL! NEQ 0 (
        echo ❌ Fehler bei der Installation der Backend-Abhängigkeiten
        pause
        exit /b 1
    )
)

echo ✅ Backend-Abhängigkeiten installiert
echo.

REM ====================================================
REM 5. Frontend-Abhängigkeiten installieren
REM ====================================================
echo [5/6] Installiere Frontend-Abhängigkeiten...
echo (dies kann einige Minuten dauern)...
echo.
cd frontend
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Fehler bei der Installation der Frontend-Abhängigkeiten
    cd ..
    pause
    exit /b 1
)
cd ..
echo ✅ Frontend-Abhängigkeiten installiert
echo.

REM ====================================================
REM 6. Konfiguration prüfen
REM ====================================================
echo [6/6] Prüfe Konfiguration...
echo.

REM .env Datei prüfen
if not exist backend\.env (
    echo ⚠️  WARNUNG: backend\.env Datei nicht gefunden!
    echo.
    echo Bitte erstellen Sie die .env Datei mit folgenden Einstellungen:
    echo - NOVITA_API_KEY: Ihr Novita AI API-Schlüssel
    echo - DATABASE_URL: PostgreSQL Verbindungs-URL
    echo.
    echo Beispiel:
    echo DATABASE_URL=postgresql://postgres:IHR_PASSWORT@localhost:5432/abs_cdss
    echo NOVITA_API_KEY=sk_...
    echo.
    echo Siehe README.md für Details.
    echo.
) else (
    echo ✅ .env Datei gefunden
)

REM Datenverzeichnisse erstellen
echo.
echo Erstelle Datenverzeichnisse...
if not exist backend\data mkdir backend\data
if not exist backend\data\embeddings mkdir backend\data\embeddings
if not exist backend\data\guidelines mkdir backend\data\guidelines
if not exist backend\data\additional_info mkdir backend\data\additional_info
if not exist backend\data\dose_info mkdir backend\data\dose_info
echo ✅ Datenverzeichnisse erstellt
echo.

REM PostgreSQL-Verbindung testen (optional)
echo Möchten Sie die PostgreSQL-Verbindung testen?
choice /C JN /M "Datenbankverbindung testen?"
echo.

if !ERRORLEVEL! EQU 1 (
    echo Teste Datenbankverbindung...
    call venv\Scripts\activate.bat
    python -c "from sqlalchemy import create_engine; import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); engine = create_engine(os.getenv('DATABASE_URL', 'postgresql://postgres:123@localhost:5432/abs_cdss')); conn = engine.connect(); print('✅ Datenbankverbindung erfolgreich'); conn.close()" 2>nul
    if !ERRORLEVEL! NEQ 0 (
        echo ⚠️  Datenbankverbindung fehlgeschlagen
        echo.
        echo Bitte stellen Sie sicher, dass:
        echo - PostgreSQL läuft
        echo - Die Datenbank 'abs_cdss' existiert
        echo - Die DATABASE_URL in der .env korrekt ist
        echo.
        echo Sie können die Anwendung trotzdem starten, aber einige
        echo Funktionen (Speichern von Empfehlungen) funktionieren nicht.
        echo.
    ) else (
        echo ✅ Datenbankverbindung erfolgreich
        echo.
    )
)

echo.
echo ====================================================
echo ✅ Installation abgeschlossen!
echo ====================================================
echo.
echo Nächste Schritte:
echo.
echo 1. Stellen Sie sicher, dass PostgreSQL läuft
echo 2. Führen Sie 'start_all_services.bat' aus, um alle Services zu starten
echo.
echo Oder starten Sie die Services einzeln:
echo   - Backend:            start_backend_venv.bat
echo   - Admin-Frontend:     start_frontend.bat
echo   - Enduser-Frontend:   start_enduser_frontend.bat
echo.
echo Nach dem Start verfügbar unter:
echo   - Backend API:        http://localhost:8000
echo   - Admin-Frontend:     http://localhost:3000
echo   - Enduser-Frontend:   http://localhost:4000
echo   - API-Dokumentation:  http://localhost:8000/docs
echo.
echo ====================================================
echo.
pause
