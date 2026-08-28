import os

with open('growth_seo_agent/routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_prompt_marker = 'Generate an SEO optimization plan'
if old_prompt_marker in content:
    print("Found old prompt.")
    
# Let's completely rewrite the prompt logic to inject high CPC and backlinks.
# Actually I'll just use regex to replace the prompt block.
import re
new_prompt = '''prompt = f"""
You are an elite Enterprise SEO Strategist for 'Nova Brief' (novabrief.tech).
The user wants to outrank competitors despite a Keyword Difficulty of 48% and maximize CPC (Cost Per Click).

Topic: {topic}

Please generate a highly structured SEO Content Draft that includes:
1. **High CPC Target Keywords:** List 5-10 long-tail keywords with high commercial intent and low-to-medium KD.
2. **Optimized Meta Tags:** Title (under 60 chars) and Description (under 160 chars) packed with high CPC terms.
3. **Internal Backlink Strategy:** Specify exactly which pages on the Nova Brief website should link to this article to spread PageRank.
4. **Outbound Backlink Strategy:** Suggest 3 high-authority domains (e.g., Google Scholar, AWS Docs) to link OUT to, which increases Google's trust in this content.
5. **Content Outline (Semantic HTML):** Provide a highly structured H1, H2, H3 hierarchy optimized for Google Featured Snippets.

Do not include any generic filler text, just the highly professional SEO output in Markdown.
"""'''

content = re.sub(r'prompt = f"""[\s\S]*?Do not include any generic filler text, just the highly professional SEO output\.\s*"""', new_prompt, content)

with open('growth_seo_agent/routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated SEO Agent Prompt")
