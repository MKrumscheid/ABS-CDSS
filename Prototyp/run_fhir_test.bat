@echo off
echo Starting FHIR Medication Parsing Test...
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found, using system Python...
)

echo.
echo Running test script...
python test_fhir_medications.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Test completed successfully!
) else (
    echo.
    echo ❌ Test failed!
)

echo.
pause