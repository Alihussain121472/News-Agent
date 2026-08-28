import re

with open('social_media_agent/routes.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace Gemini usage with Groq usage
old_ai_block = '''        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = """You are an expert Social Media Manager for 'Nova Brief', a top-tier tech platform that provides daily AI news and alerts for prestigious student programs (Google, Microsoft, NASA).
            Your goal is to increase our Twitter reach, engagement, and conversion rate.
            Write 3 highly engaging, viral-style Twitter posts. 
            Rules:
            1. Use strong hooks.
            2. Be professional yet punchy.
            3. Use 2-3 relevant hashtags.
            4. Include a call to action to subscribe or visit novabrief.com.
            5. Base at least one post on the following recent news if available:
            """ + news_context + """
            Format your response strictly as 3 posts separated by '|||'. Do not include post numbers or extra text.
            """
            
            response = model.generate_content(prompt)
            raw_posts = response.text.split('|||')
            posts = [p.strip() for p in raw_posts if p.strip()]'''

new_ai_block = '''        # Use Groq Llama 3.3 API
        groq_api_key = os.getenv('GROQ_API_KEY')
        if groq_api_key:
            import requests
            prompt = """You are an expert Social Media Manager for 'Nova Brief', a top-tier tech platform that provides daily AI news and alerts for prestigious student programs (Google, Microsoft, NASA).
            Your goal is to increase our Twitter reach, engagement, and conversion rate.
            Write 3 highly engaging, viral-style Twitter posts. 
            Rules:
            1. Use strong hooks.
            2. Be professional yet punchy.
            3. Use 2-3 relevant hashtags.
            4. Include a call to action to subscribe or visit novabrief.com.
            5. Base at least one post on the following recent news if available:
            """ + news_context + """
            Format your response strictly as 3 posts separated by '|||'. Do not include post numbers or extra text.
            """
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 500
            }
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
            if response.status_code == 200:
                reply_text = response.json()['choices'][0]['message']['content']
                raw_posts = reply_text.split('|||')
                posts = [p.strip() for p in raw_posts if p.strip()]
            else:
                posts = []'''

text = text.replace(old_ai_block, new_ai_block)
text = text.replace("import google.generativeai as genai", "")
text = text.replace("api_key = os.getenv('GEMINI_API_KEY')", "")

with open('social_media_agent/routes.py', 'w', encoding='utf-8') as f:
    f.write(text)
