import re

# 1. Update index.html
with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("Daily AI news + student program alerts with direct registration links. Free forever.", "Exclusive daily AI intelligence briefings and elite student program alerts. Complimentary forever.")
text = text.replace("Do I need an account to subscribe?", "Is an account required for subscription?")
text = text.replace("Can I unsubscribe?", "Can I cancel my subscription?")
text = text.replace("Get Started For Free", "Initiate Free Access")

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

# 2. Update Admin Dashboard
with open('analytics_revenue_portal/templates/analytics_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("Total Visitors", "Platform Traffic")
text = text.replace("Registered Users", "Active Members")
text = text.replace("Total Leads", "Acquired Prospects")
text = text.replace("Total Revenue", "Gross Revenue")

with open('analytics_revenue_portal/templates/analytics_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

# 3. Update base_saas.html (Admin Sidebar)
with open('templates/base_saas.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('fa-globe"></i> Website', 'fa-globe"></i> Public Platform')

with open('templates/base_saas.html', 'w', encoding='utf-8') as f:
    f.write(text)

