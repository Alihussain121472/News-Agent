# 📖 Beginner's Guide to the Codebase

Welcome to the Nova Brief codebase! We have designed this code to be easy to understand, even if you are a beginner. Here is a simple breakdown of how the whole website works.

## 1. web_server.py (The Website Brain)
This file is the main engine of the website. It uses a popular Python tool called **Flask**.
- **What it does:** Every time a user types your website address or clicks a button, this file receives the request and decides what to show them.
- **Key Parts:** 
  - @app.route('/'): This means "when someone visits the home page, run the code below".
  - def register_user_account(): This function handles the logic when someone fills out the sign-up form.

## 2. database.py (The Memory)
This file acts like a giant spreadsheet. It uses **SQLite** to safely store information.
- **What it does:** It remembers user accounts, passwords, past news articles, and website statistics.
- **Key Parts:**
  - init_database(): This creates all the "tables" (like sheets in Excel) for the first time.
  - get_user_by_email(): This searches the database to find a specific user so they can log in.

## 3. i_news_agent.py (The Automated Worker)
Think of this file as your digital employee.
- **What it does:** It runs in the background. It searches Google for the latest AI news, formats it into a beautiful email, and sends it to all your subscribers automatically every morning at 8:00 AM.
- **Key Parts:**
  - search_ai_news(): Connects to the internet to find news articles.
  - send_email(): Logs into your Gmail account to send out the newsletters.

## 4. Blueprints (The Organization)
As the website grew, we created separate folders (like social_media_agent, growth_seo_agent, and nalytics_revenue_portal). 
- **What they do:** Instead of putting 10,000 lines of code in web_server.py, we split them into these folders to keep the code clean and easy to read.

---
**💡 Pro Tip for Beginners:** Look for the # symbol in the code. We have added short, plain-English comments above all the major functions to explain exactly what they do!
