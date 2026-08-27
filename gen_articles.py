import os
import psycopg2
import markdown

with open('.env', 'r') as f:
    for line in f:
        if '=' in line:
            k, v = line.strip().split('=', 1)
            os.environ[k] = v

from database import safe_connect
import requests
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


articles = [
    {
        'slug': 'top-5-student-automation-tools-2026',
        'title': 'Top 5 Student Automation Tools in 2026: Skyrocket Your Productivity',
        'prompt': 'Write a comprehensive 1000-word SEO article about the "Top 5 Student Automation Tools in 2026". Include how Nova Brief tracks student programs automatically. Output in Markdown.'
    },
    {
        'slug': 'how-to-automate-internship-search',
        'title': 'How to Automate Your Tech Internship Search: The Ultimate Student Guide',
        'prompt': 'Write a 1000-word SEO article about "How to Automate Your Tech Internship Search" focusing on student automation tools. Mention Google, AWS, and Meta. Output in Markdown.'
    }
]

conn = safe_connect()
cursor = conn.cursor()

for a in articles:
    print(f"Generating: {a['title']}")
    response = model.generate_content(a['prompt'])
    html_content = markdown.markdown(response.text)
    
    # Styled HTML wrapper
    final_html = f'''
    <div class="prose prose-slate max-w-none text-slate-700">
        {html_content.replace('h3', 'h3 class="text-xl font-bold text-slate-800 mt-8 mb-4"').replace('h2', 'h2 class="text-2xl font-bold text-blue-700 mt-10 mb-6"').replace('p', 'p class="leading-relaxed mb-6"')}
    </div>
    '''
    
    try:
        cursor.execute('''
        INSERT INTO blog_articles (slug, title, content, meta_description, keywords)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (slug) DO NOTHING;
        ''', (a['slug'], a['title'], final_html, 'Learn about the best student automation tools in 2026 to boost your productivity and land top tech internships.', 'student automation tools, tech internships, nova brief, productivity'))
        conn.commit()
        print("Inserted.")
    except Exception as e:
        print(f"DB Error: {e}")
        conn.rollback()

conn.close()
print("Done.")
