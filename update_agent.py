import re

with open('ai_news_agent.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Update RSS URL
old_rss = "rss_url = 'https://news.google.com/rss/search?q=artificial+intelligence+OR+machine+learning+OR+generative+AI+OR+LLM+OR+AI+policy+OR+AI+safety&hl=en-US&gl=US&ceid=US:en'"
new_rss = "rss_url = 'https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en'"
code = code.replace(old_rss, new_rss)

# Update NewsAPI fetch to top-headlines for tech
old_api = """        resp = requests.get('https://newsapi.org/v2/everything', params={
            'q': 'artificial intelligence OR machine learning OR generative AI OR ChatGPT OR LLM OR AI policy OR AI safety',
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': limit,
            'apiKey': api_key
        }, timeout=15)"""

new_api = """        resp = requests.get('https://newsapi.org/v2/top-headlines', params={
            'category': 'technology',
            'language': 'en',
            'pageSize': limit,
            'apiKey': api_key
        }, timeout=15)"""
code = code.replace(old_api, new_api)

with open('ai_news_agent.py', 'w', encoding='utf-8') as f:
    f.write(code)
