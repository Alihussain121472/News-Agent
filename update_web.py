import re

with open('web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_endpoint = """
@app.route('/api/summarize-news', methods=['POST'])
def summarize_news():
    data = request.get_json() or {}
    articles = data.get('articles', [])
    if not articles:
        return jsonify({'status': 'error', 'message': 'No articles selected.'}), 400

    import os
    import requests
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        return jsonify({'status': 'error', 'message': 'AI Summarization is currently unavailable (Missing API Key).'}), 503

    prompt = "You are a professional Tech News Summarizer for Nova Brief. Read the following selected tech news articles and provide a highly readable, cohesive executive summary. Group similar topics if necessary. Use markdown bullet points and bold text for emphasis. Do not include introductory fluff, just deliver the professional summary.\\n\\n"
    for i, a in enumerate(articles, 1):
        prompt += f"Article {i}: {a.get('title')}\\nSummary: {a.get('summary')}\\n\\n"

    try:
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Please generate the professional summary now."}
            ],
            "temperature": 0.5,
            "max_tokens": 1024
        }
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        reply = resp.json()['choices'][0]['message']['content']
        return jsonify({'status': 'success', 'summary': reply})
    except Exception as e:
        logger.error(f'Summarization error: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to generate summary.'}), 500
"""

# Insert before handle_ai_chat
text = text.replace("@app.route('/api/chat', methods=['POST'])", new_endpoint + "\n@app.route('/api/chat', methods=['POST'])")

with open('web_server.py', 'w', encoding='utf-8') as f:
    f.write(text)
