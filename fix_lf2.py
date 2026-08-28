import re
with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = re.compile(r'(<div class="space-y-3">.*?)(</div>\s*</div>\s*</div>\s*</div>\s*</section>)', re.DOTALL)
match = pattern.search(text)
if match:
    new_block = '''<div class="space-y-3" id="heroLiveFeedContainer">
              <div class="bg-slate-800/60 rounded-xl p-4 border border-slate-700/50 text-center animate-pulse">
                <div class="text-sm text-slate-400"><i class="fas fa-spinner fa-spin mr-2"></i> Fetching live intel...</div>
              </div>
            </div>'''
    text = text[:match.start(1)] + new_block + "\n          " + match.group(2)
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Success")
else:
    print("Match failed")
