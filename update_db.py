import os

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_methods = '''    def get_contact_message(self, msg_id: int):
        conn = safe_connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM contact_messages WHERE id=%s", (msg_id,))
        row = to_dict(cursor.fetchone())
        conn.close()
        return row

    def mark_message_replied(self, msg_id: int):
        conn = safe_connect()
        cursor = conn.cursor()
        cursor.execute("UPDATE contact_messages SET status='replied' WHERE id=%s", (msg_id,))
        conn.commit()
        conn.close()
'''

content = content.replace("def mark_message_read(self, msg_id: int):", new_methods + "\n    def mark_message_read(self, msg_id: int):")

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated database.py")
