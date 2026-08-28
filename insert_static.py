import os
import psycopg2
from database import safe_connect

articles = [
    {
        'slug': 'student-automation-tools-2026',
        'title': 'The Ultimate Guide to Student Automation Tools in 2026',
        'content': '''<div class="prose prose-slate max-w-none text-slate-700">
<p class="leading-relaxed mb-6">As students navigate an increasingly competitive tech landscape, <strong>student automation tools</strong> have become the secret weapon for securing top-tier internships at companies like Google, AWS, and Meta. In 2026, relying on manual searches is no longer enough.</p>
<h2 class="text-2xl font-bold text-blue-700 mt-10 mb-6">Why Automation is the Future of Tech Internships</h2>
<p class="leading-relaxed mb-6">With hundreds of thousands of applicants vying for limited spots, the students who get hired are the ones who apply first. Automation tools instantly scrape career pages, filter for your specific tech stack, and deliver alerts directly to your inbox.</p>
<h3 class="text-xl font-bold text-slate-800 mt-8 mb-4">How Nova Brief Revolutionizes the Process</h3>
<p class="leading-relaxed mb-6">Nova Brief is at the forefront of this revolution. By employing autonomous Agentic AI, Nova OS constantly monitors enterprise internship portals. Instead of refreshing pages daily, students receive a curated briefing with direct application links the second a program goes live.</p>
</div>''',
        'meta_desc': 'Discover how student automation tools are revolutionizing the 2026 tech internship search. Learn how Nova Brief secures early alerts for Google and Meta programs.',
        'keywords': 'student automation tools, tech internships 2026, AI internship tracker'
    },
    {
        'slug': 'how-to-automate-your-internship-search',
        'title': 'How to Automate Your Internship Search with AI',
        'content': '''<div class="prose prose-slate max-w-none text-slate-700">
<p class="leading-relaxed mb-6">Finding a software engineering internship shouldn't feel like a full-time job. By leveraging modern <strong>student automation tools</strong>, you can let AI do the heavy lifting while you focus on LeetCode and building projects.</p>
<h2 class="text-2xl font-bold text-blue-700 mt-10 mb-6">The Power of AI Alerts</h2>
<p class="leading-relaxed mb-6">Instead of manually checking LinkedIn or Handshake, automation tools scan the web 24/7. When companies like AWS or Meta silently drop new student programs, an AI agent can instantly notify you.</p>
<h3 class="text-xl font-bold text-slate-800 mt-8 mb-4">Action Plan for Students</h3>
<p class="leading-relaxed mb-6">Sign up for automated platforms like Nova Brief. Ensure your resume is ATS-friendly, and be ready to click "Apply" the moment your automated alert arrives. In 2026, speed is just as important as skill.</p>
</div>''',
        'meta_desc': 'Stop searching manually. Learn how to use AI and student automation tools to instantly find software engineering internships before your peers.',
        'keywords': 'student automation tools, AI internship alerts, software engineering internships'
    }
]

with open('.env', 'r') as f:
    for line in f:
        if line.startswith('DATABASE_URL='):
            os.environ['DATABASE_URL'] = line.strip().split('=', 1)[1]

conn = safe_connect()
cursor = conn.cursor()

for a in articles:
    try:
        cursor.execute('''
        INSERT INTO blog_articles (slug, title, content, meta_description, keywords)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (slug) DO NOTHING;
        ''', (a['slug'], a['title'], a['content'], a['meta_desc'], a['keywords']))
        conn.commit()
        print(f"Inserted {a['slug']}")
    except Exception as e:
        print(f"DB Error: {e}")
        conn.rollback()

conn.close()
