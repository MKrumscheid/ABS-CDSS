#!/usr/bin/env pwsh
# FHIR Medication Parsing Test Runner

Write-Host "Starting FHIR Medication Parsing Test..." -ForegroundColor Yellow
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & "venv\Scripts\Activate.ps1"
} elseif (Test-Path "venv\bin\activate") {
    Write-Host "Activating virtual environment (Unix)..." -ForegroundColor Green
    & "venv/bin/activate"
} else {
    Write-Host "No virtual environment found, using system Python..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Running test script..." -ForegroundColor Cyan
python test_fhir_medications.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Test completed successfully!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Test failed!" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")