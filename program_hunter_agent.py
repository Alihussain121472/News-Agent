import os, json, logging, requests
from datetime import datetime, timedelta
from database import NewsDatabase

logger = logging.getLogger(__name__)

def hunt_for_new_programs():
    logger.info("Starting Program Hunter Agent...")
    newsapi_key = os.environ.get('NEWSAPI_KEY')
    groq_key = os.environ.get('GROQ_API_KEY')
    
    if not newsapi_key or not groq_key:
        logger.warning("Missing API keys for Program Hunter.")
        return 0

    # Queries targeting major companies and specific funds the user wants
    queries = [
        '"student program" OR "fellowship" OR "scholarship"',
        '"Gemini fund" OR "NASA open science"',
        '"free certificate" OR "student grant"'
    ]
    
    articles = []
    for q in queries:
        try:
            url = f"https://newsapi.org/v2/everything?q={requests.utils.quote(q)}&language=en&sortBy=publishedAt&pageSize=5&apiKey={newsapi_key}"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                articles.extend(data.get('articles', []))
        except Exception as e:
            logger.error(f"NewsAPI error in program hunter: {e}")

    if not articles:
        return 0

    db = NewsDatabase()
    added_count = 0
    
    # Process with Groq
    for article in articles[:10]: # Limit to prevent API rate limits
        title = article.get('title', '')
        desc = article.get('description', '')
        url = article.get('url', '')
        
        if not title or not url or '[Removed]' in title:
            continue
            
        prompt = f"""You are an AI that extracts student program announcements.
Analyze this news article:
Title: {title}
Description: {desc}
URL: {url}

Does this announce a specific student program, grant, fellowship, or free certificate by a major organization (like NASA, Google, Gemini Fund, etc)?
If YES, respond with ONLY a valid JSON object matching this schema, nothing else:
{{
  "is_program": true,
  "title": "Program Name",
  "company": "Company Name",
  "description": "Short summary of the program and what students get (goodies, badges, etc)",
  "registration_url": "{url}"
}}
If NO, respond with ONLY: {{"is_program": false}}"""

        try:
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            }
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message']['content']
                result = json.loads(content)
                
                if result.get('is_program') and result.get('title') and result.get('company'):
                    # Check if already exists to prevent duplicates
                    existing = db.get_all_programs()
                    is_dup = any(result['title'].lower() in p['title'].lower() for p in existing)
                    if not is_dup:
                        logger.info(f"Hunter found new program: {result['title']}")
                        db.add_student_program(
                            title=result['title'],
                            company=result['company'],
                            description=result['description'],
                            registration_url=result.get('registration_url') or url,
                            deadline=None,
                            launch_date=datetime.now().strftime('%Y-%m-%d'),
                            category='program',
                            notify_before_days=1
                        )
                        added_count += 1
        except Exception as e:
            logger.error(f"Groq error in program hunter: {e}")
            
    # Trigger notifications immediately if we found any
    if added_count > 0:
        try:
            from ai_news_agent import send_program_notifications
            send_program_notifications()
        except Exception as e:
            logger.error(f"Failed to trigger notifications from hunter: {e}")
            
    return added_count

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv('.env.local')
    hunt_for_new_programs()
