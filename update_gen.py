import re

with open('gen_articles.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_gen = '''import requests
groq_api_key = os.environ.get('GROQ_API_KEY')

def generate_with_llama(prompt):
    if not groq_api_key:
        print("No GROQ_API_KEY found")
        return ""
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2048
    }
    response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    print(f"Error {response.status_code}: {response.text}")
    return ""
'''

text = text.replace("import google.generativeai as genai\nfrom database import safe_connect\n\ngenai.configure(api_key=os.environ.get('GEMINI_API_KEY'))\nmodel = genai.GenerativeModel('gemini-pro')", "from database import safe_connect\n" + new_gen)
text = text.replace("response = model.generate_content(prompt)\n        content = response.text", "content = generate_with_llama(prompt)")

with open('gen_articles.py', 'w', encoding='utf-8') as f:
    f.write(text)
