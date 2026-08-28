import re

with open('analytics_revenue_portal/templates/messages.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Make "Write a reply" more professional
text = text.replace("Write a reply", "Compose Official Response")

# Also, there's a button "Send Reply Now" in there somewhere, let's find it.
text = text.replace("Send Reply Now", "Dispatch Official Response")

with open('analytics_revenue_portal/templates/messages.html', 'w', encoding='utf-8') as f:
    f.write(text)
