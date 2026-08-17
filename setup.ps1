# AI News Agent Setup Script for PowerShell

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " AI Morning Brief Agent - Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[1/4] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.7+ from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Install requirements
Write-Host "[2/4] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "Dependencies installed successfully!" -ForegroundColor Green
Write-Host ""

# Check if .env exists
Write-Host "[3/4] Checking .env file..." -ForegroundColor Yellow
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file from template..." -ForegroundColor Cyan
    Copy-Item .env.example -Destination .env
    Write-Host ".env file created. Please edit it with your credentials." -ForegroundColor Green
} else {
    Write-Host ".env file already exists. Skipping creation." -ForegroundColor Green
}
Write-Host ""

# Run test
Write-Host "[4/4] Testing configuration..." -ForegroundColor Yellow
Write-Host ""
python ai_news_agent.py --test-email
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your credentials:" -ForegroundColor White
Write-Host "   - Gmail: EMAIL_USER and EMAIL_APP_PASSWORD"
Write-Host "   - NewsAPI: NEWSAPI_KEY from https://newsapi.org/"
Write-Host "   - Recipient: RECIPIENT_EMAIL"
Write-Host ""
Write-Host "2. Test the agent:" -ForegroundColor White
Write-Host "   python ai_news_agent.py --test-email"
Write-Host ""
Write-Host "3. Preview the 5-item briefing:" -ForegroundColor White
Write-Host "   python ai_news_agent.py --preview"
Write-Host ""
Write-Host "4. Run the brief now:" -ForegroundColor White
Write-Host "   python ai_news_agent.py --run-now"
Write-Host ""
Write-Host "5. Start daily scheduler at 8:00 AM:" -ForegroundColor White
Write-Host "   python ai_news_agent.py --schedule"
Write-Host ""
Write-Host "For more details, see README.md" -ForegroundColor Cyan
Write-Host ""
