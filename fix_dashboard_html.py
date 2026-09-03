import re

with open('analytics_revenue_portal/templates/analytics_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('<p class="text-xs font-bold uppercase tracking-[0.08em] text-slate-400">Total traffic</p>\n        <p class="mt-3 text-3xl font-extrabold tracking-tight text-slate-900">{{ total_visitors }}</p>', '<p class="text-xs font-bold uppercase tracking-[0.08em] text-slate-400">Today\'s traffic</p>\n        <p class="mt-3 text-3xl font-extrabold tracking-tight text-slate-900">{{ daily_visitors }}</p>')

text = text.replace('<p class="text-xs font-bold uppercase tracking-[0.08em] text-slate-400">Support requests</p>\n        <p class="mt-3 text-3xl font-extrabold tracking-tight text-slate-900">{{ leads }}</p>', '<p class="text-xs font-bold uppercase tracking-[0.08em] text-slate-400">Today\'s requests</p>\n        <p class="mt-3 text-3xl font-extrabold tracking-tight text-slate-900">{{ daily_leads }}</p>')

text = text.replace('All-time visits', 'Today\'s visits')
text = text.replace('All enquiries', 'Today\'s enquiries')

# Add "View History" button in the header
text = text.replace('<p class="mt-1 text-sm text-slate-500">Overview of your real-time performance</p>', '<p class="mt-1 text-sm text-slate-500">Overview of your real-time performance</p>\n    <a href="/admin/history" class="mt-4 inline-flex items-center gap-2 rounded-lg bg-white border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition"><i class="fas fa-history"></i> View Historical Data</a>')

with open('analytics_revenue_portal/templates/analytics_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
