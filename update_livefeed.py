import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

old_feed = """<div class="space-y-3">
            <div class="bg-slate-800/60 rounded-xl p-4 border border-slate-700/50">
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <i class="fas fa-robot text-blue-400 text-xs"></i>
                </div>
                <div>
                  <div class="text-sm font-semibold text-white">AI Morning Brief</div>
                  <div class="text-xs text-slate-500">5 top AI stories - 8:00 AM daily</div>
                </div>
              </div>
            </div>
            <div class="bg-slate-800/60 rounded-xl p-4 border border-emerald-500/20">
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <i class="fas fa-graduation-cap text-emerald-400 text-xs"></i>
                </div>
                <div>
                  <div class="text-sm font-semibold text-white">Program Alert</div>
                  <div class="text-xs text-slate-500">Google Student Facilitator - Register </div>
                </div>
              </div>
            </div>
            <div class="bg-slate-800/60 rounded-xl p-4 border border-purple-500/20">
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <i class="fas fa-star text-purple-400 text-xs"></i>
                </div>
                <div>
                  <div class="text-sm font-semibold text-white">Microsoft Fabric Program</div>
                  <div class="text-xs text-slate-500">Early alert sent 7 days before launch</div>
                </div>
              </div>
            </div>
          </div>"""

new_feed = """<div class="space-y-3" id="heroLiveFeedContainer">
            <div class="bg-slate-800/60 rounded-xl p-4 border border-slate-700/50 text-center animate-pulse">
              <div class="text-sm text-slate-400"><i class="fas fa-spinner fa-spin mr-2"></i> Fetching live intel...</div>
            </div>
          </div>"""

text = text.replace(old_feed, new_feed)

# Also add the javascript at the bottom before </body>
js_code = """<script>
  document.addEventListener('DOMContentLoaded', async () => {
    try {
      const res = await fetch('/api/articles?limit=3');
      const data = await res.json();
      const container = document.getElementById('heroLiveFeedContainer');
      if (data && data.length > 0) {
        container.innerHTML = '';
        data.slice(0,3).forEach((item, index) => {
          let icon = 'fa-robot'; let color = 'blue';
          if(index === 1) { icon = 'fa-graduation-cap'; color = 'emerald'; }
          if(index === 2) { icon = 'fa-star'; color = 'purple'; }
          
          container.innerHTML += 
            <a href="/user/dashboard" class="block bg-slate-800/60 rounded-xl p-4 border border--500/20 hover:bg-slate-700 transition">
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 rounded-lg bg--500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <i class="fas  text--400 text-xs"></i>
                </div>
                <div>
                  <div class="text-sm font-semibold text-white line-clamp-1"></div>
                  <div class="text-xs text-slate-500"></div>
                </div>
              </div>
            </a>
          ;
        });
      }
    } catch(err) {
      console.error('Failed to load feed', err);
    }
  });
</script>"""

if "heroLiveFeedContainer" not in text:
    print("Warning: old feed not replaced!")
else:
    if "heroLiveFeedContainer');" not in text:
        text = text.replace("</body>", js_code + "\n</body>")

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
