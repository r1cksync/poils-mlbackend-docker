# Hindi OCR API Setup Script
# This script sets up the Python FastAPI backend for Hindi OCR

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Hindi OCR API Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.9 or later from https://www.python.org/" -ForegroundColor Red
    exit 1
}

# Navigate to the correct directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host ""
Write-Host "Setting up virtual environment..." -ForegroundColor Yellow

# Create virtual environment
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists. Skipping creation." -ForegroundColor Green
} else {
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Virtual environment created successfully!" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to create virtual environment!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow

# Activate virtual environment
$activateScript = ".\venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "Virtual environment activated!" -ForegroundColor Green
} else {
    Write-Host "ERROR: Activation script not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes..." -ForegroundColor Yellow

# Upgrade pip
python -m pip install --upgrade pip --quiet

# Install requirements
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to install dependencies!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Creating directories..." -ForegroundColor Yellow

# Create necessary directories
$dirs = @("model_cache", "logs")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "Already exists: $dir" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Creating .env file..." -ForegroundColor Yellow

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ".env file created from .env.example" -ForegroundColor Green
    Write-Host "You can edit .env to customize settings" -ForegroundColor Cyan
} else {
    Write-Host ".env file already exists" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Start the server:" -ForegroundColor White
Write-Host "   uvicorn main:app --reload" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Visit the API documentation:" -ForegroundColor White
Write-Host "   http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Test the API:" -ForegroundColor White
Write-Host "   python test_api.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Deploy to Render:" -ForegroundColor White
Write-Host "   See DEPLOYMENT.md for instructions" -ForegroundColor Yellow
Write-Host ""
Write-Host "Note: First run will download the ML model (~1GB)" -ForegroundColor Cyan
Write-Host "This may take a few minutes on first startup." -ForegroundColor Cyan
Write-Host ""
