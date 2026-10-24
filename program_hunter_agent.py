import os, json, logging, requests
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
    candidate_count = 0
    seen_candidate_titles = set()
    
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

        Does this article report a specific student program, grant, fellowship, or free certificate by an organization?
If YES, respond with ONLY a valid JSON object matching this schema, nothing else:
{{
  "is_program": true,
  "title": "Program Name",
  "company": "Company Name",
  "description": "Short factual summary using only the article text",
  "article_source_url": "{url}"
}}
Do not invent benefits, eligibility, deadlines, or application links. This article URL is only a source for human review, not an application URL.
If NO, respond with ONLY: {{"is_program": false}}"""

        try:
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload = {
                "model": os.environ.get('GROQ_MODEL', 'openai/gpt-oss-120b').strip(),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            }
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message']['content']
                result = json.loads(content)
                
                if result.get('is_program'):
                    # A news article URL is not an application URL. Queue candidates for human review.
                    existing = db.get_all_programs()
                    candidate_title = str(result.get('title') or '').strip()
                    company = str(result.get('company') or '').strip()
                    if not candidate_title or not company:
                        continue
                    normalized_title = candidate_title.casefold()
                    is_dup = (
                        normalized_title in seen_candidate_titles
                        or any(normalized_title in str(p.get('title') or '').casefold() for p in existing)
                    )
                    if not is_dup:
                        seen_candidate_titles.add(normalized_title)
                        source_url = result.get('article_source_url') or url
                        message = (
                            f"Program candidate needs review: {candidate_title} ({company}). "
                            f"Confirm the official application page, current status, eligibility, and deadline before publishing. "
                            f"Article source: {source_url}"
                        )
                        db.log_agent_event(
                            'program_candidate_review',
                            message,
                            details=json.dumps({
                                'title': candidate_title,
                                'company': company,
                                'description': str(result.get('description') or '').strip(),
                                'article_source_url': source_url,
                            }),
                        )
                        logger.info(message)
                        candidate_count += 1
        except Exception as e:
            logger.error(f"Groq error in program hunter: {e}")
            
    return candidate_count

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv('.env.local')
    hunt_for_new_programs()
