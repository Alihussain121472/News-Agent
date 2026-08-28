import os
import re

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add is_active to registered_users and student_programs
content = content.replace("role TEXT DEFAULT 'user', program_notifications BOOLEAN DEFAULT TRUE)", "role TEXT DEFAULT 'user', program_notifications BOOLEAN DEFAULT TRUE, is_active BOOLEAN DEFAULT TRUE)")
content = content.replace("launch_date DATE,\n            created_at TIMESTAMP", "launch_date DATE,\n            is_active BOOLEAN DEFAULT TRUE,\n            created_at TIMESTAMP")

# 2. Fix all instances of is_active=1 and is_active=0
content = content.replace("is_active=1", "is_active=TRUE")
content = content.replace("is_active=0", "is_active=FALSE")
content = content.replace("is_active,role,password_hash) VALUES (%s,%s,1,'user',%s)", "is_active,role,password_hash) VALUES (%s,%s,TRUE,'user',%s)")

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed PostgreSQL boolean syntax and missing is_active columns")
