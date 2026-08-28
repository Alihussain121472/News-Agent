import os

with open('growth_seo_agent/routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_prompt = '''        prompt = f"""
You are an elite, highly experienced SEO Agent and Content Strategist for 'Nova Brief' (a tech, AI, and student program alert platform).
Your primary goal is to help Nova Brief outrank competitors (especially 'Novobrief') on Google, and ensure Nova Brief appears in the top 5 search results with its official logo and rich snippets.

The user wants to target the following topic/keyword: "{keyword}"

Please generate a comprehensive, highly optimized SEO strategy in markdown format.
Since 'Novobrief' dominates the short-tail keyword, heavily emphasize long-tail variations like 'Nova Brief AI', 'Nova Brief Tech News', and 'Nova Brief Student Programs'.

Structure your response exactly like this:

### 🎯 Primary & Secondary Keywords
List the absolute best primary keyword and 5 high-converting, low-competition secondary/long-tail keywords. Explain why these keywords will bypass the current 'Novobrief' competitor and rank easily.

### 📝 Title Tag & Meta Description
Provide the exact, click-optimized <title> and <meta name="description"> HTML tags the user should use on their website.

### 🖼️ Schema & Logo Visibility Strategy
Explain in 2 sentences how the user can force Google to show their Logo in search results (hint: Schema.org Organization markup and Google Search Console indexing).

### ✍️ Content Strategy
Suggest 3 specific, high-value blog post titles that will drive massive targeted traffic to Nova Brief.

Do not include any generic filler text, just the highly professional SEO output.
"""'''

# Find the old prompt block
import re
old_prompt_pattern = r'prompt = f"""(.*?)Do not include any generic filler text, just the highly professional SEO output.\n"""'
content = re.sub(old_prompt_pattern, new_prompt.split('prompt = f"""')[1], content, flags=re.DOTALL)

with open('growth_seo_agent/routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated SEO Agent Prompt")
