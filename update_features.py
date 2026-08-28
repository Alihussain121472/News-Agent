import re
with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. AI News Daily
old_ai = """<div class="bg-slate-900/70 backdrop-blur-md border border-slate-400/15 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(37,99,235,0.15)]">
        <div class="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center mb-4">
          <i class="fas fa-robot text-blue-400 text-xl"></i>
        </div>
        <h3 class="text-lg font-bold text-white mb-2">AI News Daily</h3>
        <p class="text-slate-400 text-sm leading-relaxed">5 curated AI stories every morning at 8 AM with summaries, why it matters, and what could change.</p>
      </div>"""
new_ai = """<a href="/user/dashboard" class="block bg-slate-900/70 backdrop-blur-md border border-slate-400/15 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(37,99,235,0.15)] hover:border-blue-500/50">
        <div class="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center mb-4">
          <i class="fas fa-robot text-blue-400 text-xl"></i>
        </div>
        <h3 class="text-lg font-bold text-white mb-2">AI News Daily</h3>
      </a>"""
text = text.replace(old_ai, new_ai)

# 2. Student Program Alerts
old_student = """<div class="bg-slate-900/70 backdrop-blur-md border border-emerald-500/20 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(37,99,235,0.15)]">
        <div class="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center mb-4">
          <i class="fas fa-graduation-cap text-emerald-400 text-xl"></i>
        </div>
        <h3 class="text-lg font-bold text-white mb-2">Student Program Alerts</h3>
        <p class="text-slate-400 text-sm leading-relaxed">Early alerts for Google, Microsoft, Amazon, NASA, Deloitte programs - with direct registration links before they go live.</p>
      </div>"""
new_student = """<a href="#programs" class="block bg-slate-900/70 backdrop-blur-md border border-emerald-500/20 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(37,99,235,0.15)] hover:border-emerald-500/50">
        <div class="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center mb-4">
          <i class="fas fa-graduation-cap text-emerald-400 text-xl"></i>
        </div>
        <h3 class="text-lg font-bold text-white mb-2">Student Program Alerts</h3>
      </a>"""
text = text.replace(old_student, new_student)

# 3. Activity Tracking
old_act = """<div class="bg-slate-900/70 backdrop-blur-md border border-slate-400/15 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(37,99,235,0.15)]">
        <div class="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center mb-4">
          <i class="fas fa-chart-line text-purple-400 text-xl"></i>
        </div>
        <h3 class="text-lg font-bold text-white mb-2">Activity Tracking</h3>
        <p class="text-slate-400 text-sm leading-relaxed">Your personal dashboard tracks every email received, program alert, login, and daily reading progress.</p>
      </div>"""
new_act = """<a href="/user/dashboard" class="block bg-slate-900/70 backdrop-blur-md border border-slate-400/15 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(37,99,235,0.15)] hover:border-purple-500/50">
        <div class="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center mb-4">
          <i class="fas fa-chart-line text-purple-400 text-xl"></i>
        </div>
        <h3 class="text-lg font-bold text-white mb-2">Activity Tracking</h3>
      </a>"""
text = text.replace(old_act, new_act)

# 4. Always Early
old_early = """<div class="bg-slate-900/70 backdrop-blur-md border border-slate-400/15 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(37,99,235,0.15)]">
        <div class="w-12 h-12 rounded-xl bg-orange-500/20 flex items-center justify-center mb-4">
          <i class="fas fa-clock text-orange-400 text-xl"></i>
        </div>
        <h3 class="text-lg font-bold text-white mb-2">Always Early</h3>
        <p class="text-slate-400 text-sm leading-relaxed">We notify you 7 days before a program launches so you have time to prepare your application.</p>
      </div>"""
new_early = """<a href="#programs" class="block bg-slate-900/70 backdrop-blur-md border border-slate-400/15 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(37,99,235,0.15)] hover:border-orange-500/50">
        <div class="w-12 h-12 rounded-xl bg-orange-500/20 flex items-center justify-center mb-4">
          <i class="fas fa-clock text-orange-400 text-xl"></i>
        </div>
        <h3 class="text-lg font-bold text-white mb-2">Always Early</h3>
      </a>"""
text = text.replace(old_early, new_early)

# 5. Privacy First
old_priv = """<div class="bg-slate-900/70 backdrop-blur-md border border-slate-400/15 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(37,99,235,0.15)]">
        <div class="w-12 h-12 rounded-xl bg-pink-500/20 flex items-center justify-center mb-4">
          <i class="fas fa-shield-alt text-pink-400 text-xl"></i>
        </div>
        <h3 class="text-lg font-bold text-white mb-2">Privacy First</h3>
        <p class="text-slate-400 text-sm leading-relaxed">Your data stays private. No spam, no selling your email. Unsubscribe instantly at any time.</p>
      </div>"""
new_priv = """<a href="#subscribe" class="block bg-slate-900/70 backdrop-blur-md border border-slate-400/15 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(37,99,235,0.15)] hover:border-pink-500/50">
        <div class="w-12 h-12 rounded-xl bg-pink-500/20 flex items-center justify-center mb-4">
          <i class="fas fa-shield-alt text-pink-400 text-xl"></i>
        </div>
        <h3 class="text-lg font-bold text-white mb-2">Privacy First</h3>
      </a>"""
text = text.replace(old_priv, new_priv)

# 6. Mobile Ready
old_mob = """<div class="bg-slate-900/70 backdrop-blur-md border border-slate-400/15 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(37,99,235,0.15)]">
        <div class="w-12 h-12 rounded-xl bg-cyan-500/20 flex items-center justify-center mb-4">
          <i class="fas fa-mobile-alt text-cyan-400 text-xl"></i>
        </div>
        <h3 class="text-lg font-bold text-white mb-2">Mobile Ready</h3>
        <p class="text-slate-400 text-sm leading-relaxed">Emails and dashboards designed beautifully for every screen - phone, tablet, or desktop.</p>
      </div>"""
new_mob = """<a href="/user/dashboard" class="block bg-slate-900/70 backdrop-blur-md border border-slate-400/15 rounded-2xl p-6 transition-all duration-300 ease-in-out hover:-translate-y-1.5 hover:shadow-[0_20px_40px_rgba(37,99,235,0.15)] hover:border-cyan-500/50">
        <div class="w-12 h-12 rounded-xl bg-cyan-500/20 flex items-center justify-center mb-4">
          <i class="fas fa-mobile-alt text-cyan-400 text-xl"></i>
        </div>
        <h3 class="text-lg font-bold text-white mb-2">Mobile Ready</h3>
      </a>"""
text = text.replace(old_mob, new_mob)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
