import os

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix _ensure_table_columns for PostgreSQL
old_ensure = '''    def _ensure_table_columns(self, conn, table_name: str, columns: List[str]) -> None:
        cursor = conn.cursor()
        cursor.execute(f'PRAGMA table_info({table_name})')
        existing = {row[1] for row in cursor.fetchall()}
        for column in columns:
            column_name = column.split()[0].strip()
            if column_name not in existing:
                cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column}')
                logger.info(f'Added missing column {column_name} to {table_name}')'''

new_ensure = '''    def _ensure_table_columns(self, conn, table_name: str, columns: List[str]) -> None:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table_name,))
            existing = {row[0] for row in cursor.fetchall()} if hasattr(cursor, 'fetchall') else set()
            for column in columns:
                column_name = column.split()[0].strip()
                if column_name not in existing:
                    cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column}')
                    logger.info(f'Added missing column {column_name} to {table_name}')
        except Exception as e:
            logger.error(f'Error ensuring columns: {e}')'''

content = content.replace(old_ensure, new_ensure)

# Fix the conn.close() position in init_database
content = content.replace("conn.commit()\n        conn.close()\n\n        self._ensure_table_columns", "self._ensure_table_columns")
content = content.replace("        conn.commit()\n        logger.info('Database initialized successfully.')", "        conn.commit()\n        conn.close()\n        logger.info('Database initialized successfully.')")

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed _ensure_table_columns and connection handling.")
