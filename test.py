import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the space-y-3 block for live feed
pattern = r'<div class="space-y-3">.*?</div>\s*</div>\s*</div>\s*</div>\s*</div>\s*</div>'
match = re.search(r'<div class="space-y-3">.*?(?=</section>)', text, re.DOTALL)
if match:
    pass

# Let's just find the exact block and replace it using a script
