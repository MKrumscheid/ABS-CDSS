@echo off
echo ===================================================
echo Python Installation Diagnose
echo ===================================================
echo.

echo 1. Python Version:
python --version
echo.

echo 2. Python Pfad:
where python
echo.

echo 3. pip Version:
pip --version
echo.

echo 4. pip Pfad:
where pip
echo.

echo 5. Python Site-Packages:
python -c "import site; print('System:', site.getsitepackages()); print('User:', site.getusersitepackages())"
echo.

echo 6. Installierte Pakete:
pip list | findstr -i "fastapi uvicorn pydantic sentence torch faiss"
echo.

echo 7. Verfügbare Installation-Optionen testen:
echo.
echo Test: pip install --user --dry-run pydantic
pip install --user --dry-run pydantic
echo.

echo Test: pip install --dry-run pydantic  
pip install --dry-run pydantic
echo.

echo ===================================================
echo Diagnose abgeschlossen
echo ===================================================
pause