import os

with open('analytics_revenue_portal/templates/messages.html', 'r', encoding='utf-8') as f:
    content = f.read()

tabs = '''        <div class="p-4 border-b border-slate-200 bg-white">
            <div class="flex justify-between items-center mb-3">
                <h3 class="font-bold text-slate-800">Inbox & Complaints</h3>
                <span class="text-xs font-semibold text-slate-500 bg-slate-100 px-2 py-1 rounded-md" id="total-msgs">{{ messages|length }} Total</span>
            </div>
            <div class="flex gap-2 overflow-x-auto pb-1 hide-scrollbar">
                <button onclick="filterMsgs('All', this)" class="filter-btn bg-slate-800 text-white text-[10px] font-bold px-3 py-1.5 rounded-full whitespace-nowrap transition">All</button>
                <button onclick="filterMsgs('Support', this)" class="filter-btn bg-slate-100 hover:bg-slate-200 text-slate-600 text-[10px] font-bold px-3 py-1.5 rounded-full whitespace-nowrap transition">Support</button>
                <button onclick="filterMsgs('Feedback', this)" class="filter-btn bg-slate-100 hover:bg-slate-200 text-slate-600 text-[10px] font-bold px-3 py-1.5 rounded-full whitespace-nowrap transition">Feedback</button>
                <button onclick="filterMsgs('Suggestion', this)" class="filter-btn bg-slate-100 hover:bg-slate-200 text-slate-600 text-[10px] font-bold px-3 py-1.5 rounded-full whitespace-nowrap transition">Suggestions</button>
            </div>
        </div>'''

content = content.replace('''        <div class="p-4 border-b border-slate-200 bg-white flex justify-between items-center">
            <h3 class="font-bold text-slate-800">Inbox</h3>
            <span class="text-xs font-semibold text-slate-500 bg-slate-100 px-2 py-1 rounded-md">{{ messages|length }} Total</span>
        </div>''', tabs)


js = '''
function filterMsgs(type, btn) {
    document.querySelectorAll('.filter-btn').forEach(b => {
        b.classList.remove('bg-slate-800', 'text-white');
        b.classList.add('bg-slate-100', 'text-slate-600');
    });
    btn.classList.remove('bg-slate-100', 'text-slate-600');
    btn.classList.add('bg-slate-800', 'text-white');
    
    let count = 0;
    document.querySelectorAll('.msg-item').forEach(el => {
        if(type === 'All' || el.getAttribute('data-subject').includes(type)) {
            el.style.display = 'block';
            count++;
        } else {
            el.style.display = 'none';
        }
    });
    document.getElementById('total-msgs').textContent = count + ' Total';
}
'''

content = content.replace('data-content="{{ msg.message|e }}">', 'data-content="{{ msg.message|e }}"\n                 data-subject="{{ msg.subject|e }}">')
content = content.replace('function openMessage', js + '\nfunction openMessage')

with open('analytics_revenue_portal/templates/messages.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated messages.html with filters")
