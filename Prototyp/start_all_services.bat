@echo off
echo ====================================================
echo Starting ABS-CDSS - All Services
echo ====================================================
echo.
echo This will start:
echo - Backend API Server (Port 8000)
echo - Admin Frontend (Port 3000) 
echo - Enduser Frontend (Port 4000)
echo.
echo Press Ctrl+C in any window to stop the respective service.
echo Close this window to stop all services.
echo.
echo ====================================================

REM Set window title for main window
title ABS-CDSS - Service Controller

REM Start Backend in new window
echo Starting Backend API Server...
start "ABS-CDSS Backend (Port 8000)" cmd /k "cd /d "%~dp0" && start_backend_venv.bat"

REM Wait a moment for backend to initialize
timeout /t 3 /nobreak > nul

REM Start Admin Frontend in new window  
echo Starting Admin Frontend...
start "ABS-CDSS Admin Frontend (Port 3000)" cmd /k "cd /d "%~dp0" && start_frontend.bat"

REM Wait a moment
timeout /t 2 /nobreak > nul

REM Start Enduser Frontend in new window
echo Starting Enduser Frontend...
start "ABS-CDSS Enduser Frontend (Port 4000)" cmd /k "cd /d "%~dp0" && start_enduser_frontend.bat"

echo.
echo ====================================================
echo All services are starting...
echo.
echo Backend API:        http://localhost:8000
echo Admin Frontend:     http://localhost:3000
echo Enduser Frontend:   http://localhost:4000
echo API Documentation:  http://localhost:8000/docs
echo.
echo ====================================================
echo.
echo All services are now running in separate windows.
echo You can close this window - the services will continue running.
echo To stop a service, go to its window and press Ctrl+C.
echo.
pause