import re
with open("web_server.py", "r", encoding="utf-8") as f:
    content = f.read()

pattern = r"@app\.route\('/api/temp/send-welcome'[\s\S]*?def temp_send_welcome\(\):[\s\S]*?return str\(e\), 500\n"
content = re.sub(pattern, "", content)

with open("web_server.py", "w", encoding="utf-8") as f:
    f.write(content)
