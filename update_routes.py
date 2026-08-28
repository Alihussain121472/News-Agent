import os

with open('analytics_revenue_portal/routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_route = '''
@analytics_bp.route('/api/messages/<int:msg_id>/reply', methods=['POST'])
@admin_required
def reply_msg(msg_id):
    from flask import request
    from ai_news_agent import send_email
    db = NewsDatabase()
    
    data = request.get_json(silent=True) or {}
    reply_text = data.get('reply', '').strip()
    if not reply_text:
        return jsonify({'status': 'error', 'message': 'Reply cannot be empty'}), 400
        
    msg = db.get_contact_message(msg_id)
    if not msg:
        return jsonify({'status': 'error', 'message': 'Message not found'}), 404
        
    subject = f"Re: {msg['subject']}"
    html = f"""<html><body style="font-family:Arial,sans-serif;color:#333;line-height:1.6;">
    <p>Hi {msg['name']},</p>
    <p>{reply_text.replace(chr(10), '<br>')}</p>
    <br>
    <p>Best regards,<br>Nova Admin Team</p>
    <hr style="border:0;border-top:1px solid #eee;margin:20px 0;">
    <p style="color:#888;font-size:12px;">On {msg['submitted_at'][:10]}, you wrote:<br><em>{msg['message']}</em></p>
    </body></html>"""
    
    success = send_email(msg['email'], subject, html)
    if success:
        db.mark_message_replied(msg_id)
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to send email. Check SMTP settings.'}), 500
'''

content = content.replace("def mark_msg_read(msg_id):", new_route + "\ndef mark_msg_read(msg_id):")

with open('analytics_revenue_portal/routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated routes.py")
