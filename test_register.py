import database
db = database.NewsDatabase()
try:
    print(db.create_or_update_user_account('test12345@example.com', 'Test User', 'hash123'))
except Exception as e:
    import traceback
    traceback.print_exc()
