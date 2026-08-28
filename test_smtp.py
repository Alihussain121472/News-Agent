import smtplib
import os
from dotenv import load_dotenv

load_dotenv()
email_user = os.getenv('EMAIL_USER')
email_pass = os.getenv('EMAIL_APP_PASSWORD')

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_user, email_pass)
    print("SUCCESS: Credentials are valid!")
    server.quit()
except Exception as e:
    print(f"FAILED: {e}")
