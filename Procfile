web: gunicorn web_server:app --bind 0.0.0.0:$PORT --workers 2 --threads 8 --timeout 180 --preload
release: python -c "from database import NewsDatabase; NewsDatabase().init_database()"
