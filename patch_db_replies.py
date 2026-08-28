import os

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_func = '''    def mark_message_replied(self, msg_id: int, reply_text: str = None):
        conn = safe_connect()
        cursor = conn.cursor()
        if reply_text:
            cursor.execute("UPDATE contact_messages SET status='replied', admin_reply=%s, replied_at=CURRENT_TIMESTAMP WHERE id=%s", (reply_text, msg_id))
        else:
            cursor.execute("UPDATE contact_messages SET status='replied' WHERE id=%s", (msg_id,))
        conn.commit()
        conn.close()'''

new_func = '''    def mark_message_replied(self, msg_id: int, reply_text: str = None):
        conn = safe_connect()
        cursor = conn.cursor()
        if reply_text:
            cursor.execute("UPDATE contact_messages SET status='replied', admin_reply = CASE WHEN admin_reply IS NULL OR admin_reply = '' THEN %s ELSE admin_reply || '\n\n---\n\n' || %s END, replied_at=CURRENT_TIMESTAMP WHERE id=%s", (reply_text, reply_text, msg_id))
        else:
            cursor.execute("UPDATE contact_messages SET status='replied' WHERE id=%s", (msg_id,))
        conn.commit()
        conn.close()'''

content = content.replace(old_func, new_func)

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated database.py to append replies")
