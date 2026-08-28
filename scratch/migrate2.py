import re

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    out = []
    expect_dict = False
    
    for i, line in enumerate(lines):
        if "import sqlite3" in line:
            line = line.replace("import sqlite3", "import psycopg2\nimport psycopg2.extras\nimport os")
            
        if "sqlite3.connect" in line:
            line = line.replace("sqlite3.connect(self.db_path)", "psycopg2.connect(os.getenv('DATABASE_URL'))")
            line = line.replace("sqlite3.connect(db.db_path)", "psycopg2.connect(os.getenv('DATABASE_URL'))")
            expect_dict = False  # Reset on new connection
            
        if "conn.row_factory = sqlite3.Row" in line:
            expect_dict = True
            continue # Remove line
            
        if "conn.cursor()" in line:
            if expect_dict:
                line = line.replace("conn.cursor()", "conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)")
            
        # Syntax replacements
        line = line.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        line = line.replace("BOOLEAN DEFAULT 1", "BOOLEAN DEFAULT TRUE")
        line = line.replace("BOOLEAN DEFAULT 0", "BOOLEAN DEFAULT FALSE")
        line = line.replace("sqlite3.IntegrityError", "psycopg2.IntegrityError")
        
        if any(kw in line for kw in ['execute', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WHERE', 'VALUES', 'SET ']):
            if '"?' not in line and '?' in line:
                if 'url=' not in line and '/?' not in line:
                    line = line.replace('?', '%s')
                    
        out.append(line)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(out)

process_file('database.py')
process_file('web_server.py')
process_file('ai_news_agent.py')
process_file('growth_seo_agent/routes.py')
print("Done")
