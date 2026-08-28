import os

with open('analytics_revenue_portal/templates/messages.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix openMessage
old_open_msg = '''    if (replyText && replyText !== "None" && replyText.trim() !== "") {
        document.getElementById('reply-history-section').style.display = 'flex';
        document.getElementById('view-reply-text').textContent = replyText;
        document.getElementById('view-reply-date').textContent = " - " + replyDate.substring(0,16);
        document.getElementById('reply-action-section').style.display = 'none';
    } else {
        document.getElementById('reply-history-section').style.display = 'none';
        document.getElementById('reply-action-section').style.display = 'block';
    }'''

new_open_msg = '''    if (replyText && replyText !== "None" && replyText.trim() !== "") {
        document.getElementById('reply-history-section').style.display = 'flex';
        document.getElementById('view-reply-text').textContent = replyText;
        document.getElementById('view-reply-date').textContent = " - " + replyDate.substring(0,16);
        document.getElementById('reply-action-section').style.display = 'block';
    } else {
        document.getElementById('reply-history-section').style.display = 'none';
        document.getElementById('reply-action-section').style.display = 'block';
    }'''
content = content.replace(old_open_msg, new_open_msg)

# Fix sendReply success block
old_success = '''            // Show history block
            document.getElementById('reply-history-section').style.display = 'flex';
            document.getElementById('view-reply-text').textContent = text;
            const now = new Date();
            document.getElementById('view-reply-date').textContent = "Just now";
            document.getElementById('reply-action-section').style.display = 'none';'''

new_success = '''            // Show history block
            const historySec = document.getElementById('reply-history-section');
            const viewText = document.getElementById('view-reply-text');
            if (historySec.style.display === 'none') {
                viewText.textContent = text;
            } else {
                viewText.textContent += '\\n\\n---\\n\\n' + text;
            }
            historySec.style.display = 'flex';
            document.getElementById('view-reply-date').textContent = "Just now";
            document.getElementById('reply-action-section').style.display = 'block';'''
content = content.replace(old_success, new_success)

# Update the button text slightly to indicate multiple replies
content = content.replace('<i class="fas fa-reply group-hover:-translate-x-1 transition-transform"></i> Click here to write a reply', '<i class="fas fa-reply group-hover:-translate-x-1 transition-transform"></i> Write a reply')


with open('analytics_revenue_portal/templates/messages.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated messages.html to allow permanent replies")
