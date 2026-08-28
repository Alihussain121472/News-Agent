import os
import re

with open('templates/user_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Sidebar Links
sidebar_injection = '''
        <button id="nav-memory" onclick="switchTab('memory')" class="nav-item w-full flex items-center gap-3 px-4 py-3 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition">
          <i class="fas fa-bookmark w-5 text-center"></i> Memory Vault
        </button>
        <button id="nav-preferences" onclick="openPreferences()" class="nav-item w-full flex items-center gap-3 px-4 py-3 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition">
          <i class="fas fa-sliders-h w-5 text-center"></i> Preferences
        </button>
'''
if 'id="nav-memory"' not in content:
    content = content.replace('        <button id="nav-programs"', sidebar_injection + '        <button id="nav-programs"')

# 2. Add memory tab and date picker to articles tab
# Let's replace the articles tab header
old_articles_header = '''<div class="flex items-center justify-between mb-8 pb-4 border-b border-slate-700/50">
          <h2 class="text-2xl font-black text-white flex items-center gap-3"><i class="fas fa-bolt text-yellow-400"></i> Live Intelligence Feed</h2>'''
new_articles_header = '''<div class="flex flex-col sm:flex-row items-center justify-between mb-8 pb-4 border-b border-slate-700/50 gap-4">
          <h2 class="text-2xl font-black text-white flex items-center gap-3"><i class="fas fa-bolt text-yellow-400"></i> Live Intelligence Feed</h2>
          <div class="flex gap-2">
            <input type="date" id="newsDatePicker" onchange="loadArticles()" class="bg-slate-800/50 border border-slate-700 text-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />'''
content = content.replace(old_articles_header, new_articles_header)

# 3. Add Memory Tab Content
memory_tab = '''
      <!-- MEMORY TAB -->
      <div id="tab-memory" class="hidden max-w-4xl mx-auto w-full">
        <div class="flex items-center justify-between mb-8 pb-4 border-b border-slate-700/50">
          <h2 class="text-2xl font-black text-white flex items-center gap-3"><i class="fas fa-bookmark text-blue-400"></i> Memory Vault</h2>
          <span class="text-xs text-slate-500 bg-slate-800 px-3 py-1 rounded-full"><i class="fas fa-info-circle"></i> Auto-cleans after 30 days</span>
        </div>
        <div id="memoryArticlesList" class="space-y-8 pb-12"></div>
      </div>
'''
if 'id="tab-memory"' not in content:
    content = content.replace('<!-- PROGRAMS TAB -->', memory_tab + '\n      <!-- PROGRAMS TAB -->')

# 4. Add Preferences Modal
preferences_modal = '''
  <!-- Preferences Modal -->
  <div id="preferencesModal" class="fixed inset-0 bg-slate-900/80 backdrop-blur-sm z-[100] hidden flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-slate-700/50 rounded-2xl shadow-2xl w-full max-w-xl flex flex-col transform transition-all">
      <div class="p-6 border-b border-slate-800 flex justify-between items-center">
        <h3 class="text-xl font-bold text-white flex items-center gap-3"><i class="fas fa-sliders-h text-blue-400"></i> Personalize Feed</h3>
        <button onclick="closePreferences()" class="text-slate-500 hover:text-slate-300 transition text-xl">&times;</button>
      </div>
      <div class="p-6 overflow-y-auto max-h-[60vh] space-y-6">
        <div>
          <h4 class="text-white font-bold mb-3"><i class="fas fa-building text-slate-400 mr-2"></i> Companies</h4>
          <div class="grid grid-cols-2 gap-3" id="prefCompanies">
            <label class="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" value="Google" class="rounded bg-slate-800 border-slate-700"> Google</label>
            <label class="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" value="Microsoft" class="rounded bg-slate-800 border-slate-700"> Microsoft</label>
            <label class="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" value="Meta" class="rounded bg-slate-800 border-slate-700"> Meta / Facebook</label>
            <label class="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" value="OpenAI" class="rounded bg-slate-800 border-slate-700"> OpenAI</label>
            <label class="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" value="NVIDIA" class="rounded bg-slate-800 border-slate-700"> NVIDIA</label>
            <label class="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" value="Apple" class="rounded bg-slate-800 border-slate-700"> Apple</label>
          </div>
        </div>
        <div>
          <h4 class="text-white font-bold mb-3"><i class="fas fa-microchip text-slate-400 mr-2"></i> Fields of Interest</h4>
          <div class="grid grid-cols-2 gap-3" id="prefFields">
            <label class="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" value="Generative AI" class="rounded bg-slate-800 border-slate-700"> Generative AI</label>
            <label class="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" value="Machine Learning" class="rounded bg-slate-800 border-slate-700"> Machine Learning</label>
            <label class="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" value="Robotics" class="rounded bg-slate-800 border-slate-700"> Robotics</label>
            <label class="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" value="Cybersecurity" class="rounded bg-slate-800 border-slate-700"> Cybersecurity</label>
            <label class="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" value="AI Safety" class="rounded bg-slate-800 border-slate-700"> AI Safety</label>
            <label class="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" value="Data Science" class="rounded bg-slate-800 border-slate-700"> Data Science</label>
          </div>
        </div>
      </div>
      <div class="p-4 border-t border-slate-800 flex justify-end gap-3">
        <button onclick="closePreferences()" class="text-slate-400 hover:text-white px-4 py-2 transition">Cancel</button>
        <button onclick="savePreferences()" id="btnSavePref" class="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-6 rounded-lg transition shadow-lg">Save Preferences</button>
      </div>
    </div>
  </div>
'''
if 'id="preferencesModal"' not in content:
    content = content.replace('</body>', preferences_modal + '\n</body>')

# 5. Fix tabs array in JS
old_tabs_array = "['overview','activity','articles','programs','progress','summarizer']"
new_tabs_array = "['overview','activity','articles','programs','progress','summarizer','memory']"
content = content.replace(old_tabs_array, new_tabs_array)

# 6. Update renderArticles
old_render_js = "Math.max(2, Math.floor((a.summary||'').length/130))} min read</span>\n          </div>"
new_render_js = "Math.max(2, Math.floor((a.summary||'').length/130))} min read</span>\n          </div>\n          <div class=\"flex items-center gap-2\">\n            <button onclick=\"saveArticle(${a.id}, this)\" class=\"text-slate-400 hover:text-blue-400 bg-slate-800/50 hover:bg-slate-800 px-3 py-1.5 rounded-lg transition text-xs font-semibold\"><i class=\"fas fa-bookmark mr-1\"></i> Save</button>\n            <button onclick=\"shareArticle('${a.url||'#'}', '${(a.title||'').replace(/'/g, '\\\\\\'\\\\\\')}')\" class=\"text-slate-400 hover:text-emerald-400 bg-slate-800/50 hover:bg-slate-800 px-3 py-1.5 rounded-lg transition text-xs font-semibold\"><i class=\"fas fa-share-alt mr-1\"></i> Share</button>\n          </div>"
content = content.replace(old_render_js, new_render_js)

# 7. Update loadArticles to use date
content = content.replace(
    "const r = await fetch('/api/articles?limit=50');", 
    "const dateVal = document.getElementById('newsDatePicker') ? document.getElementById('newsDatePicker').value : '';\n    const r = await fetch(`/api/articles?limit=50${dateVal ? '&date='+dateVal : ''}`);"
)

# 8. Add JS functions for Preferences and Memory
js_functions = '''
async function loadMemory() {
    try {
        const r = await fetch('/api/user/saved-articles');
        const arts = await r.json();
        const container = document.getElementById('memoryArticlesList');
        if(!arts.length) {
            container.innerHTML = '<div class="text-center text-slate-500 py-12"><i class="fas fa-box-open text-4xl mb-3 opacity-50 block"></i> No saved articles yet.<br>Save articles from the Live Feed to build your memory vault.</div>';
            return;
        }
        container.innerHTML = arts.map(a => `
            <article class="group bg-dark-800/40 p-5 rounded-xl border border-slate-700/50 relative mb-4">
                <div class="text-[10px] text-slate-500 absolute top-3 right-4"><i class="fas fa-clock"></i> Saved ${relTime(a.saved_at)}</div>
                <h3 class="text-lg font-bold text-slate-200 mb-2 pr-20"><a href="${a.url||'#'}" target="_blank" class="hover:text-blue-400 transition">${a.title}</a></h3>
                <p class="text-slate-400 text-sm mb-4 line-clamp-2">${a.summary}</p>
                <button onclick="removeArticle(${a.id}, this)" class="text-red-400 hover:text-red-300 hover:bg-red-500/10 px-3 py-1 rounded text-xs font-bold transition border border-red-500/20"><i class="fas fa-trash-alt mr-1"></i> Remove</button>
            </article>
        `).join('');
    } catch(e) { console.error(e); }
}

async function saveArticle(id, btn) {
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>';
    try {
        await fetch('/api/user/saved-articles/'+id, {method: 'POST'});
        btn.innerHTML = '<i class="fas fa-check text-emerald-400 mr-1"></i> Saved';
        btn.classList.add('text-emerald-400');
        loadMemory();
    } catch(e) {}
}

async function removeArticle(id, btn) {
    const card = btn.closest('article');
    try {
        await fetch('/api/user/saved-articles/'+id, {method: 'DELETE'});
        card.style.opacity = '0';
        setTimeout(() => { loadMemory(); }, 300);
    } catch(e) {}
}

function shareArticle(url, title) {
    if(navigator.share) {
        navigator.share({ title: title, url: url });
    } else {
        window.open('https://twitter.com/intent/tweet?text=' + encodeURIComponent(title + ' ' + url), '_blank');
    }
}

async function openPreferences() {
    try {
        const r = await fetch('/api/user/preferences');
        const p = await r.json();
        const comps = (p.companies||'').split(',');
        const fields = (p.fields||'').split(',');
        
        document.querySelectorAll('#prefCompanies input').forEach(cb => cb.checked = comps.includes(cb.value));
        document.querySelectorAll('#prefFields input').forEach(cb => cb.checked = fields.includes(cb.value));
        
        document.getElementById('preferencesModal').classList.remove('hidden');
    } catch(e) {}
}
function closePreferences() { document.getElementById('preferencesModal').classList.add('hidden'); }
async function savePreferences() {
    const btn = document.getElementById('btnSavePref');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    const comps = Array.from(document.querySelectorAll('#prefCompanies input:checked')).map(cb => cb.value).join(',');
    const fields = Array.from(document.querySelectorAll('#prefFields input:checked')).map(cb => cb.value).join(',');
    
    try {
        await fetch('/api/user/preferences', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({companies: comps, fields: fields})
        });
        closePreferences();
        loadArticles(); // reload feed with new prefs
    } catch(e) {}
    btn.innerHTML = 'Save Preferences';
}

// Ensure loadMemory is called initially
document.addEventListener('DOMContentLoaded', loadMemory);
'''
if 'function loadMemory' not in content:
    content = content.replace('// Load overview\n', js_functions + '\n// Load overview\n')

with open('templates/user_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched user_dashboard.html successfully")
