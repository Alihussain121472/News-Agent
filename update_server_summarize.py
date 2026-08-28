import re

with open('web_server.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Add the /api/summarize endpoint
endpoint_code = """
@app.route('/api/summarize', methods=['POST'])
@login_required
def summarize_article():
    data = request.json or {}
    url = data.get('url')
    if not url or url == '#':
        return jsonify({'status': 'error', 'message': 'Invalid URL provided.'}), 400

    try:
        import requests
        from bs4 import BeautifulSoup
        import os
        
        # Scrape the article text
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        if len(text) < 100:
            return jsonify({'status': 'error', 'message': 'Could not extract enough readable text from this article.'}), 400
            
        # Truncate text to avoid token limits (approx 3000 words)
        text = text[:15000]
        
        # Send to Groq Llama 3
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            return jsonify({'status': 'error', 'message': 'AI Summarization is currently disabled (API Key missing).'}), 500
            
        groq_resp = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={
                'model': 'llama-3.3-70b-versatile',
                'messages': [
                    {'role': 'system', 'content': 'You are an expert technology analyst. Provide a quick, highly readable summary of the provided article in 3 to 4 bullet points. Focus on the most important takeaways. Do not include introductory fluff.'},
                    {'role': 'user', 'content': f'Summarize this article:\\n\\n{text}'}
                ],
                'temperature': 0.3,
                'max_tokens': 500
            },
            timeout=20
        )
        groq_resp.raise_for_status()
        summary = groq_resp.json()['choices'][0]['message']['content']
        
        # Record activity
        db.record_activity(session.get('user_email'), 'summarizer_used', f'Summarized article: {url}')
        
        return jsonify({'status': 'success', 'summary': summary})
        
    except Exception as e:
        logger.error(f"Summarizer error: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to summarize the article. The website might be blocking automated access.'}), 500
"""

# Insert before @app.route('/api/contact', methods=['POST'])
if "@app.route('/api/contact', methods=['POST'])" in code:
    code = code.replace("@app.route('/api/contact', methods=['POST'])", endpoint_code + "\n@app.route('/api/contact', methods=['POST'])")
else:
    print("Could not find insertion point!")

with open('web_server.py', 'w', encoding='utf-8') as f:
    f.write(code)
