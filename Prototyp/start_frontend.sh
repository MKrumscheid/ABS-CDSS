#!/bin/bash
echo "==================================="
echo "RAG Test Pipeline - Frontend Setup"
echo "==================================="

echo ""
echo "1. Installing Node.js dependencies..."
cd frontend
npm install

if [ $? -ne 0 ]; then
    echo "❌ Error installing Node.js dependencies"
    exit 1
fi

echo ""
echo "✅ Frontend setup complete!"
echo ""
echo "Starting React development server..."
echo "Frontend will be available at: http://localhost:3000"
echo ""

npm start
