import os

with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

schema_markup = '''
  <meta name="keywords" content="Nova Brief, Nova OS, AI News, Student Programs, Tech Certifications, Agentic AI, Autonomous SaaS, Syed Ali Hussain">
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "Nova Brief",
    "alternateName": "Nova OS AI",
    "url": "https://novabrief-web.onrender.com/",
    "potentialAction": {
      "@type": "SearchAction",
      "target": "https://novabrief-web.onrender.com/blog?q={search_term_string}",
      "query-input": "required name=search_term_string"
    }
  }
  </script>
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Nova Brief",
    "url": "https://novabrief-web.onrender.com/",
    "logo": "https://novabrief-web.onrender.com/static/logo.jpg",
    "founder": {
      "@type": "Person",
      "name": "Syed Ali Hussain"
    },
    "sameAs": [
      "https://x.com/Syedali6160",
      "https://www.linkedin.com/in/ali-hussain-93a24430a/"
    ]
  }
  </script>
'''

if 'application/ld+json' not in content:
    content = content.replace('</head>', f'{schema_markup}\n</head>')
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Schema added to index.html")
else:
    print("Schema already exists.")
