import re

with open('templates/user_dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Change Sidebar Overview text
html = html.replace('<i class="fas fa-th-large w-5 text-center"></i> Overview', '<i class="fas fa-th-large w-5 text-center"></i> My Analytics')

# 2. Add News Feed button
new_sidebar_btn = '''      <button onclick="switchTab('articles')" class="nav-item active w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-300 mb-1" id="nav-articles">
        <i class="fas fa-newspaper w-5 text-center"></i> News Feed
      </button>
      <button onclick="switchTab('overview')" class="nav-item w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-300 mb-1" id="nav-overview">
        <i class="fas fa-chart-pie w-5 text-center"></i> My Analytics
      </button>'''

html = re.sub(r'<button onclick="switchTab\(\'overview\'\)".*?id="nav-overview">.*?</button>', '', html, flags=re.DOTALL)
html = re.sub(r'<button onclick="switchTab\(\'articles\'\)".*?id="nav-articles">.*?</button>', '', html, flags=re.DOTALL)
html = html.replace('<div class="flex-1 overflow-y-auto p-3">', '<div class="flex-1 overflow-y-auto p-3">\n' + new_sidebar_btn)

# 3. New Articles Tab HTML
old_articles_tab = '''      <!-- ARTICLES TAB -->
      <div id="tab-articles" class="hidden">
        <div class="glass rounded-2xl p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-bold text-white flex items-center gap-2"><i class="fas fa-newspaper text-blue-400"></i> AI News Articles</h3>
          </div>
          <div class="relative mb-4">
            <i class="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-sm"></i>
            <input type="text" id="articleSearch" placeholder="Search articles..." onkeyup="liveSearch()" class="w-full bg-dark-800 border border-slate-700 text-white placeholder-slate-500 rounded-xl pl-9 pr-4 py-2.5 text-sm focus:outline-none focus:border-blue-500 transition"/>
          </div>
          <div id="articlesList" class="space-y-4"></div>
        </div>
      </div>'''

new_articles_tab = '''      <!-- ARTICLES TAB -->
      <div id="tab-articles" class="hidden max-w-4xl mx-auto w-full">
        <div class="flex items-center justify-between mb-8 pb-4 border-b border-slate-700/50">
          <h2 class="text-2xl font-black text-white flex items-center gap-3"><i class="fas fa-bolt text-yellow-400"></i> Live Intelligence Feed</h2>
          <div class="relative w-64">
            <i class="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm"></i>
            <input type="text" id="articleSearch" placeholder="Search topics..." onkeyup="liveSearch()" class="w-full bg-slate-800/50 border border-slate-700 text-white placeholder-slate-400 rounded-full pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-blue-500 transition shadow-inner"/>
          </div>
        </div>
        <div id="articlesList" class="space-y-8 pb-12"></div>
      </div>'''
html = html.replace(old_articles_tab, new_articles_tab)

# 4. New Render function
new_render = '''function renderArticles(arts){
  document.getElementById('articlesList').innerHTML = arts.length ? arts.map(a=>`
    <article class="group bg-transparent transition">
      <div class="flex items-center gap-2 mb-2">
        <div class="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-[10px] text-slate-400 font-bold border border-slate-700">
          <i class="fas fa-robot"></i>
        </div>
        <span class="text-xs font-semibold text-slate-300">${a.source||'Nova Brief AI'}</span>
        <span class="text-xs text-slate-500">•</span>
        <span class="text-xs text-slate-500">${relTime(a.fetched_at)}</span>
      </div>
      <a href="${a.url&&a.url!=='#'?a.url:'#'}" target="_blank" class="block group-hover:opacity-80 transition">
        <h3 class="text-xl md:text-2xl font-bold text-slate-100 leading-tight mb-2">${a.title||'Untitled'}</h3>
        <p class="text-slate-400 text-sm md:text-base leading-relaxed mb-4 font-light">${(a.summary||'').substring(0,280)}${(a.summary||'').length>280?'...':''}</p>
      </a>
      ${a.why_important?`<div class="bg-slate-800/40 border-l-2 border-blue-500 p-3 rounded-r-lg text-xs text-slate-300 mb-4"><span class="font-bold text-blue-400 block mb-1">Why it matters:</span>${a.why_important}</div>`:''}
      <div class="flex items-center justify-between border-b border-slate-800 pb-8">
        <div class="flex items-center gap-4">
          <span class="text-[11px] font-medium px-2.5 py-1 bg-slate-800 text-slate-300 rounded-full">Artificial Intelligence</span>
          <span class="text-xs text-slate-500">${Math.max(2, Math.floor((a.summary||'').length/130))} min read</span>
        </div>
        <div class="flex items-center gap-3">
          <button class="text-slate-500 hover:text-slate-300 transition" title="Save for later"><i class="far fa-bookmark"></i></button>
          <button class="text-slate-500 hover:text-slate-300 transition" title="Show less like this"><i class="fas fa-minus-circle"></i></button>
        </div>
      </div>
    </article>`).join('') : '<div class="text-slate-500 text-sm text-center py-12">No articles in your feed yet.</div>';
}'''

html = re.sub(r'function renderArticles\(arts\)\{[\s\S]*?\n\}', new_render, html)

# 5. Default tab
html = html.replace("switchTab('overview');", "switchTab('articles');")

with open('templates/user_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
