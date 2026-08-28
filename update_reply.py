import os
import re

with open('analytics_revenue_portal/templates/messages.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_btn = '''            <div class="mt-8 pt-6 border-t border-slate-100">
                <button class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg text-sm font-semibold transition" onclick="alert('Reply functionality coming soon!')">
                    <i class="fas fa-reply mr-2"></i> Reply to User
                </button>
            </div>'''

new_btn = '''            <div class="mt-8 pt-6 border-t border-slate-100">
                <div id="reply-container" class="hidden flex-col gap-3">
                    <textarea id="reply-text" rows="4" class="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm focus:outline-none focus:border-blue-500 resize-none" placeholder="Type your reply to this user..."></textarea>
                    <div class="flex items-center gap-2">
                        <button id="send-reply-btn" onclick="sendReply()" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-bold transition flex items-center gap-2">
                            <i class="fas fa-paper-plane"></i> Send Reply
                        </button>
                        <button onclick="document.getElementById('reply-container').classList.add('hidden'); document.getElementById('reply-btn-wrapper').classList.remove('hidden');" class="text-slate-500 hover:text-slate-700 text-sm font-semibold px-3 py-2 transition">Cancel</button>
                    </div>
                </div>
                <div id="reply-btn-wrapper">
                    <button class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-2" onclick="document.getElementById('reply-container').classList.remove('hidden'); document.getElementById('reply-btn-wrapper').classList.add('hidden');">
                        <i class="fas fa-reply"></i> Reply to User
                    </button>
                </div>
            </div>'''

content = content.replace(old_btn, new_btn)

js_to_add = '''
async function sendReply() {
    const btn = document.getElementById('send-reply-btn');
    const text = document.getElementById('reply-text').value.trim();
    if(!text) return;
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    
    try {
        const response = await fetch('/analytics/api/messages/' + currentMessageId + '/reply', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ reply: text })
        });
        
        const data = await response.json();
        if(response.ok) {
            alert('Reply sent successfully!');
            document.getElementById('reply-text').value = '';
            document.getElementById('reply-container').classList.add('hidden');
            document.getElementById('reply-btn-wrapper').classList.remove('hidden');
        } else {
            alert('Failed to send reply: ' + data.message);
        }
    } catch (e) {
        alert('An error occurred.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-paper-plane"></i> Send Reply';
    }
}
'''

content = content.replace('function openMessage', 'let currentMessageId = null;\n\n' + js_to_add + '\nfunction openMessage')
content = content.replace('// Hide empty state', '// Hide empty state\n    currentMessageId = id;')

with open('analytics_revenue_portal/templates/messages.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated messages.html with reply form")
