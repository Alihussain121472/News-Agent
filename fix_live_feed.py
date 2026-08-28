import re
with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

start_str = '<div class="space-y-3">'
end_str = '<!-- End of floating mockups -->'
start_idx = text.find(start_str)
end_idx = text.find(end_str)

if start_idx != -1 and end_idx != -1:
    # wait, the space-y-3 could be something else. Let's find the first space-y-3 after "Live Feed"
    lf_idx = text.find("Live Feed")
    sy3_idx = text.find('<div class="space-y-3">', lf_idx)
    end_div_idx = text.find('</div>\n          </div>\n        </div>\n      </div>', sy3_idx)
    
    old_block = text[sy3_idx:end_div_idx]
    
    new_block = '''<div class="space-y-3" id="heroLiveFeedContainer">
              <div class="bg-slate-800/60 rounded-xl p-4 border border-slate-700/50 text-center animate-pulse">
                <div class="text-sm text-slate-400"><i class="fas fa-spinner fa-spin mr-2"></i> Fetching live intel...</div>
              </div>
            </div>'''
            
    text = text[:sy3_idx] + new_block + text[end_div_idx:]
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Replaced Live Feed container")
else:
    print("Not found")

