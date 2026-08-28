import re
with open('database.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the broken multiline string
old_str = """cursor.execute("UPDATE contact_messages SET status='replied', admin_reply = CASE WHEN admin_reply IS NULL OR admin_reply = '' THEN %s ELSE admin_reply || '

---

' || %s END, replied_at=CURRENT_TIMESTAMP WHERE id=%s", (reply_text, reply_text, msg_id))"""

new_str = """cursor.execute('''UPDATE contact_messages SET status='replied', admin_reply = CASE WHEN admin_reply IS NULL OR admin_reply = '' THEN %s ELSE admin_reply || '\n\n---\n\n' || %s END, replied_at=CURRENT_TIMESTAMP WHERE id=%s''', (reply_text, reply_text, msg_id))"""

text = text.replace(old_str, new_str)
with open('database.py', 'w', encoding='utf-8') as f:
    f.write(text)
