import re

with open('templates/user_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

old_block = """      <a href="${a.url&&a.url!=='#'?a.url:'#'}" target="_blank" class="block group-hover:opacity-80 transition">
        <h3 class="text-xl md:text-2xl font-bold text-slate-100 leading-tight mb-2">${a.title||'Untitled'}</h3>
        <p class="text-slate-400 text-sm md:text-base leading-relaxed mb-4 font-light">${(a.summary||'').substring(0,280)}${(a.summary||'').length>280?'...':''}</p>
      </a>
      ${a.why_important?`<div class="bg-slate-800/40 border-l-2 border-blue-500 p-3 rounded-r-lg text-xs text-slate-300 mb-4"><span class="font-bold text-blue-400 block mb-1">Why it matters:</span>${a.why_important}</div>`:''}
      <div class="flex items-center justify-between border-b border-slate-800 pb-8">
        <div class="flex items-center gap-4">
          <span class="text-[11px] font-medium px-2.5 py-1 bg-slate-800 text-slate-300 rounded-full">Artificial Intelligence</span>"""

new_block = """      <a href="${a.url&&a.url!=='#'?a.url:'#'}" target="_blank" class="block group-hover:opacity-80 transition">
        <h3 class="text-xl md:text-2xl font-bold text-slate-100 leading-tight mb-2">${a.title||'Untitled'}</h3>
        <p class="text-slate-400 text-sm md:text-base leading-relaxed mb-4 font-light">${(a.summary||'').substring(0,280)}${(a.summary||'').length>280?'...':''}</p>
      </a>
      ${a.why_important?`<div class="bg-slate-800/40 border-l-2 border-blue-500 p-3 rounded-r-lg text-xs text-slate-300 mb-4"><span class="font-bold text-blue-400 block mb-1">Why it matters:</span>${a.why_important}</div>`:''}
      <div class="mb-5 mt-2">
        <a href="${a.url&&a.url!=='#'?a.url:'#'}" target="_blank" class="inline-flex items-center gap-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 text-xs font-bold px-4 py-2 rounded-lg transition-colors">
          Read Full Article on ${a.source||'Source'} <i class="fas fa-external-link-alt"></i>
        </a>
      </div>
      <div class="flex items-center justify-between border-b border-slate-800 pb-8">
        <div class="flex items-center gap-4">
          <span class="text-[11px] font-medium px-2.5 py-1 bg-slate-800 text-slate-300 rounded-full">Technology Industry</span>"""

text = text.replace(old_block, new_block)

with open('templates/user_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
