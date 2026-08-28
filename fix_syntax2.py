import re
with open('database.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("'SELECT COUNT(*) FROM email_logs WHERE recipient=%s AND status='success''", "\"SELECT COUNT(*) FROM email_logs WHERE recipient=%s AND status='success'\"")
text = text.replace("AND e.status='success') AS emails_received", "AND e.status=''success'') AS emails_received")
text = text.replace("'SELECT COUNT(*) FROM email_logs WHERE status='success''", "\"SELECT COUNT(*) FROM email_logs WHERE status='success'\"")

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(text)
