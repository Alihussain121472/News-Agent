# 🤖 AI News Agent Portfolio

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**AI News Agent Portfolio** is an intelligent, automated news digest system that fetches the latest AI industry news and delivers beautiful email briefings to multiple recipients. Features a stunning web dashboard for managing recipients, viewing 3-month news history, and monitoring agent activity.

![AI News Agent Dashboard](https://img.shields.io/badge/Status-Active-success)

![AI News Agent Dashboard](https://img.shields.io/badge/Status-Active-success)

---

## ✨ Features

### 📧 **Multi-Recipient Email System**
- Add unlimited email recipients through web dashboard
- Send daily AI news digests to all recipients automatically
- Beautiful HTML-formatted emails with insights and context
- Individual delivery tracking and success monitoring

### 📰 **Smart News Aggregation**
- Fetches latest AI news from NewsAPI
- Automatic fallback to Google News RSS
- Covers: AI, Machine Learning, ChatGPT, LLMs, AI Policy, AI Safety
- Contextual analysis: "Why it matters", "What could change", "Why you should care"

### 🎨 **Beautiful Web Portfolio Dashboard**
- Real-time statistics and monitoring
- 3-month news history with search and filtering
- Recipient management (add/remove emails)
- Email delivery logs and agent activity tracking
- Responsive design with gradient UI

### 🗄️ **Smart Data Management**
- SQLite database stores all fetched news
- Automatic 3-month data retention
- Search functionality across all articles
- Email and agent activity logging

### ⚙️ **Automated Scheduling**
- Daily digest at 8:03 AM (configurable)
- Runs automatically via scheduled tasks
- Manual trigger available from dashboard
- Background processing with full logging

---

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Gmail account with App Password enabled
- NewsAPI key (free tier available)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Alihussain121472/ai-news-agent-portfolio.git
   cd ai-news-agent-portfolio
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your information:
   ```env
   # Gmail Configuration
   GMAIL_USER=your_gmail@gmail.com
   GMAIL_APP_PASSWORD=your_16_character_app_password
   
   # NewsAPI Configuration
   NEWSAPI_KEY=your_newsapi_key_here
   RECIPIENT_EMAIL=default_recipient@gmail.com
   ```

4. **Get Gmail App Password**
   - Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and your device
   - Copy the 16-character password to `.env`

5. **Get NewsAPI Key**
   - Visit [NewsAPI.org](https://newsapi.org/)
   - Sign up for free (100 requests/day)
   - Copy your API key to `.env`

---

## 📖 Usage

### Launch Web Dashboard

```bash
python web_server.py
```

Open your browser to: **http://localhost:5000**

### Send News Digest Immediately

```bash
python ai_news_agent.py --run-now
```

### Test Email Configuration

```bash
python ai_news_agent.py --test-email
```

### Preview News (No Email)

```bash
python ai_news_agent.py --preview
```

### Start Daily Scheduler

```bash
python ai_news_agent.py --schedule
```

---

## 🎯 Dashboard Features

### 📊 Real-Time Statistics
- Total articles stored
- Articles this week/month
- Email delivery count and success rate
- Last email sent timestamp

### 📧 Recipient Management
- Add new email addresses instantly
- Remove recipients with one click
- View all active recipients
- All recipients receive daily digests

### 📰 News History
- View all stored articles (3-month retention)
- Search by title or content
- Filter by date range (7/30/90 days)
- Full article summaries with AI insights

### 📋 Activity Logs
- **Articles Tab**: Browse all news with insights
- **Email Logs**: Track delivery status per recipient
- **Agent Logs**: Monitor system activity

### ⚙️ Quick Actions
- **Run Agent Now**: Send digest immediately
- **Refresh Data**: Update all statistics
- **Cleanup Old Data**: Remove articles >3 months

---

## 🗂️ Project Structure

```
ai-news-agent-portfolio/
├── ai_news_agent.py          # Main agent logic
├── database.py                # SQLite database management
├── web_server.py              # Flask web dashboard
├── templates/
│   └── dashboard.html         # Web UI
├── recipients.json            # Email recipient list
├── news_history.db            # SQLite database (auto-created)
├── .env                       # Configuration (not tracked)
├── .env.example               # Configuration template
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── ai_news_agent.log          # Agent activity logs
```

---

## 🔧 Configuration

### Change Schedule Time

Edit `ai_news_agent.py` line 307:
```python
scheduler.add_job(run_news_digest, 'cron', hour=8, minute=3)
# Change hour and minute as needed
```

### Customize News Topics

Edit `ai_news_agent.py` line 127:
```python
query = 'artificial intelligence OR machine learning OR your custom topics'
```

### Adjust Article Count

Edit `ai_news_agent.py` line 284:
```python
news_items = search_ai_news(limit=5)  # Change to desired number
```

---

## 📧 Email Template

Each digest includes:
- **5 curated AI news articles**
- Article title, source, and publish date
- AI-generated summary
- **Why it matters**: Impact analysis
- **What could change**: Future implications
- **Why you should care**: Personal relevance
- Direct links to full articles

---

## 🛠️ Technology Stack

- **Backend**: Python 3.7+, Flask 3.0
- **Database**: SQLite3
- **Email**: SMTP (Gmail)
- **News API**: NewsAPI.org + Google News RSS
- **Scheduling**: APScheduler
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Data Parsing**: feedparser, requests

---

## 🔐 Security Notes

- Never commit `.env` file (included in `.gitignore`)
- Use Gmail App Passwords, not your main password
- Keep your NewsAPI key private
- Database stores no sensitive information
- Recipients list stored locally in `recipients.json`

---

## 🐛 Troubleshooting

### "Gmail credentials not found"
- Verify `.env` file exists with correct variable names
- Check `GMAIL_USER` and `GMAIL_APP_PASSWORD` are set
- Ensure App Password is exactly 16 characters

### "NewsAPI key rejected"
- Verify your API key at [NewsAPI.org](https://newsapi.org/)
- Check you haven't exceeded 100 requests/day (free tier)
- Agent automatically falls back to Google News RSS

### "Connection refused" for email
- Ensure using App Password, not regular Gmail password
- Check internet connection
- Try test email: `python ai_news_agent.py --test-email`

### Dashboard not loading
- Ensure Flask is installed: `pip install Flask`
- Check port 5000 is not in use
- Try accessing `http://127.0.0.1:5000`

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📜 License

This project is licensed under the MIT License.

---

## 📞 Contact

**Ali Hussain**
- GitHub: [@Alihussain121472](https://github.com/Alihussain121472)
- Email: syedali6160@gmail.com

---

## 🌟 Star this repository if you find it helpful!

**Made with ❤️ by Ali Hussain**