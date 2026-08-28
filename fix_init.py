import os

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the beginning and end of init_database
old_init = '''    def init_database(self):
        if not getattr(self, 'conn', None):
            return
        conn = self.conn
        cursor = conn.cursor()'''

new_init = '''    def init_database(self):
        conn = safe_connect()
        cursor = conn.cursor()'''

content = content.replace(old_init, new_init)

# Now we need to make sure conn.commit() and conn.close() are called at the end of init_database
# It's a huge function, let's find the end of it.
import re
end_pattern = r"            user_message TEXT,\n            ai_response TEXT,\n            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\)'\)\n\n        self\._ensure_table_columns"
end_replacement = "            user_message TEXT,\n            ai_response TEXT,\n            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')\n\n        conn.commit()\n        conn.close()\n\n        self._ensure_table_columns"

content = re.sub(end_pattern, end_replacement, content)

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed init_database")
