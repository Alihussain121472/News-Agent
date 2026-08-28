import os
import re

with open('analytics_revenue_portal/templates/messages.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Pass admin_reply and replied_at to openMessage
content = content.replace(
    '''onclick="openMessage({{ msg.id }}, '{{ msg.name|e }}', '{{ msg.email|e }}', '{{ msg.subject|e }}', '{{ msg.submitted_at|e }}', this)"''',
    '''onclick="openMessage({{ msg.id }}, '{{ msg.name|e }}', '{{ msg.email|e }}', '{{ msg.subject|e }}', '{{ msg.submitted_at|e }}', '{{ msg.admin_reply|default('')|e }}', '{{ msg.replied_at|default('')|e }}', this)"'''
)

# Update openMessage signature
content = content.replace(
    'function openMessage(id, name, email, subject, date, element) {',
    'function openMessage(id, name, email, subject, date, replyText, replyDate, element) {'
)

# Render reply history in the HTML
reply_history_html = '''            <div class="mt-8 pt-6 border-t border-slate-100" id="reply-history-section" style="display: none;">
                <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Reply History</h4>
                <div class="bg-blue-50 border border-blue-100 rounded-xl p-4">
                    <div class="flex justify-between items-center mb-2">
                        <span class="font-bold text-sm text-blue-900">Nova Admin</span>
                        <span class="text-[10px] text-blue-400 font-semibold" id="view-reply-date"></span>
                    </div>
                    <div class="text-sm text-blue-800 whitespace-pre-wrap" id="view-reply-text"></div>
                </div>
            </div>
            
            <div class="mt-8 pt-6 border-t border-slate-100" id="reply-action-section">'''

content = content.replace('            <div class="mt-8 pt-6 border-t border-slate-100">', reply_history_html, 1)

# Modify JS to handle the new fields
js_update = '''    const content = element.getAttribute('data-content');
    document.getElementById('view-body').textContent = content;
    
    if (replyText) {
        document.getElementById('reply-history-section').style.display = 'block';
        document.getElementById('view-reply-text').textContent = replyText;
        document.getElementById('view-reply-date').textContent = replyDate.substring(0,16);
        document.getElementById('reply-action-section').style.display = 'none';
    } else {
        document.getElementById('reply-history-section').style.display = 'none';
        document.getElementById('reply-action-section').style.display = 'block';
    }'''

content = content.replace('''    const content = element.getAttribute('data-content');
    document.getElementById('view-body').textContent = content;''', js_update)

with open('analytics_revenue_portal/templates/messages.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated messages.html")
