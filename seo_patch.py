import os
import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Enhance SEO Title and Description for High CPC
html = re.sub(
    r'<title>.*?</title>',
    '<title>Nova Brief | Leading AI News & Elite Tech Student Programs (Google, AWS, Meta)</title>',
    html, flags=re.IGNORECASE
)

html = re.sub(
    r'<meta name="description" content=".*?"/>',
    '<meta name="description" content="Discover breaking Enterprise AI news, Machine Learning tools, and exclusive student internship alerts for Google, Microsoft, and Meta. High CPC tech insights."/>',
    html, flags=re.IGNORECASE
)

html = re.sub(
    r'<meta name="keywords" content=".*?"',
    '<meta name="keywords" content="Enterprise AI tools, Machine learning certifications, Tech student internships 2026, SaaS automation, AI news API, Nova Brief, Tech career growth, Cloud computing programs"',
    html, flags=re.IGNORECASE
)

# Add JSON-LD Rich Snippets for FAQ (Massive SEO Boost)
faq_schema = '''
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {
          "@type": "Question",
          "name": "How does Nova Brief track AI tools and student programs?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Nova Brief uses autonomous AI agents to scrape and aggregate enterprise AI news, machine learning tools, and exclusive student internships from Google, AWS, and Meta."
          }
        },
        {
          "@type": "Question",
          "name": "What tech companies are included in the internship alerts?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "We provide direct application links and deadlines for top-tier companies including Google, Microsoft, Amazon AWS, Meta, Apple, IBM, and NASA."
          }
        }
      ]
    }
    </script>
'''

html = html.replace('</head>', faq_schema + '\n</head>')

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated On-Page SEO")
