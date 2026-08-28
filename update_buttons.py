import re
with open('templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add a "Read News & Articles" button to the homepage
old_buttons = '''<div class="flex flex-wrap gap-4 mt-8">
          <a href="#subscribe" class="inline-flex items-center gap-3 bg-gradient-to-r from-blue-600 to-emerald-500 hover:from-blue-500 hover:to-emerald-400 text-white font-black px-10 py-5 rounded-2xl shadow-[0_0_40px_rgba(37,99,235,0.4)] transition-all hover:scale-105 hover:shadow-[0_0_60px_rgba(52,211,153,0.5)] transform animate-bounce">
            <i class="fas fa-bolt text-yellow-300"></i> Get Started For Free
          </a>
          <a href="/user/register" class="inline-flex items-center gap-2 bg-slate-800/80 backdrop-blur-md border border-slate-400/30 hover:bg-slate-700 hover:border-slate-300 text-white font-bold px-8 py-5 rounded-2xl shadow-lg transition-all hover:-translate-y-1">
            <i class="fas fa-user-plus text-emerald-400"></i> Create Free Account
          </a>
        </div>'''

new_buttons = '''<div class="flex flex-wrap gap-4 mt-8">
          <a href="#subscribe" class="inline-flex items-center gap-3 bg-gradient-to-r from-blue-600 to-emerald-500 hover:from-blue-500 hover:to-emerald-400 text-white font-black px-10 py-5 rounded-2xl shadow-[0_0_40px_rgba(37,99,235,0.4)] transition-all hover:scale-105 hover:shadow-[0_0_60px_rgba(52,211,153,0.5)] transform animate-bounce">
            <i class="fas fa-bolt text-yellow-300"></i> Get Started For Free
          </a>
          <a href="/user/dashboard" class="inline-flex items-center gap-2 bg-slate-800/80 backdrop-blur-md border border-slate-400/30 hover:bg-slate-700 hover:border-slate-300 text-white font-bold px-8 py-5 rounded-2xl shadow-lg transition-all hover:-translate-y-1">
            <i class="fas fa-newspaper text-blue-400"></i> Read Live News
          </a>
          <a href="/user/register" class="inline-flex items-center gap-2 bg-slate-800/80 backdrop-blur-md border border-slate-400/30 hover:bg-slate-700 hover:border-slate-300 text-white font-bold px-8 py-5 rounded-2xl shadow-lg transition-all hover:-translate-y-1">
            <i class="fas fa-user-plus text-emerald-400"></i> Create Account
          </a>
        </div>'''

html = html.replace(old_buttons, new_buttons)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
