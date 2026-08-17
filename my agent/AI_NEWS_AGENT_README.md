# AI News Digest Agent Setup Guide

## Overview
The AI News Digest Agent automatically fetches the latest AI industry news and sends you a beautifully formatted email digest daily. It uses NewsAPI to source news and Gmail SMTP for email delivery.

## Prerequisites
- Python 3.7+
- Gmail account with app-specific password
- NewsAPI key (free tier available)

## Installation Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Then edit `.env` with:
- `EMAIL_USER`: Your Gmail address
- `EMAIL_APP_PASSWORD`: Your Gmail app-specific password
- `NEWSAPI_KEY`: Your NewsAPI key
- `RECIPIENT_EMAIL`: Email to receive the digest (can be same as EMAIL_USER)

### 3. Get Gmail App Password
1. Go to https://myaccount.google.com/apppasswords
2. Sign in to your Google account
3. Select "Mail" and "Windows Computer" (or your device)
4. Click "Generate"
5. Copy the 16-character password to `.env`

### 4. Get NewsAPI Key
1. Go to https://newsapi.org/
2. Click "Get API Key"
3. Sign up for a free account (100 requests/day included)
4. Copy your API key to `.env`

## Usage

### Run News Digest Immediately
```bash
python ai_news_agent.py --run-now
```

### Send Test Email
Verify configuration is correct:
```bash
python ai_news_agent.py --test-email
```

### Start Daily Scheduler (9 AM)
```bash
python ai_news_agent.py --schedule
```

### Default Behavior
```bash
python ai_news_agent.py
# Runs once and exits
```

## Features

✅ **Latest AI News**: Automatically fetches news about AI, ML, LLMs, ChatGPT, etc.
✅ **Smart Summaries**: Uses NewsAPI descriptions and adds contextual importance messages
✅ **Beautiful Emails**: HTML formatted emails with proper styling and links
✅ **Daily Digest**: Scheduled to send at 9:00 AM each day
✅ **Error Logging**: Full logging to console and file (`ai_news_agent.log`)
✅ **Easy Configuration**: Simple `.env` file setup

## Customization

### Change Digest Time
Edit the scheduler line in `ai_news_agent.py`:
```python
# Line ~232 - Change hour and minute values
scheduler.add_job(run_news_digest, 'cron', hour=9, minute=0)
```

### Change News Topics
Edit the search query in `search_ai_news()`:
```python
query = "your custom search terms here"
```

### Adjust Article Count
Change the limit in `search_ai_news()`:
```python
return news_items[:10]  # Change 10 to desired number
```

## Troubleshooting

### "Gmail credentials not found"
- Ensure `.env` file exists and has correct env variable names
- Double-check EMAIL_USER and EMAIL_APP_PASSWORD are set
- Gmail app passwords must be exactly 16 characters

### "NEWSAPI_KEY not found"
- Verify you copied the entire API key from newsapi.org
- Restart Python after updating `.env`

### "Connection refused" for email
- Ensure you're using an app-specific password, not your Gmail password
- Check that "Less secure app access" isn't needed (app password handles this)

### No articles returned
- Check that your search query is valid
- Verify NEWSAPI_KEY works (test on newsapi.org)
- Free plan has 100 requests/day limit

## Log Files

Check `ai_news_agent.log` for detailed execution logs:
```bash
tail -f ai_news_agent.log
```

## Windows Task Scheduler Integration

To run automatically on Windows startup:

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to your preferred time
4. Set action to run: `python.exe`
5. Add arguments: `"C:\path\to\ai_news_agent.py" --schedule`
6. Set "Run whether user is logged in or not"

## API Limits

**NewsAPI Free Tier:**
- 100 requests per day
- One request per day = ~30 articles retrieved

**Gmail:**
- No limit for personal use
- Respects standard SMTP rate limits

## License
Personal use agent for AI news aggregation

## Support
Check logs for detailed error information and adjust configuration as needed.
