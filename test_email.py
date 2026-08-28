import os
from dotenv import load_dotenv
load_dotenv()
import ai_news_agent
print('Sending email...')
ai_news_agent.send_welcome_email('test12345@example.com', 'Test User')
print('Done!')
