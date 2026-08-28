import re

with open('templates/user_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("World Top Tech Articles", "Global Technology Intelligence")
text = text.replace("Applied Programs", "Active Program Applications")
text = text.replace("You didn't apply in any program yet.", "No active program applications detected.")
text = text.replace("Apply to a Program", "Submit Program Application")
text = text.replace("No articles fetched yet. System updates hourly.", "Intelligence feed pending. System synchronizes globally every hour.")

with open('templates/user_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
