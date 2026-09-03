import re

with open('analytics_revenue_portal/routes.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("total_visitors=visitor_stats.get('total_visits', 0),", "total_visitors=visitor_stats.get('total_visits', 0),\n        daily_visitors=visitor_stats.get('daily_visits', 0),")
text = text.replace("leads=len(db.get_contact_messages(limit=10000)),", "leads=len(db.get_contact_messages(limit=10000)),\n        daily_leads=db.get_daily_contact_count(),")

# Add history route
new_route = """
@analytics_bp.route('/history')
@admin_required
def history():
    db = NewsDatabase()
    return render_template('admin_history.html', history=db.get_daily_history())
"""

if '@analytics_bp.route(\'/history\')' not in text:
    text += new_route

with open('analytics_revenue_portal/routes.py', 'w', encoding='utf-8') as f:
    f.write(text)
