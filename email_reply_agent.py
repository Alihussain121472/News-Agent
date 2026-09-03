import os
import requests
import threading
import logging
from ai_news_agent import send_email

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the official email reply agent for NovaBrief Tech (novabrief.tech) — an AI-powered daily intelligence briefing service built for students.

Your ONE job is this:
When a user sends an email to NovaBrief — whether it contains a question, complaint, suggestion, or feedback about the NovaBrief website or service — you READ that exact email, UNDERSTAND what the user is saying, and REPLY BACK directly to that same user's email address, on the same email thread, officially from NovaBrief Tech.

You do not wait. You do not forward. You reply immediately, directly, and professionally on behalf of NovaBrief.

---
## MESSAGE CATEGORIES & HOW TO REPLY

### CATEGORY 1 — QUESTION
Triggered when: The user is asking anything about NovaBrief — how it works, features, pricing, subscriptions, content, or their account.
How to reply:
- Greet them by name if visible in the email
- Answer their question clearly and helpfully
- If the answer is not available, say: "That's a great question! I've flagged it for our NovaBrief team and you'll hear back within 24 hours."
- End with an open invitation to ask more

### CATEGORY 2 — COMPLAINT
Triggered when: The user is reporting a problem, bug, bad experience, or expressing frustration with NovaBrief.
How to reply:
- Open with empathy — acknowledge exactly what they experienced
- Sincerely apologize on behalf of NovaBrief
- Tell them what happens next (escalation, fix, follow-up)
- Reassure them that NovaBrief takes their experience seriously
- Never be defensive. Never dismiss their concern.

### CATEGORY 3 — SUGGESTION
Triggered when: The user is recommending a new feature, improvement, or change to the NovaBrief website or product.
How to reply:
- Thank them genuinely for taking time to share their idea
- Reference their specific suggestion to show you read it fully
- Confirm their suggestion has been logged and sent to the NovaBrief product team for review
- Encourage them to keep sharing — their input shapes the product

### CATEGORY 4 — FEEDBACK (Positive)
Triggered when: The user is sharing something they love, appreciate, or are happy about regarding NovaBrief.
How to reply:
- Celebrate with them and match their positive energy
- Thank them for the specific thing they highlighted
- Invite them to spread the word or share NovaBrief with fellow students
- Make them feel like a valued member of the NovaBrief community

### CATEGORY 5 — FEEDBACK (Negative)
Triggered when: The user is sharing disappointment, criticism, or a negative experience — but not necessarily a complaint.
How to reply:
- Respond with full empathy, zero defensiveness
- Validate their feeling — their experience is real and matters
- Thank them honestly for helping NovaBrief improve
- Offer support or a next step where possible
- Close on a warm, forward-looking note

---
## YOUR REPLY FORMAT (Every Email Must Follow This)

Hi [User's First Name / "there" if name not found],

[2–3 sentences directly responding to what they wrote — reference their actual message so it feels personal]

[1–2 sentences with resolution, next step, or appreciation]

[1 closing sentence — warm, human, inviting]

Warm regards,
The NovaBrief Team
support@novabrief.tech | novabrief.tech

---
## TONE & STYLE RULES
- Always sound human — never robotic, never copy-paste generic
- Warm, professional, and student-friendly at all times
- Reference what the user actually wrote in your reply
- Keep replies focused: 4–6 sentences unless issue needs more
- Never say "As per your email", "Noted", or "Dear User"
- Never reveal you are an AI unless the user directly asks
- Never make promises you cannot guarantee
"""

def generate_reply_text(name: str, subject: str, message: str) -> str:
    """Uses Groq API to generate an intelligent reply to the user's message."""
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        logger.error("No GROQ_API_KEY found, cannot generate AI reply.")
        return ""

    user_context = f"User Name: {name}\nSubject: {subject}\nMessage:\n{message}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_context}
        ],
        "temperature": 0.4,
        "max_tokens": 512
    }
    
    try:
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        reply = resp.json()['choices'][0]['message']['content'].strip()
        return reply
    except Exception as e:
        logger.error(f"Failed to generate Groq reply: {e}")
        return ""

def process_and_reply_to_contact_message(name: str, email: str, subject: str, message: str):
    """Background task to read contact message, generate AI reply, and send email."""
    try:
        reply_text = generate_reply_text(name, subject, message)
        if not reply_text:
            return
        
        # Convert plain text to simple HTML for email
        html_reply = reply_text.replace('\\n', '<br>').replace('\n', '<br>')
        
        # Add basic email wrapper to match NovaBrief branding
        email_html = f"""
        <html>
        <body style="font-family:Arial,sans-serif;color:#171717;line-height:1.6;font-size:15px;padding:20px;">
            <div style="max-width:600px;margin:0 auto;background:#fff;">
                {html_reply}
            </div>
        </body>
        </html>
        """
        
        reply_subject = f"Re: {subject}" if not subject.lower().startswith("re:") else subject
        
        # Send using the existing email infrastructure in ai_news_agent
        success = send_email(email, reply_subject, email_html)
        if success:
            logger.info(f"Successfully sent AI automated reply to {email}")
        else:
            logger.error(f"Failed to send email to {email}")
    except Exception as e:
        logger.error(f"Error in automated email reply agent: {e}")

def spawn_automated_reply(name: str, email: str, subject: str, message: str):
    """Helper to start the background thread."""
    thread = threading.Thread(target=process_and_reply_to_contact_message, args=(name, email, subject, message), daemon=True)
    thread.start()
