# 📋 DEPLOYMENT CHECKLIST

Complete this checklist before deploying to production.

## ✅ Pre-Deployment Setup

### Credentials & Keys
- [ ] Gmail app password generated (16 characters)
- [ ] NewsAPI key obtained (free at newsapi.org)
- [ ] Secret key generated using: `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] All sensitive info is in .env file (NOT committed to git)

### Local Testing
- [ ] Run `python web_server.py` locally
- [ ] Visit http://localhost:5000
- [ ] Test subscribe form
- [ ] Test admin dashboard at http://localhost:5000/dashboard
- [ ] Check Privacy, Terms, Cookie pages
- [ ] Test contact form
- [ ] Verify email sending with test account

### Code Quality
- [ ] No Python syntax errors
- [ ] Database initializes without errors
- [ ] All imports are available
- [ ] No hardcoded secrets in code
- [ ] .gitignore configured properly
- [ ] Requirements.txt is up to date

### GitHub Preparation
- [ ] Repository is public (for free deployment)
- [ ] All code committed: `git add .`
- [ ] Meaningful commit message: `git commit -m "Deploy Nova Brief"`
- [ ] Pushed to main branch: `git push origin main`

---

## ✅ Domain Setup

### Free Domain
- [ ] Domain registered (Freenom, DuckDNS, or other free service)
- [ ] Domain is active and accessible
- [ ] Nameservers noted for later configuration

---

## ✅ Hosting Setup (Render)

### Account & Connection
- [ ] Render account created
- [ ] GitHub connected to Render
- [ ] Repository is accessible from Render

### Service Configuration
- [ ] Service name: nova-brief-website
- [ ] Root directory set correctly
- [ ] Runtime: Python 3
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `gunicorn web_server:app`
- [ ] Plan: Free tier selected

### Environment Variables
- [ ] GMAIL_USER set correctly
- [ ] GMAIL_APP_PASSWORD set correctly
- [ ] NEWSAPI_KEY set correctly
- [ ] RECIPIENT_EMAIL set correctly
- [ ] FLASK_ENV set to "production"
- [ ] SECRET_KEY set to unique random string
- [ ] All variables saved

### Deployment
- [ ] Service deployed successfully
- [ ] No build errors in logs
- [ ] Service shows as "Live" in Render dashboard
- [ ] Can access test URL from Render
- [ ] Website loads without errors

---

## ✅ Domain Configuration

### DNS Setup
- [ ] Domain DNS configured to point to Render
- [ ] Custom domain added to Render service settings
- [ ] SSL certificate provisioned (automatic)
- [ ] HTTPS working (green lock in browser)

### DNS Verification (if needed)
- [ ] CNAME record created: novabrief.ai-news.app → your-render-service.onrender.com
- [ ] DNS TTL appropriate (3600 seconds)
- [ ] DNS propagation checked (might take 24-48 hours)

---

## ✅ Functionality Testing

### Website Features
- [ ] Homepage loads correctly
- [ ] Hero section displays
- [ ] Features section visible
- [ ] Subscribe section visible and working
- [ ] FAQ accordion works
- [ ] Contact form loads

### Subscription System
- [ ] Subscribe form accepts input
- [ ] Email validation works
- [ ] Subscription success message shows
- [ ] Subscriber added to database
- [ ] Welcome email received

### Admin Dashboard
- [ ] Dashboard accessible at /dashboard
- [ ] Statistics display correctly
- [ ] Article list loads
- [ ] Email logs show history
- [ ] Run agent button works

### Pages & Legal
- [ ] Privacy policy page accessible
- [ ] Terms of service page accessible
- [ ] Cookie policy page accessible
- [ ] Contact page with form works
- [ ] Footer links work correctly

### Mobile & Responsive
- [ ] Website works on mobile browsers
- [ ] Navigation collapses on small screens
- [ ] Subscribe form works on mobile
- [ ] Dashboard accessible on mobile
- [ ] No layout issues

---

## ✅ Email System

### Daily Sending
- [ ] Wait until scheduled time (8:03 AM)
- [ ] Check email for automated briefing
- [ ] Email has proper formatting
- [ ] Email contains articles
- [ ] Unsubscribe link present

### Manual Testing
- [ ] Visit /api/agent/run-now endpoint
- [ ] Agent runs and sends test email
- [ ] No errors in logs
- [ ] Email received within 1 minute

### Database
- [ ] Articles saved in database
- [ ] Email logs recorded
- [ ] Subscriber count updated
- [ ] User activity tracked

---

## ✅ Security Checklist

### Credentials
- [ ] No passwords in git commits
- [ ] All secrets in environment variables
- [ ] .env file in .gitignore
- [ ] Secret key is unique
- [ ] Email password is app-specific password

### Website Security
- [ ] HTTPS enabled (https://novabrief.ai-news.app)
- [ ] HTTP redirects to HTTPS
- [ ] Form inputs validated
- [ ] SQL injection prevention
- [ ] CSRF protection (if applicable)

### API Security
- [ ] No sensitive data in logs
- [ ] Rate limiting considered
- [ ] API endpoints protected (if needed)
- [ ] Database backups planned

---

## ✅ Performance & Monitoring

### Website Performance
- [ ] Page loads in under 3 seconds
- [ ] CSS/JS files load properly
- [ ] Images optimized
- [ ] Mobile performance good

### Monitoring Setup
- [ ] Render logs accessible
- [ ] Can view error messages
- [ ] Alerts configured (if available)
- [ ] Backup email setup

### Logging
- [ ] ai_news_agent.log tracking
- [ ] Database operations logged
- [ ] API errors captured
- [ ] Can access Render logs

---

## ✅ Backup & Recovery

### Database Backup
- [ ] Know how to backup news_history.db
- [ ] Backup location documented
- [ ] Recovery process tested

### Code Recovery
- [ ] Code is version controlled in git
- [ ] Can rollback to previous version
- [ ] GitHub repository is secure

---

## ✅ Documentation

### Setup Docs
- [ ] QUICK_START.md completed
- [ ] COMPLETE_DEPLOYMENT_GUIDE.md reviewed
- [ ] Environment variables documented
- [ ] Custom domain instructions saved

### Maintenance Docs
- [ ] Troubleshooting guide prepared
- [ ] Support contact info documented
- [ ] Update procedures documented
- [ ] Backup procedures documented

---

## ✅ Final Steps

### Before Going Live
- [ ] All checks above completed ✓
- [ ] Tested in production environment
- [ ] Team notified of go-live
- [ ] Support plan in place

### Post-Deployment
- [ ] Monitor for first 24 hours
- [ ] Check email delivery at 8 AM
- [ ] Review Render logs for errors
- [ ] Get subscriber feedback
- [ ] Update README with live URL

---

## 📊 Status Tracker

**Pre-Deployment:** [ ] Complete  
**Deployment:** [ ] Complete  
**Testing:** [ ] Complete  
**Security:** [ ] Complete  
**Go-Live:** [ ] Ready  

---

**Prepared by:** _____________  
**Date:** _____________  
**Environment:** [ ] Development [ ] Staging [ ] Production  

---

**🎉 Once all items are checked, your website is production-ready!**
