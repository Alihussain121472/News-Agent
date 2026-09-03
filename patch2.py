import re
with open("web_server.py", "r", encoding="utf-8") as f:
    content = f.read()

old_register = """    _safe_add_recipient(email)
    session.clear()"""

new_register = """    _safe_add_recipient(email)
    
    def _bg_welcome():
        from ai_news_agent import send_welcome_to_registered_users
        send_welcome_to_registered_users()
    import threading
    threading.Thread(target=_bg_welcome).start()
    
    session.clear()"""

content = content.replace(old_register, new_register)
with open("web_server.py", "w", encoding="utf-8") as f:
    f.write(content)
