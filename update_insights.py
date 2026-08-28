import os
import re

with open('analytics_revenue_portal/templates/analytics_insights.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_msg = 'Your website traffic is steady, but your organic reach is slightly underperforming. The AI recommends generating 2 more SEO articles this week targeting the keyword "student automation tools" to capture more search volume.'
new_msg = '<span class="text-emerald-400 font-bold"><i class="fas fa-check-circle"></i> Task Completed:</span> You successfully generated the 2 SEO articles targeting "student automation tools"! These are now live on your website and indexing on Google.<br><br><b>Next Recommendation:</b> You should share these new articles on Reddit and Quora to drive immediate referral traffic and build external backlinks.'

content = content.replace(old_msg, new_msg)

with open('analytics_revenue_portal/templates/analytics_insights.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated Insights UI")
