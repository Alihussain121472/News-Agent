# Nova Brief - Complete Website Deployment Guide

Complete website with AI news briefings, email subscriptions, and analytics dashboard.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git
- GitHub account
- Email account (Gmail recommended)
- NewsAPI key (free at https://newsapi.org)

### Local Development

1. **Clone and Setup**
```bash
cd "C:\Users\DELL\OneDrive\Desktop\my agent"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
copy .env.example .env
# Edit .env with your credentials
```

3. **Run Locally**
```bash
python web_server.py
# Visit http://localhost:5000
```

## 📋 Free Domain & Hosting Options

### Option 1: FREE Domain + Render Hosting (RECOMMENDED)

#### Step 1: Get a Free Domain

**Using Freenom (Totally Free)**
1. Go to https://www.freenom.com
2. Search for your domain (e.g., novabrief.tk, novabrief.ml)
3. Register for 12 months free
4. Take note of the domain name

**Alternative: Using Subdomains**
- If you have a GitHub account, use GitHub Pages subdomain
- Or use a free subdomain service like **DuckDNS** (https://www.duckdns.org)

#### Step 2: Deploy to Render (FREE Tier)

1. **Push Code to GitHub**
```bash
git add .
git commit -m "Add Nova Brief website"
git push origin main
```

2. **Create Render Account**
   - Go to https://render.com
   - Click "Get Started"
   - Sign up with GitHub

3. **Create Web Service on Render**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your "my agent" repository

4. **Configure Render Service**
   - **Name**: nova-brief-website
   - **Root Directory**: (leave empty or set to project root)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn web_server:app`
   - **Plan**: Free

5. **Add Environment Variables**
   Click "Advanced" and add these variables:
   ```
   GMAIL_USER=your-email@gmail.com
   GMAIL_APP_PASSWORD=your-app-password
   NEWSAPI_KEY=your-newsapi-key
   RECIPIENT_EMAIL=your-email@gmail.com
   FLASK_ENV=production
   ```

6. **Deploy**
   - Click "Create Web Service"
   - Render will automatically deploy your website
   - You'll get a URL like: https://nova-brief-website.onrender.com

#### Step 3: Connect Your Free Domain

**For Freenom domains:**

1. Go to Freenom account → "My Domains" → Manage Domain
2. Click "Management Tools" → "Nameservers"
3. Use Custom Nameservers:
   - Use Render's provided nameservers (check Render dashboard)
   - Or point to Freenom's default nameservers

**For DuckDNS:**

1. Go to https://www.duckdns.org
2. Create account
3. Add your domain to DuckDNS
4. Point to Render's IP address
5. Update DNS records

**For GitHub Pages subdomain:**
1. Add CNAME file in repository root
2. Set to your Render domain

---

### Option 2: Railway.app (FREE + Credits)

1. Go to https://railway.app
2. Connect GitHub repository
3. Click "Deploy Now"
4. Configure Environment Variables (same as above)
5. Get instant domain or connect custom domain

---

### Option 3: Vercel + Backend (Advanced)

Deploy frontend to Vercel (FREE) and backend to Railway.

---

## 🔧 Environment Variables Setup

Create a `.env` file with these variables:

```env
# Email Configuration (Gmail)
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# News API
NEWSAPI_KEY=your-key-from-newsapi.org

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-random-secret-key

# Recipient Email
RECIPIENT_EMAIL=your-email@gmail.com

# Database
DATABASE_URL=sqlite:///news_history.db

# Port (set automatically by hosting)
PORT=5000
```

### Get Gmail App Password:
1. Enable 2-Factor Authentication on Gmail
2. Go to https://myaccount.google.com/apppasswords
3. Select "Mail" and "Windows Computer"
4. Copy the 16-character password

### Get NewsAPI Key:
1. Go to https://newsapi.org
2. Sign up (FREE tier)
3. Copy your API key

---

## 📊 Features Included

✅ **Beautiful Landing Page**
- Hero section with stats
- Features showcase
- FAQ section
- Contact form

✅ **Email Newsletter System**
- Automated daily briefings at 8 AM
- AI-powered news curation
- Multiple news sources
- Email templates with formatting

✅ **Admin Dashboard**
- View subscriber statistics
- Monitor email delivery
- Track user activity
- View article history
- Run manual news digest

✅ **SEO Optimized**
- Sitemap (sitemap.xml)
- Robots.txt
- Meta tags
- Open Graph tags
- Structured data

✅ **Security**
- Privacy Policy page
- Terms of Service
- Cookie Policy
- GDPR compliance ready
- Secure email handling

✅ **Analytics & Tracking**
- Site visit tracking
- User activity logging
- Email performance metrics
- Subscriber statistics

---

## 🌐 Custom Domain Configuration

### After Deployment, Connect Your Domain

**On Render Dashboard:**
1. Go to your service settings
2. Scroll to "Custom Domain"
3. Add your domain (e.g., novabrief.ai-news.app)
4. Follow DNS configuration instructions

**DNS Configuration (if using separate DNS provider):**
```
Type: CNAME
Name: @ (or your subdomain)
Value: your-render-service.onrender.com
TTL: 3600
```

**SSL Certificate:**
- Render automatically provides free SSL (HTTPS)
- No additional configuration needed

---

## 📧 Email Configuration

### Option A: Gmail (Recommended for Testing)

1. Enable 2FA on Gmail account
2. Generate app password: https://myaccount.google.com/apppasswords
3. Use generated 16-char password in `.env`

### Option B: SendGrid (Better for Production)

1. Sign up at https://sendgrid.com (FREE tier: 100 emails/day)
2. Create API key
3. Update `ai_news_agent.py` to use SendGrid API

### Option C: Mailgun (FREE tier)

1. Sign up at https://www.mailgun.com
2. Get sandbox domain and API key
3. Update email configuration in code

---

## 🚀 Automated Daily Emails

The agent automatically sends emails at **8:03 AM daily** using APScheduler.

**To Trigger Manually:**
```bash
# Via Python
python ai_news_agent.py --run-now

# Via API
curl -X POST https://novabrief.ai-news.app/api/agent/run-now
```

---

## 🗄️ Database

SQLite database (`news_history.db`) stores:
- News articles
- User subscriptions
- Email logs
- Activity tracking
- Contact form submissions

**Backup Database:**
```bash
copy news_history.db news_history.db.backup
```

---

## 📱 Monitoring & Logs

**Render Logs:**
- View in Render Dashboard → "Logs" tab
- Check for errors and performance issues

**Local Logs:**
- `ai_news_agent.log` - Agent activity
- Browser console - Frontend errors

---

## 🔒 Security Checklist

- [ ] Change `SECRET_KEY` in `.env`
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS (automatic on Render)
- [ ] Update privacy policy with your contact
- [ ] Review email templates for branding
- [ ] Set up backup email alerts
- [ ] Monitor API rate limits (NewsAPI)
- [ ] Regular database backups

---

## 📈 Next Steps to Scale

1. **Add Blog** - Document AI news insights
2. **Premium Features** - Paid subscription tier
3. **Mobile App** - React Native app
4. **Telegram Bot** - Alternative notification method
5. **RSS Feed** - Alternative news format
6. **API Endpoints** - Programmatic access
7. **Webhooks** - Integrate with other services
8. **Custom Categories** - User-selected topics

---

## 🆘 Troubleshooting

### Website Not Loading
- Check Render logs
- Verify environment variables
- Check internet connection
- Clear browser cache

### Emails Not Sending
- Verify Gmail app password
- Check NewsAPI key validity
- Review `ai_news_agent.log`
- Check email in spam folder

### Database Errors
- Ensure write permissions
- Check disk space
- Verify SQL syntax
- Review database logs

### Performance Issues
- Upgrade to Render's paid plan
- Optimize database queries
- Cache API responses
- Use CDN for static files

---

## 📞 Support

**Official Documentation:**
- Render: https://render.com/docs
- Flask: https://flask.palletsprojects.com
- NewsAPI: https://newsapi.org/docs

**Need Help?**
- Check logs for error messages
- Review `.env` configuration
- Test API endpoints locally
- Ask in Render community forums

---

## 📄 License

This project is provided as-is for personal and commercial use.

---

## 🎉 You're All Set!

Your Nova Brief website is now:
- ✅ Live on the web
- ✅ Sending daily emails
- ✅ Tracking user activity
- ✅ Processing contact forms
- ✅ SEO optimized
- ✅ Secure with HTTPS

**Next Steps:**
1. Visit your domain
2. Subscribe to the newsletter
3. Check email tomorrow morning at 8 AM
4. Share with friends!

---

**Version:** 1.0  
**Last Updated:** January 2024  
**Status:** Production Ready
