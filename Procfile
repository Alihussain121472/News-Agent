web: gunicorn web_server:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
release: python -c "from database import NewsDatabase; NewsDatabase().init_database()"
