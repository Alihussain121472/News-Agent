import re

with open('ai_news_agent.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace send_password_reset_email
old_reset = re.search(r'def send_password_reset_email\(.*?return', code, re.DOTALL)
if not old_reset:
    old_reset = re.search(r'def send_password_reset_email\(.*?send_email\(email, subject, html_content\)', code, re.DOTALL)
    
if old_reset:
    new_reset = '''def send_password_reset_email(email: str, token: str) -> None:
    reset_url = f"https://novabrief-web.onrender.com/user/reset-password/{token}"
    subject = "Reset Your Password - Nova Brief"
    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background-color:#f6f9fc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#333333;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f6f9fc;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="100%" style="max-width:600px;background-color:#ffffff;border:1px solid #e6ebf1;border-radius:8px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.05);">
          <tr>
            <td style="padding:40px;text-align:left;">
              <h1 style="margin:0 0 16px 0;font-size:24px;font-weight:600;color:#111827;">Password Reset Request</h1>
              <p style="margin:0 0 24px 0;font-size:16px;color:#4b5563;line-height:1.6;">We received a request to reset the password for your Nova Brief account associated with {email}.</p>
              <p style="margin:0 0 24px 0;font-size:16px;color:#4b5563;line-height:1.6;">Click the button below to securely set a new password. This link will expire in 1 hour.</p>
              
              <div style="text-align:center;margin:32px 0;">
                <a href="{reset_url}" style="background-color:#0f172a;color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:6px;font-size:16px;font-weight:600;display:inline-block;">Reset Password</a>
              </div>
              
              <p style="margin:0;font-size:14px;color:#6b7280;line-height:1.5;">If you did not request a password reset, please ignore this email or contact support if you have concerns.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    send_email(email, subject, html_content)'''
    code = code.replace(old_reset.group(0), new_reset)

with open('ai_news_agent.py', 'w', encoding='utf-8') as f:
    f.write(code)
