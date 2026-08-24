# Deployment Guide for AI News Agent Portfolio

This guide will help you deploy your AI News Agent Portfolio to the cloud so it's accessible from anywhere.

## Option 1: Deploy to Render (Recommended - FREE)

### Step 1: Push Your Updated Code to GitHub

```bash
cd "C:\Users\DELL\OneDrive\Desktop\my agent"
git add Procfile build.sh runtime.txt requirements.txt web_server.py
git commit -m "Add cloud deployment configuration for Render"
git push origin main
```

### Step 2: Deploy on Render

1. **Sign up for Render**:
   - Go to: https://render.com
   - Click "Get Started" or "Sign Up"
   - Sign up with your GitHub account

2. **Create a New Web Service**:
   - Click "New +" button
   - Select "Web Service"
   - Click "Connect GitHub"
   - Authorize Render to access your repositories
   - Select your **"News-Agent"** repository

3. **Configure the Service**:
   - **Name**: `ai-news-agent-portfolio`
   - **Region**: Choose closest to you (e.g., Oregon, Frankfurt)
   - **Branch**: `main`
   - **Root Directory**: `my agent`
   - **Runtime**: `Python 3`
   - **Build Command**: `bash build.sh`
   - **Start Command**: `gunicorn web_server:app`
   - **Instance Type**: `Free`

4. **Add Environment Variables** (Click "Advanced" → "Add Environment Variable"):
   ```
   GMAIL_USER=your-email@gmail.com
   GMAIL_APP_PASSWORD=your-gmail-app-password
   NEWSAPI_KEY=your-newsapi-key
   RECIPIENT_EMAIL=your-email@gmail.com
   PORT=10000
   FLASK_ENV=production
   ```

5. **Click "Create Web Service"**

6. **Wait for Deployment** (2-3 minutes)
   - Render will build and deploy your app
   - You'll get a public URL like: `https://ai-news-agent-portfolio.onrender.com`

---

## Option 2: Deploy to Railway (Alternative - FREE)

### Step 1: Sign Up for Railway

1. Go to: https://railway.app
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose **"News-Agent"** repository

### Step 2: Configure Environment Variables

1. Click on your deployed service
2. Go to "Variables" tab
3. Add these variables:
   ```
   GMAIL_USER=your-email@gmail.com
   GMAIL_APP_PASSWORD=your-gmail-app-password
   NEWSAPI_KEY=your-newsapi-key
   RECIPIENT_EMAIL=your-email@gmail.com
   FLASK_ENV=production
   ```

4. Railway will auto-detect Python and deploy
5. You'll get a public URL like: `https://ai-news-agent-production.up.railway.app`

---

## Option 3: Deploy to PythonAnywhere (Good for Learning)

1. Go to: https://www.pythonanywhere.com
2. Sign up for FREE account
3. Upload your code via Git or manual upload
4. Configure web app in the dashboard
5. Set environment variables
6. You'll get: `https://yourusername.pythonanywhere.com`

---

## After Deployment

### Your App Will Be Accessible At:
- **Public URL**: `https://novabrief.ai-news.app` (after DNS + custom domain setup)
- Accessible from **any device** (phone, tablet, laptop)
- Accessible from **anywhere in the world**
- **Always online** (as long as free tier limits aren't exceeded)

### Features Available:
✅ View news dashboard from anywhere
✅ Manage recipients remotely
✅ Monitor email delivery logs
✅ Search and filter news history
✅ Run agent manually from any device

### Important Notes:

1. **Free Tier Limitations**:
   - **Render**: 750 hours/month free, sleeps after 15 mins of inactivity
   - **Railway**: $5 free credit/month
   - **PythonAnywhere**: Always-on web apps (limited)

2. **Cold Starts**: Free tier apps may take 30-60 seconds to wake up after inactivity

3. **Scheduled Tasks**: 
   - The scheduled email sending will work on PythonAnywhere
   - For Render/Railway, you'll need to use external cron services like:
     - https://cron-job.org (free)
     - https://easycron.com (free tier)
   - Set them to ping your app daily at 8:00 AM

4. **Database Persistence**:
   - Free tier databases may reset periodically
   - For permanent storage, consider upgrading or using external DB

---

## Troubleshooting

### App Not Starting:
- Check build logs in Render/Railway dashboard
- Verify all environment variables are set
- Ensure `requirements.txt` has all dependencies

### Email Not Sending:
- Verify Gmail App Password is correct
- Check environment variables are properly set
- Review app logs for errors

### Database Issues:
- Database file is created automatically on first run
- Free tier may have storage limitations
- Consider using PostgreSQL for production

---

## Security Recommendations

1. **Never commit `.env` file** (already in `.gitignore`)
2. **Use environment variables** for all secrets
3. **Rotate credentials** periodically
4. **Enable 2FA** on deployment platform
5. **Monitor usage** to avoid free tier limits

---

## Upgrading to Production

For serious production use, consider:
- **Paid hosting** ($5-10/month) for better uptime
- **PostgreSQL database** instead of SQLite
- **Redis** for caching and session management
- **CDN** for static assets
- **Monitoring** tools (Sentry, DataDog)
- **Custom domain** for professional URL

---

## Getting Help

- **Render Docs**: https://render.com/docs
- **Railway Docs**: https://docs.railway.app
- **PythonAnywhere**: https://help.pythonanywhere.com

Your portfolio will be live at a public URL accessible from any device! 🚀
