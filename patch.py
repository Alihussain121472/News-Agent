import re

with open("web_server.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace subscribe_public
old_subscribe = """    account_result = db.create_or_update_user_account(email, name)
    user_record = db.get_user_by_email(email) or {}
    
    welcome_sent = False
    try:
        if not user_record.get('welcome_email_sent_at'):
            from ai_news_agent import send_welcome_email
            welcome_sent = send_welcome_email(email, name)
            if welcome_sent:
                db.mark_welcome_email_sent(email)
                db.log_email_sent(email, 'Welcome to Nova Brief', 0, 'success')
            else:
                db.log_email_sent(email, 'Welcome to Nova Brief', 0, 'failed', 'SMTP delivery failed')
    except Exception as e:
        logger.error(f'Error sending subscription welcome email: {e}')
    
    return jsonify({
        'status': 'success',
        'message': f'Welcome, {name}! You are subscribed. Sign in separately to access your dashboard.',
        'already_registered': account_result == 'updated',
        'welcome_email_sent': welcome_sent,"""

new_subscribe = """    account_result = db.create_or_update_user_account(email, name)
    user_record = db.get_user_by_email(email) or {}
    
    def _bg_welcome():
        try:
            if not user_record.get('welcome_email_sent_at'):
                from ai_news_agent import send_welcome_email
                if send_welcome_email(email, name):
                    db.mark_welcome_email_sent(email)
                    db.log_email_sent(email, 'Welcome to Nova Brief', 0, 'success')
                else:
                    db.log_email_sent(email, 'Welcome to Nova Brief', 0, 'failed', 'SMTP delivery failed')
        except Exception as e:
            logger.error(f'Error sending subscription welcome email: {e}')
    import threading
    threading.Thread(target=_bg_welcome).start()
    
    return jsonify({
        'status': 'success',
        'message': f'Welcome, {name}! You are subscribed. Sign in separately to access your dashboard.',
        'already_registered': account_result == 'updated',
        'welcome_email_sent': True,"""

content = content.replace(old_subscribe, new_subscribe)

# Replace join_program_alert
old_program = """    _safe_add_recipient(email)
    db.enable_user_program_notifications(email, name)
    db.log_user_activity(email, 'joined_program_alerts', f'Joined alerts for {program_title or "all programs"}')
    
    welcome_sent = False
    try:
        from ai_news_agent import send_program_welcome_email
        welcome_sent = send_program_welcome_email(email, name, program_title)
        if welcome_sent:
            db.log_email_sent(email, 'Program Alerts Activated', 0, 'success')
        else:
            db.log_email_sent(email, 'Program Alerts Activated', 0, 'failed', 'SMTP delivery failed')
    except Exception as e:
        logger.error(f'Error sending program alert welcome email: {e}')
    
    return jsonify({
        'status': 'success',
        'message': 'You have been added to the elite program early alert list.',
        'welcome_email_sent': welcome_sent,"""

new_program = """    _safe_add_recipient(email)
    db.enable_user_program_notifications(email, name)
    db.log_user_activity(email, 'joined_program_alerts', f'Joined alerts for {program_title or "all programs"}')
    
    def _bg_program():
        try:
            from ai_news_agent import send_program_welcome_email
            if send_program_welcome_email(email, name, program_title):
                db.log_email_sent(email, 'Program Alerts Activated', 0, 'success')
            else:
                db.log_email_sent(email, 'Program Alerts Activated', 0, 'failed', 'SMTP delivery failed')
        except Exception as e:
            logger.error(f'Error sending program alert welcome email: {e}')
    import threading
    threading.Thread(target=_bg_program).start()
    
    return jsonify({
        'status': 'success',
        'message': 'You have been added to the elite program early alert list.',
        'welcome_email_sent': True,"""

content = content.replace(old_program, new_program)

with open("web_server.py", "w", encoding="utf-8") as f:
    f.write(content)
