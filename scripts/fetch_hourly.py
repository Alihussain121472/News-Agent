def fetch_latest_news_hourly() -> int:
    logger.info('Starting hourly news fetch...')
    db = NewsDatabase()
    news_items = search_ai_news(limit=5)
    if news_items:
        db.save_news_batch(news_items)
        db.log_agent_event('hourly_fetch', f'Fetched and saved {len(news_items)} new articles')
        return len(news_items)
    return 0
