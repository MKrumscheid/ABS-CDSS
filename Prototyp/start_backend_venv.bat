@echo off
echo ===================================
echo RAG Test Pipeline - Backend (venv)
echo ===================================

echo.
echo Aktiviere virtuelle Python-Umgebung...
if not exist venv\Scripts\activate.bat (
    echo ❌ Virtuelle Umgebung nicht gefunden!
    echo Bitte führen Sie setup_venv.bat zuerst aus.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo.
echo Starte FastAPI Server...
echo API wird verfügbar sein unter: http://localhost:8000
echo Dokumentation unter: http://localhost:8000/docs
echo.
echo Drücken Sie Strg+C zum Beenden
echo.

cd backend
python main.py