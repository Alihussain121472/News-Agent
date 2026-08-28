import os
for root, _, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            if '/analytics/' in content:
                content = content.replace('/analytics/', '/admin/')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Fixed links in {filepath}")
