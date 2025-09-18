@echo off
echo ===================================================
echo RAG Test Pipeline - Clinical Decision Support
echo ===================================================
echo.
echo Dieses Skript richtet die komplette RAG-Testpipeline ein.
echo.
echo Voraussetzungen:
echo - Python 3.8+ installiert
echo - Node.js 16+ installiert  
echo - Internetverbindung für Dependencies
echo.
echo Prüfe Python-Installation...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python ist nicht installiert oder nicht im PATH
    echo Bitte installieren Sie Python von python.org
    pause
    exit /b 1
)

echo.
echo Prüfe pip-Installation...
pip --version
if %ERRORLEVEL% NEQ 0 (
    echo ❌ pip ist nicht verfügbar
    pause
    exit /b 1
)

echo.
echo ✅ 1/4 - Erstelle Datenverzeichnisse...
mkdir backend\data 2>nul
mkdir backend\data\embeddings 2>nul
mkdir backend\data\guidelines 2>nul

echo ✅ 2/4 - Installiere Python Dependencies (inkl. FHIR Support)...
cd backend
echo.
echo Verwende --user Installation für bessere Kompatibilität...
echo.
echo Installiere FHIR.resources und weitere Dependencies...
echo.

REM Try user installation first
pip install --user --upgrade pip
pip install --user -r ../requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ⚠️  Benutzer-Installation fehlgeschlagen. Versuche globale Installation...
    echo.
    pip install -r ../requirements.txt
    
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ❌ Installation fehlgeschlagen!
        echo.
        echo Mögliche Lösungen:
        echo 1. Führen Sie die Eingabeaufforderung als Administrator aus
        echo 2. Oder installieren Sie in einer virtuellen Umgebung:
        echo    python -m venv venv
        echo    venv\Scripts\activate
        echo    pip install -r ../requirements.txt
        echo.
        pause
        exit /b 1
    )
)

cd ..

echo.
echo ✅ 3/4 - Prüfe Node.js Installation...
node --version
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js ist nicht installiert
    echo Bitte installieren Sie Node.js von nodejs.org
    pause
    exit /b 1
)

echo.
echo Installiere Node.js Dependencies...
cd frontend
call npm install

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Fehler beim Installieren der Node.js-Abhängigkeiten
    echo Versuche npm cache zu löschen...
    call npm cache clean --force
    call npm install
    
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Installation fehlgeschlagen
        pause
        exit /b 1
    )
)

cd ..

echo.
echo ✅ 4/4 - Setup abgeschlossen!
echo.
echo ===================================================
echo              NÄCHSTE SCHRITTE
echo ===================================================
echo.
echo 1. Backend starten:
echo    Führen Sie 'start_backend.bat' aus
echo    API verfügbar unter: http://localhost:8000
echo.
echo 2. Frontend starten (in neuer Konsole):
echo    Führen Sie 'start_frontend.bat' aus  
echo    UI verfügbar unter: http://localhost:3000
echo.
echo 3. Leitlinien hochladen:
echo    - Beispiele in example_data/ verfügbar
echo    - Verwenden Sie die Upload-Funktion in der UI
echo.
echo 4. FHIR Patienten suchen:
echo    - Neuer Patienten-Tab verfügbar
echo    - Suche nach ID oder Name+Geburtsdatum
echo    - HAPI FHIR Server: https://hapi.fhir.org/baseR4
echo.
echo 5. RAG-Tests durchführen:
echo    - Wählen Sie klinische Parameter
echo    - Testen Sie verschiedene Queries
echo.
echo ===================================================
echo.
echo Drücken Sie eine beliebige Taste zum Beenden...
pause >nul