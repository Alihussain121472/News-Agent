@echo off
REM AI News Agent Setup Script for Windows

echo.
echo ========================================
echo  AI News Digest Agent - Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Python found: 
python --version
echo.

REM Install requirements
echo [2/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully!
echo.

REM Check if .env exists
if not exist .env (
    echo [3/4] Creating .env file from template...
    copy .env.example .env
    echo .env file created. Please edit it with your credentials.
) else (
    echo [3/4] .env file already exists. Skipping creation.
)
echo.

REM Run test
echo [4/4] Testing configuration...
echo.
python ai_news_agent.py --test-email
echo.

echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your credentials:
echo    - Gmail: EMAIL_USER and EMAIL_APP_PASSWORD
echo    - NewsAPI: NEWSAPI_KEY from https://newsapi.org/
echo    - Recipient: RECIPIENT_EMAIL
echo.
echo 2. Test the agent:
echo    python ai_news_agent.py --test-email
echo.
echo 3. Run news digest now:
echo    python ai_news_agent.py --run-now
echo.
echo 4. Start daily scheduler:
echo    python ai_news_agent.py --schedule
echo.
echo For more details, see AI_NEWS_AGENT_README.md
echo.
pause
