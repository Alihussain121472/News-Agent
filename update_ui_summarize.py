import re

with open('templates/user_dashboard.html', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add Navigation Button
nav_button = """        <button onclick="switchTab('articles')" class="nav-item w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-300 mb-1" id="nav-articles">
          <i class="fas fa-bolt w-4 text-center"></i> Live Feed
        </button>
        <button onclick="switchTab('summarizer')" class="nav-item w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-blue-400 font-bold mb-1 bg-blue-500/10 border border-blue-500/20" id="nav-summarizer">
          <i class="fas fa-magic w-4 text-center"></i> AI Summarizer
        </button>"""
code = code.replace("""        <button onclick="switchTab('articles')" class="nav-item w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-300 mb-1" id="nav-articles">
          <i class="fas fa-bolt w-4 text-center"></i> Live Feed
        </button>""", nav_button)

# 2. Add Tab Container (insert before <!-- PROGRAMS TAB -->)
tab_html = """      <!-- SUMMARIZER TAB -->
      <div id="tab-summarizer" class="hidden max-w-3xl mx-auto w-full">
        <div class="flex items-center justify-between mb-8 pb-4 border-b border-slate-700/50">
          <h2 class="text-2xl font-black text-white flex items-center gap-3"><i class="fas fa-magic text-blue-400"></i> AI Article Summarizer</h2>
        </div>
        
        <div class="glass rounded-2xl p-6 mb-8">
          <p class="text-slate-400 text-sm mb-6">Select a recent tech article from the feed, or paste any URL below to generate a quick, readable summary instantly.</p>
          
          <div class="mb-5">
            <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">1. Select a Recent Article</label>
            <select id="summarizeSelect" class="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500 transition appearance-none">
              <option value="">-- Choose an article to summarize --</option>
            </select>
          </div>
          
          <div class="text-center text-slate-600 text-xs font-bold uppercase tracking-widest my-4">OR</div>
          
          <div class="mb-6">
            <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">2. Paste Any Article URL</label>
            <input type="url" id="summarizeUrl" placeholder="https://techcrunch.com/..." class="w-full bg-slate-800 border border-slate-700 text-white placeholder-slate-500 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500 transition"/>
          </div>
          
          <button id="btnSummarize" onclick="runSummarizer()" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-xl transition-all shadow-[0_0_20px_rgba(37,99,235,0.3)] hover:shadow-[0_0_30px_rgba(37,99,235,0.5)] flex items-center justify-center gap-2">
            <i class="fas fa-bolt text-yellow-300"></i> Generate AI Summary
          </button>
        </div>
        
        <!-- Result Box -->
        <div id="summaryResultContainer" class="hidden">
          <h3 class="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Summary Result</h3>
          <div id="summaryContent" class="glass rounded-2xl p-6 text-slate-200 text-sm leading-relaxed prose prose-invert prose-blue max-w-none">
            <!-- Summary appears here -->
          </div>
        </div>
      </div>

      <!-- PROGRAMS TAB -->"""
code = code.replace("<!-- PROGRAMS TAB -->", tab_html)

# 3. Add to switchTab Array
code = code.replace("['overview','activity','articles','programs','progress'].forEach", "['overview','activity','articles','programs','progress','summarizer'].forEach")

# 4. Add population logic to loadArticles()
populate_js = """
async function loadArticles(){
  const r = await fetch('/api/articles?limit=50');
  allArticles = await r.json();
  renderArticles(allArticles);
  
  // Populate Summarizer Dropdown
  const select = document.getElementById('summarizeSelect');
  if(select && allArticles.length > 0) {
    select.innerHTML = '<option value="">-- Choose an article to summarize --</option>';
    allArticles.forEach(a => {
      if(a.url && a.url !== '#') {
        const opt = document.createElement('option');
        opt.value = a.url;
        opt.textContent = a.title.substring(0, 80) + (a.title.length > 80 ? '...' : '');
        select.appendChild(opt);
      }
    });
  }
}
"""
old_loadArticles = """async function loadArticles(){
  const r = await fetch('/api/articles?limit=50');
  allArticles = await r.json();
  renderArticles(allArticles);
}"""
code = code.replace(old_loadArticles, populate_js)

# 5. Add runSummarizer() JS at the bottom
js_func = """
// Run AI Summarizer
async function runSummarizer() {
  const selectUrl = document.getElementById('summarizeSelect').value;
  const inputUrl = document.getElementById('summarizeUrl').value.trim();
  const url = inputUrl || selectUrl;
  
  if(!url || !url.startsWith('http')) {
    alert('Please select an article or enter a valid URL.');
    return;
  }
  
  const btn = document.getElementById('btnSummarize');
  const resultContainer = document.getElementById('summaryResultContainer');
  const resultContent = document.getElementById('summaryContent');
  
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing Article...';
  btn.disabled = true;
  btn.classList.add('opacity-70');
  
  try {
    const r = await fetch('/api/summarize', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url: url})
    });
    const data = await r.json();
    
    resultContainer.classList.remove('hidden');
    if(data.status === 'success') {
      // Format bullet points properly with Tailwind HTML
      let html = data.summary.replace(/\\n/g, '<br>');
      html = html.replace(/\\*\\*(.*?)\\*\\*/g, '<strong class="text-white"></strong>');
      html = html.replace(/\\*(.*?)\\*/g, '<em class="text-slate-300"></em>');
      resultContent.innerHTML = html;
      resultContent.classList.remove('border-red-500/50', 'text-red-400');
    } else {
      resultContent.innerHTML = <i class="fas fa-exclamation-circle text-red-500 mr-2"></i> ;
      resultContent.classList.add('border-red-500/50', 'text-red-400');
    }
  } catch(e) {
    resultContainer.classList.remove('hidden');
    resultContent.innerHTML = <i class="fas fa-exclamation-circle text-red-500 mr-2"></i> Network error. Please try again.;
  } finally {
    btn.innerHTML = '<i class="fas fa-bolt text-yellow-300"></i> Generate AI Summary';
    btn.disabled = false;
    btn.classList.remove('opacity-70');
    resultContainer.scrollIntoView({behavior: 'smooth', block: 'nearest'});
  }
}
</script>
"""
code = code.replace("</script>", js_func)

with open('templates/user_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(code)
