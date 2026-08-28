import os
import re

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_func = '''    def mark_message_replied(self, msg_id: int):
        conn = safe_connect()
        cursor = conn.cursor()
        cursor.execute("UPDATE contact_messages SET status='replied' WHERE id=%s", (msg_id,))
        conn.commit()
        conn.close()'''

new_func = '''    def mark_message_replied(self, msg_id: int, reply_text: str = None):
        conn = safe_connect()
        cursor = conn.cursor()
        if reply_text:
            cursor.execute("UPDATE contact_messages SET status='replied', admin_reply=%s, replied_at=CURRENT_TIMESTAMP WHERE id=%s", (reply_text, msg_id))
        else:
            cursor.execute("UPDATE contact_messages SET status='replied' WHERE id=%s", (msg_id,))
        conn.commit()
        conn.close()'''

content = content.replace(old_func, new_func)

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated mark_message_replied in database.py")
