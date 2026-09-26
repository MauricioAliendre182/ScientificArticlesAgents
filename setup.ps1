# Quick setup script for Scientific Articles Engine (PowerShell/Windows)

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Scientific Articles Engine - Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = (python --version 2>&1).ToString().Split()[1]
    Write-Host "✓ Python $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "myenv")) {
    python -m venv myenv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
}
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\myenv\Scripts\Activate.ps1
Write-Host "✓ Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip | Out-Null
Write-Host "✓ pip upgraded" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -e . | Out-Null
Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Install development dependencies (optional)
$devDeps = Read-Host "Install development dependencies? (y/n)"
if ($devDeps -eq "y") {
    Write-Host "Installing development dependencies..." -ForegroundColor Yellow
    pip install -e ".[dev]" | Out-Null
    Write-Host "✓ Development dependencies installed" -ForegroundColor Green
    Write-Host ""
}

# Setup environment file
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ .env file created" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  Please edit .env and add your API keys:" -ForegroundColor Yellow
    Write-Host "   - OPENAI_API_KEY or ANTHROPIC_API_KEY"
    Write-Host "   - DATABASE_PASSWORD (if using PostgreSQL)"
    Write-Host ""
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
    Write-Host ""
}

# Run tests (optional)
$runTests = Read-Host "Run tests to verify installation? (y/n)"
if ($runTests -eq "y") {
    Write-Host "Running tests..." -ForegroundColor Yellow
    pytest tests/unit/ -v
    Write-Host "✓ Tests completed" -ForegroundColor Green
    Write-Host ""
}

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env with your API keys"
Write-Host "2. Customize config.yaml if needed"
Write-Host "3. Run: .\myenv\Scripts\Activate.ps1"
Write-Host "4. Test: scientific-articles-engine --help"
Write-Host "5. Generate an article: scientific-articles-engine generate 'Your Topic'"
Write-Host ""
Write-Host "For more information, see README.md"
