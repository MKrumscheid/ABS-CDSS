@echo off
echo ===================================
echo RAG Test Pipeline - Frontend Setup
echo ===================================

echo.
echo 1. Installing Node.js dependencies...
cd frontend
call npm install

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Error installing Node.js dependencies
    pause
    exit /b 1
)

echo.
echo ✅ Frontend setup complete!
echo.
echo Starting React development server...
echo Frontend will be available at: http://localhost:3000
echo.

call npm start