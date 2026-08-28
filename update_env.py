import os

with open('.env', 'r', encoding='utf-8') as f:
    content = f.read()

import re
content = re.sub(r'DATABASE_URL=.*', 'DATABASE_URL=postgresql://postgres.qgueetgopiidzuqrzznz:Alihussain110%40@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres', content)

with open('.env', 'w', encoding='utf-8') as f:
    f.write(content)
