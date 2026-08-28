import os
import re

with open('analytics_revenue_portal/routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_logic = '''    success = send_email(msg['email'], subject, html)
    if success:
        db.mark_message_replied(msg_id)
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to send email. Check SMTP settings.'}), 500'''

new_logic = '''    success = send_email(msg['email'], subject, html)
    db.mark_message_replied(msg_id, reply_text)
    if success:
        return jsonify({'status': 'success', 'message': 'Reply sent and saved to history!'})
    else:
        return jsonify({'status': 'success', 'message': 'Reply saved to history, but email failed to send (Check SMTP).'})'''

content = content.replace(old_logic, new_logic)

with open('analytics_revenue_portal/routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated routes.py")
