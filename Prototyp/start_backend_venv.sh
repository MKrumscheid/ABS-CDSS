#!/bin/bash
echo "==================================="
echo "RAG Test Pipeline - Backend (venv)"
echo "==================================="

echo ""
echo "Aktiviere virtuelle Python-Umgebung..."
if [ ! -f venv/bin/activate ]; then
    echo "❌ Virtuelle Umgebung nicht gefunden!"
    echo "Bitte führen Sie setup.sh zuerst aus."
    exit 1
fi

source venv/bin/activate

echo ""
echo "Starte FastAPI Server..."
echo "API wird verfügbar sein unter: http://localhost:8000"
echo "Dokumentation unter: http://localhost:8000/docs"
echo ""
echo "Drücken Sie Strg+C zum Beenden"
echo ""

cd backend
python main.py
