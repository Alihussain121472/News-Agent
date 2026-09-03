import re
with open("web_server.py", "r", encoding="utf-8") as f:
    content = f.read()

pattern = r"@app\.route\('/api/temp/get-logs'[\s\S]*?def temp_get_logs\(\):[\s\S]*?return jsonify\(db\.get_recent_email_logs\(limit=5\)\)\n"
content = re.sub(pattern, "", content)

pattern2 = r"@app\.route\('/api/temp/send-welcome'[\s\S]*?def temp_send_welcome\(\):[\s\S]*?return str\(e\), 500\n"
content = re.sub(pattern2, "", content)

with open("web_server.py", "w", encoding="utf-8") as f:
    f.write(content)
