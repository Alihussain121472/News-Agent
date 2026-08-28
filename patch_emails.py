import re

with open('ai_news_agent.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace format_welcome_email
old_welcome = re.search(r'def format_welcome_email\(.*?return f"""<!DOCTYPE html>.*?</html>"""', code, re.DOTALL)
new_welcome = '''def format_welcome_email(subscriber_email: str, name: str = None) -> str:
    today = datetime.now().strftime('%A, %B %d, %Y')
    greeting = f"Hello {name}," if name else "Hello,"
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
              <h1 style="margin:0 0 16px 0;font-size:24px;font-weight:600;color:#111827;">Welcome to Nova Brief</h1>
              <p style="margin:0 0 24px 0;font-size:16px;color:#4b5563;line-height:1.6;">{greeting}<br><br>Your account has been successfully verified and activated. You are now subscribed to receive our enterprise-grade daily AI intelligence briefings and elite student program alerts.</p>
              
              <div style="background-color:#f3f4f6;border-radius:6px;padding:24px;margin-bottom:24px;">
                <h2 style="margin:0 0 16px 0;font-size:14px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.05em;">What to Expect</h2>
                <div style="margin-bottom:16px;font-size:14px;color:#4b5563;line-height:1.5;">
                  <strong style="color:#111827;">Daily AI Briefing (8:00 AM)</strong><br>
                  The top 5 AI industry developments summarized with actionable analysis on market impact.
                </div>
                <div style="margin-bottom:16px;font-size:14px;color:#4b5563;line-height:1.5;">
                  <strong style="color:#111827;">Early Program Alerts</strong><br>
                  Advance notifications for Google, Microsoft, AWS, and Meta student programs with direct application links.
                </div>
                <div style="font-size:14px;color:#4b5563;line-height:1.5;">
                  <strong style="color:#111827;">Intelligence Dashboard</strong><br>
                  Access your personal portal to track applications, monitor activity, and search global tech news.
                </div>
              </div>
              
              <div style="text-align:center;margin:32px 0;">
                <a href="https://novabrief-web.onrender.com/user/dashboard" style="background-color:#0f172a;color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:6px;font-size:16px;font-weight:600;display:inline-block;">Access Dashboard</a>
              </div>
            </td>
          </tr>
          <tr>
            <td style="background-color:#f9fafb;border-top:1px solid #e5e7eb;padding:24px;text-align:center;font-size:12px;color:#6b7280;">
              <p style="margin:0 0 8px 0;">Nova Brief &bull; Professional AI Intelligence</p>
              <p style="margin:0;"><a href="https://novabrief-web.onrender.com" style="color:#3b82f6;text-decoration:none;">Platform</a> &bull; <a href="https://novabrief-web.onrender.com/privacy" style="color:#6b7280;text-decoration:none;">Privacy Policy</a> &bull; <a href="https://novabrief-web.onrender.com/terms" style="color:#6b7280;text-decoration:none;">Terms of Service</a></p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""'''
if old_welcome:
    code = code.replace(old_welcome.group(0), new_welcome)


# Replace format_program_welcome_email
old_prog_welcome = re.search(r'def format_program_welcome_email\(.*?return f"""<!DOCTYPE html>.*?</html>"""', code, re.DOTALL)
new_prog_welcome = '''def format_program_welcome_email(subscriber_email: str, name: str = None, program_title: str = None) -> str:
    greeting = f"Hello {name}," if name else "Hello,"
    prog_text = f"specifically for <strong>{program_title}</strong> and other elite programs" if program_title else "for elite student programs"
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
              <h1 style="margin:0 0 16px 0;font-size:24px;font-weight:600;color:#111827;">Alert Registration Confirmed</h1>
              <p style="margin:0 0 24px 0;font-size:16px;color:#4b5563;line-height:1.6;">{greeting}<br><br>Your alert configuration has been successfully provisioned {prog_text}. You will now receive priority notifications before these applications officially open to the public.</p>
              
              <div style="background-color:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:16px;margin-bottom:24px;color:#166534;font-size:14px;line-height:1.5;">
                <strong>Status: Active</strong><br>Your email ({subscriber_email}) is secured in our priority notification queue.
              </div>
              
              <div style="text-align:center;margin:32px 0;">
                <a href="https://novabrief-web.onrender.com/user/dashboard" style="background-color:#059669;color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:6px;font-size:16px;font-weight:600;display:inline-block;">View Program Dashboard</a>
              </div>
            </td>
          </tr>
          <tr>
            <td style="background-color:#f9fafb;border-top:1px solid #e5e7eb;padding:24px;text-align:center;font-size:12px;color:#6b7280;">
              <p style="margin:0 0 8px 0;">Nova Brief &bull; Elite Program Alerts</p>
              <p style="margin:0;"><a href="https://novabrief-web.onrender.com" style="color:#3b82f6;text-decoration:none;">Platform</a> &bull; <a href="https://novabrief-web.onrender.com/privacy" style="color:#6b7280;text-decoration:none;">Privacy Policy</a> &bull; <a href="https://novabrief-web.onrender.com/terms" style="color:#6b7280;text-decoration:none;">Terms of Service</a></p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""'''
if old_prog_welcome:
    code = code.replace(old_prog_welcome.group(0), new_prog_welcome)


with open('ai_news_agent.py', 'w', encoding='utf-8') as f:
    f.write(code)
