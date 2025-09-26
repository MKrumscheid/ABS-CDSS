@echo off
cd /d "%~dp0frontend"
echo Starting Enduser Frontend on port 4000...
echo Admin Frontend: http://localhost:3000
echo Enduser Frontend: http://localhost:4000
npm run start:enduser
pause