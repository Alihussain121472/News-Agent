import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

replacements = [
    (
        "Your Daily Intelligence Briefing", 
        "Tech News and Internship Alerts for Students"
    ),
    (
        "Curated AI news + early alerts for Google, Microsoft, Amazon, NASA student programs - all delivered to your inbox before they launch.",
        "Get daily AI updates and a heads-up on student programs from Google, Microsoft, Amazon, and NASA. We tell you before applications open so you have time to prepare."
    ),
    (
        "One platform. Real-time tech intelligence, elite program access, and AI-powered tools — all in one place.",
        "You are busy with classes and exams. We track the important tech news and internship openings so you don't have to."
    ),
    (
        "One platform. Real-time tech intelligence, elite program access, and AI-powered tools — all in one place.",
        "You are busy with classes and exams. We track the important tech news and internship openings so you don't have to."
    ),
    (
        "One platform. Real-time tech intelligence, elite program access, and AI-powered tools \x97 all in one place.",
        "You are busy with classes and exams. We track the important tech news and internship openings so you don't have to."
    ),
    (
        "Breaking Tech News",
        "Only the Tech News You Need"
    ),
    (
        "Get the latest tech news straight from top companies and CEOs. We filter out the noise so you only see what actually matters.",
        "Read updates directly from top companies and CEOs. We skip the useless articles and show you what actually matters for your career."
    ),
    (
        "Student Program Alerts",
        "Internship Alerts"
    ),
    (
        "Never miss an opportunity. We track internships and learning programs from Google, Microsoft, Meta, and AWS so you can apply first.",
        "We track internships and learning programs from Google, Microsoft, Meta, and AWS. When they start accepting applications, you find out immediately."
    ),
    (
        "Instant Summaries",
        "Fast Article Summaries"
    ),
    (
        "Don't have time to read a long article? Select any story and get a quick, accurate summary of the key takeaways in seconds.",
        "Too busy to read a 10-minute article? Click a button and get a short, accurate summary of the main points in seconds."
    ),
    (
        "Early Advantage",
        "Apply Before Everyone Else"
    ),
    (
        "Get notified about programs days before they officially launch. Prepare your application while everyone else is still finding out.",
        "We tell you about programs days before they officially launch. You can prep your resume while everyone else is just finding out they exist."
    ),
    (
        "We track programs from Google, Microsoft, Amazon, NASA, Deloitte and many more - so you never miss a chance.",
        "We track internships and student programs at Google, Microsoft, Amazon, NASA, and Deloitte. When they are looking for students, you will know."
    ),
    (
        "Get Early Alerts for Google, Microsoft & NASA Programs",
        "Get Early Alerts for Google, Microsoft, and NASA"
    ),
    (
        "Join the student alert list to get launch preparation tips & direct 1-click registration links delivered to your inbox.",
        "Join the list to get application tips and direct registration links sent straight to your inbox."
    ),
    (
        "Exclusive daily AI intelligence briefings and elite student program alerts. Free forever.",
        "Get daily AI news and early alerts for student programs. It is completely free."
    )
]

for old, new in replacements:
    # also handle en-dash/em-dash replacements in text
    old_mod = old.replace("—", "?")
    if old in text:
        text = text.replace(old, new)
    elif old_mod in text:
        text = text.replace(old_mod, new)
    # also try replacing em dash with â€” or whatever weird encoding it has
    else:
        # regex to match despite weird dashes
        pattern = re.escape(old).replace(r'\—', r'.').replace(r'\-', r'.').replace(r'\x97', r'.')
        text = re.sub(pattern, new, text)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated index.html")
