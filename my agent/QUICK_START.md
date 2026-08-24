# 🚀 Nova Brief - QUICK START GUIDE

## Complete Website Ready to Deploy!

Your AI News Agent has been upgraded to a **production-ready website** with:

✅ Beautiful landing page with features  
✅ Email subscription system (daily at 8 AM)  
✅ Admin dashboard with analytics  
✅ Contact form & lead capture  
✅ SEO optimization  
✅ Privacy & Terms pages  
✅ Mobile responsive design  
✅ HTTPS ready  

---

## 📋 Step 1: Prepare Your Credentials (5 minutes)

### 1.1 Gmail Setup
```
1. Go to https://myaccount.google.com/apppasswords
2. Enable 2-Factor Auth if needed
3. Select "Mail" and "Windows Computer"
4. Copy the 16-character password
```

### 1.2 Get Free NewsAPI Key
```
1. Go to https://newsapi.org
2. Sign up (completely FREE)
3. Copy your API key
```

### 1.3 Generate Secret Key
```
In PowerShell:
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🌐 Step 2: Get Free Domain (10 minutes)

### Option A: Freenom (Completely Free)
```
1. Go to https://www.freenom.com
2. Search: novabrief, aibriefs, techbrief (etc.)
3. Register for 12 months FREE
4. Note your domain name
```

### Option B: DuckDNS Subdomain (FREE)
```
1. Go to https://www.duckdns.org
2. Create account
3. Add domain (gets: yourname.duckdns.org)
4. Keep browser window open
```

---

## 🚀 Step 3: Deploy to Render (5 minutes)

### 3.1 Push to GitHub
```powershell
cd "C:\Users\DELL\OneDrive\Desktop\my agent"

git add .
git commit -m "Nova Brief: Production Website v1.0"
git push origin main
```

### 3.2 Deploy on Render
1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect GitHub
4. Select your repository
5. Fill in:
   - **Name**: nova-brief-website
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn web_server:app`
   - **Plan**: Free

### 3.3 Add Environment Variables
Click "Advanced" → Add these variables:
```
GMAIL_USER = your-email@gmail.com
GMAIL_APP_PASSWORD = xxxx-xxxx-xxxx-xxxx
NEWSAPI_KEY = your-newsapi-key
RECIPIENT_EMAIL = your-email@gmail.com
FLASK_ENV = production
SECRET_KEY = your-generated-secret-key
```

### 3.4 Deploy!
- Click "Create Web Service"
- Wait 2-3 minutes for deployment
- You'll get a URL: https://nova-brief-website.onrender.com ✅

---

## 🔗 Step 4: Connect Your Domain (10 minutes)

### For Freenom Domains:
1. Go back to Freenom account
2. Go to "My Domains" → Your Domain
3. Click "Management Tools" → "Nameservers"
4. Copy Render's nameservers from dashboard
5. Save changes
6. **Wait 24-48 hours for DNS to propagate**

### For DuckDNS:
1. Go to https://www.duckdns.org
2. Add your Render URL to DuckDNS
3. Updates immediately ✅

---

## ✨ Step 5: Test Your Website (5 minutes)

```
1. Visit your domain in browser
2. Click "Subscribe" button
3. Enter email & name
4. Submit ✅
5. Check email inbox for welcome message
6. Wait until 8 AM tomorrow for first briefing
```

---

## 📊 Step 6: Use Your Admin Dashboard

Visit: `https://novabrief.ai-news.app/dashboard`

See:
- 📈 Subscriber count
- 📧 Email delivery history
- 📰 Articles sent
- 👥 User activity
- 🔧 Run agent manually

---

## 🎯 What You Have Now

### Website Pages:
- ✅ Homepage with hero & features
- ✅ FAQ section
- ✅ Contact form
- ✅ Privacy policy
- ✅ Terms of service
- ✅ Admin dashboard

### Features:
- ✅ Daily emails at 8 AM
- ✅ Email subscriptions
- ✅ Article database
- ✅ User tracking
- ✅ Contact form submissions
- ✅ SEO sitemap
- ✅ Mobile responsive
- ✅ HTTPS/SSL included
- ✅ Analytics ready

### Free Stuff:
- ✅ Domain (.tk, .ml, .ga - Freenom)
- ✅ Hosting (Render)
- ✅ SSL Certificate (HTTPS)
- ✅ Database (SQLite)
- ✅ Email sending (Gmail)
- ✅ News API (NewsAPI)

---

## 💰 Costs

**COMPLETELY FREE TIER:**
- Domain: $0 (Freenom)
- Hosting: $0 (Render free tier)
- Email: $0 (Gmail)
- News: $0 (NewsAPI free tier)
- SSL: $0 (included)

**TOTAL MONTHLY COST: $0** 🎉

---

## 🔄 How It Works

```
1. Every morning at 8:03 AM
2. Agent fetches news from NewsAPI
3. AI analyzes & filters articles
4. Creates beautiful HTML email
5. Sends to all subscribers
6. Users receive briefing in inbox
7. Can view dashboard for stats
8. Can contact support via form
9. New subscribers receive welcome email
```

---

## 🛠️ Customization (Optional)

### Change Email Time
Edit in `ai_news_agent.py`:
```python
# Find this line and change:
scheduler.add_job(run_news_digest, 'cron', hour=8, minute=3)
# To send at 9 AM:
scheduler.add_job(run_news_digest, 'cron', hour=9, minute=0)
```

### Change Branding
Edit in templates:
- Change "Nova Brief" to your name
- Update colors in `static/css/main.css`
- Update emails in `ai_news_agent.py`

---

## 📞 Need Help?

### Common Issues:

**❌ Emails not sending**
- Check Gmail app password
- Verify NewsAPI key
- Check FLASK_ENV=production

**❌ Website not loading**
- Wait 5 mins after deployment
- Check Render logs
- Verify environment variables

**❌ Domain not working**
- Wait 24-48 hrs for DNS
- Check nameserver configuration
- Try clearing browser cache

### Resources:
- Render Docs: https://render.com/docs
- Flask Docs: https://flask.palletsprojects.com
- NewsAPI Docs: https://newsapi.org/docs

---

## 🎉 DONE! 

Your complete website is now:

✅ **LIVE** - Accessible on the web  
✅ **SENDING EMAILS** - Daily briefings  
✅ **TRACKING USERS** - Analytics dashboard  
✅ **PROCESSING FORMS** - Contact submissions  
✅ **SEO READY** - Google indexable  
✅ **PROFESSIONAL** - Beautiful design  
✅ **SECURE** - HTTPS/SSL  
✅ **SCALABLE** - Easy to upgrade  

---

## 🚀 Next Steps

1. **Share the link** - Tell friends about Nova Brief
2. **Add subscribers** - More emails = more traffic data
3. **Customize design** - Add your branding
4. **Add premium features** - Optional future enhancement
5. **Analyze metrics** - Check dashboard for stats

---

**Questions?** Check COMPLETE_DEPLOYMENT_GUIDE.md for detailed instructions.

**Version:** 1.0  
**Status:** 🟢 Production Ready  
**Next Deploy:** Add mobile app, API integrations, or premium features
