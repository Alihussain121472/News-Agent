import os
import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Contact Section
contact_twitter = '''          <div class="flex items-center gap-4 mt-6">
            <div class="w-12 h-12 rounded-xl bg-blue-700/20 flex items-center justify-center flex-shrink-0">
              <i class="fab fa-linkedin text-blue-500"></i>
            </div>
            <div>
              <div class="text-sm font-bold text-white mb-1">LinkedIn</div>
              <a href="https://www.linkedin.com/in/ali-hussain-93a24430a/" target="_blank" class="text-slate-400 hover:text-blue-500 transition text-sm">Ali Hussain</a>
            </div>
          </div>'''

new_contact_twitter = contact_twitter + '''
          <div class="flex items-center gap-4 mt-6">
            <div class="w-12 h-12 rounded-xl bg-sky-500/20 flex items-center justify-center flex-shrink-0">
              <i class="fab fa-twitter text-sky-400"></i>
            </div>
            <div>
              <div class="text-sm font-bold text-white mb-1">Nova Brief Updates</div>
              <a href="https://x.com/Novabrieftech" target="_blank" class="text-slate-400 hover:text-sky-400 transition text-sm">@Novabrieftech</a>
            </div>
          </div>'''

content = content.replace(contact_twitter, new_contact_twitter)

# 2. Update Footer Section
footer_links = '''<a href="https://x.com/Syedali6160" target="_blank" class="w-8 h-8 bg-slate-900/70 backdrop-blur-md border border-slate-400/15 rounded-lg flex items-center justify-center text-slate-400 hover:text-blue-400 transition"><i class="fab fa-twitter text-xs"></i></a>
            <a href="https://www.linkedin.com/in/ali-hussain-93a24430a/" target="_blank" class="w-8 h-8 bg-slate-900/70 backdrop-blur-md border border-slate-400/15 rounded-lg flex items-center justify-center text-slate-400 hover:text-blue-600 transition"><i class="fab fa-linkedin text-xs"></i></a>'''

new_footer_links = '''<a href="https://x.com/Syedali6160" target="_blank" title="Creator Twitter" class="w-8 h-8 bg-slate-900/70 backdrop-blur-md border border-slate-400/15 rounded-lg flex items-center justify-center text-slate-400 hover:text-blue-400 transition"><i class="fab fa-twitter text-xs"></i></a>
            <a href="https://x.com/Novabrieftech" target="_blank" title="Nova Brief Updates" class="w-8 h-8 bg-slate-900/70 backdrop-blur-md border border-slate-400/15 rounded-lg flex items-center justify-center text-slate-400 hover:text-blue-400 transition"><i class="fab fa-twitter text-xs"></i></a>
            <a href="https://www.linkedin.com/in/ali-hussain-93a24430a/" target="_blank" title="LinkedIn" class="w-8 h-8 bg-slate-900/70 backdrop-blur-md border border-slate-400/15 rounded-lg flex items-center justify-center text-slate-400 hover:text-blue-600 transition"><i class="fab fa-linkedin text-xs"></i></a>'''

if 'https://x.com/Novabrieftech' not in content:
    content = content.replace(footer_links, new_footer_links)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated index.html with new Twitter links")
