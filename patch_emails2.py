import re

with open('ai_news_agent.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace format_news_email
old_news = re.search(r'def format_news_email\(.*?return f"""<html><body.*?</html>"""', code, re.DOTALL)
new_news = '''def format_news_email(news_items: List[Dict[str, Any]]) -> str:
    today = datetime.now().strftime('%A, %B %d, %Y')
    if not news_items:
        return f"""<!DOCTYPE html><html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f6f9fc;padding:40px 20px;"><div style="max-width:600px;margin:0 auto;background:#fff;border:1px solid #e6ebf1;border-radius:8px;padding:32px;"><h2 style="margin:0 0 16px;font-size:20px;color:#111827;">AI Intelligence Briefing &bull; {today}</h2><div style="padding:16px;background:#fef3c7;border-radius:6px;color:#92400e;font-size:14px;">No significant AI developments detected in the current cycle.</div></div></body></html>"""

    items_html = ''.join(f"""
    <div style="margin-bottom:32px;padding-bottom:32px;border-bottom:1px solid #e5e7eb;">
      <div style="font-size:18px;font-weight:600;color:#111827;margin-bottom:8px;line-height:1.4;">{i}. {item['title']}</div>
      <div style="font-size:12px;color:#6b7280;margin-bottom:16px;text-transform:uppercase;letter-spacing:0.05em;">{item['source']} &bull; {item['published']}</div>
      <div style="font-size:15px;color:#374151;margin-bottom:12px;line-height:1.6;"><strong>Executive Summary:</strong> {item['summary']}</div>
      <div style="font-size:14px;color:#4b5563;margin-bottom:12px;line-height:1.5;"><strong>Market Impact:</strong> {item['why_important']}</div>
      <div style="font-size:14px;color:#4b5563;margin-bottom:16px;line-height:1.5;"><strong>Strategic Outlook:</strong> {item['future_change']}</div>
      <a href="{item['url']}" style="display:inline-block;color:#3b82f6;font-size:14px;font-weight:600;text-decoration:none;">Read Full Report &rarr;</a>
    </div>""" for i, item in enumerate(news_items, 1))

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background-color:#f6f9fc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#333333;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f6f9fc;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="100%" style="max-width:640px;background-color:#ffffff;border:1px solid #e6ebf1;border-radius:8px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.05);">
          <tr>
            <td style="padding:40px;text-align:left;">
              <div style="font-size:12px;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">Nova Brief Intelligence</div>
              <h1 style="margin:0 0 8px 0;font-size:28px;font-weight:700;color:#111827;letter-spacing:-0.02em;">AI Market Briefing</h1>
              <p style="margin:0 0 32px 0;font-size:15px;color:#6b7280;">{today}</p>
              
              {items_html}
              
              <div style="margin-top:8px;font-size:14px;color:#6b7280;line-height:1.5;text-align:center;">
                <strong>Strategic Overview:</strong> Artificial intelligence continues to transition from conceptual frameworks to core enterprise infrastructure. Remain informed to maintain strategic advantage.
              </div>
            </td>
          </tr>
          <tr>
            <td style="background-color:#f9fafb;border-top:1px solid #e5e7eb;padding:24px;text-align:center;font-size:12px;color:#9ca3af;">
              <p style="margin:0 0 8px 0;">Nova Brief &bull; Proprietary Intelligence Feed</p>
              <p style="margin:0;"><a href="https://novabrief-web.onrender.com" style="color:#6b7280;text-decoration:underline;">Dashboard</a> &bull; <a href="https://novabrief-web.onrender.com/privacy" style="color:#6b7280;text-decoration:underline;">Privacy</a></p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""'''
if old_news:
    code = code.replace(old_news.group(0), new_news)


# Replace format_program_email
old_prog = re.search(r'def format_program_email\(.*?return f"""<html><body.*?</html>"""', code, re.DOTALL)
new_prog = '''def format_program_email(program: Dict[str, Any]) -> str:
    """Format student program notification email with direct registration link."""
    today = datetime.now().strftime('%A, %B %d, %Y')
    deadline_text = f"<strong>Application Deadline:</strong> {program.get('deadline', 'Refer to official portal')}<br>" if program.get('deadline') else ''
    launch_text = f"<strong>Launch Date:</strong> {program.get('launch_date', 'Imminent')}<br>" if program.get('launch_date') else ''

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background-color:#f6f9fc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#333333;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f6f9fc;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="100%" style="max-width:600px;background-color:#ffffff;border:1px solid #e6ebf1;border-radius:8px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.05);">
          <tr>
            <td style="padding:40px;text-align:left;">
              <div style="font-size:12px;font-weight:700;color:#059669;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">Priority Application Alert</div>
              <h1 style="margin:0 0 8px 0;font-size:24px;font-weight:600;color:#111827;">{program.get('title', 'New Program')}</h1>
              <p style="margin:0 0 24px 0;font-size:15px;color:#6b7280;">Offered by <strong>{program.get('company', 'Corporate Partner')}</strong></p>
              
              <div style="background-color:#f9fafb;border-radius:6px;padding:24px;margin-bottom:24px;font-size:15px;color:#374151;line-height:1.6;border:1px solid #e5e7eb;">
                {launch_text}
                {deadline_text}
                <div style="margin-top:16px;"><strong>Program Details:</strong><br>{program.get('description', 'A new elite opportunity has opened for students. Review the official portal for comprehensive details.')}</div>
              </div>
              
              <div style="text-align:center;margin:32px 0;">
                <a href="{program.get('registration_url', 'https://novabrief-web.onrender.com')}" style="background-color:#059669;color:#ffffff;text-decoration:none;padding:14px 32px;border-radius:6px;font-size:16px;font-weight:600;display:inline-block;">Access Official Application</a>
              </div>
            </td>
          </tr>
          <tr>
            <td style="background-color:#f9fafb;border-top:1px solid #e5e7eb;padding:24px;text-align:center;font-size:12px;color:#6b7280;">
              <p style="margin:0 0 8px 0;">Nova Brief &bull; Career Intelligence</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""'''
if old_prog:
    code = code.replace(old_prog.group(0), new_prog)

with open('ai_news_agent.py', 'w', encoding='utf-8') as f:
    f.write(code)
