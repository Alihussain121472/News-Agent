import os
import re

with open('analytics_revenue_portal/templates/messages.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the overlapping empty state
old_empty = '''        <!-- Empty State -->
        <div id="empty-state" class="absolute inset-0 flex flex-col items-center justify-center text-slate-400 bg-slate-50 z-10">'''
new_empty = '''        <!-- Empty State -->
        <div id="empty-state" class="flex-1 flex flex-col items-center justify-center text-slate-400 bg-slate-50">'''

old_active = '''        <!-- Active View -->
        <div class="p-6 border-b border-slate-100 flex justify-between items-start">'''
new_active = '''        <!-- Active View -->
        <div id="active-view" class="hidden flex-col h-full">
        <div class="p-6 border-b border-slate-100 flex justify-between items-start">'''

content = content.replace('id="message-view"', 'id="message-view-container"')
content = content.replace(old_empty, new_empty)
content = content.replace(old_active, new_active)
content = content.replace('</div>\n</div>\n\n<script>', '</div>\n</div>\n</div>\n\n<script>')

content = content.replace("document.getElementById('empty-state').style.display = 'none';", "document.getElementById('empty-state').style.display = 'none';\n    document.getElementById('active-view').style.display = 'flex';")

with open('analytics_revenue_portal/templates/messages.html', 'w', encoding='utf-8') as f:
    f.write(content)
