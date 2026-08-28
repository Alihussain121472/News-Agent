import os
import re

for root, _, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Find exact occurrences of Ã or Â
            if 'Ã' in content or 'Â' in content or 'â' in content:
                print(f'Mojibake found in {filepath}')
                
                # Replace typical UTF-8 mojibake patterns with dashes or spaces
                # ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â is typically an em-dash
                content = content.replace('ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â', '-')
                content = content.replace('Ã¢â‚¬â€', '-')
                content = content.replace('Ã¢â‚¬â„¢', "'")
                content = content.replace('Ã¢â‚¬Å“', '"')
                content = content.replace('Ã¢â‚¬?', '"')
                
                # Strip remaining weird characters
                content = re.sub(r'[ÃÂâ€š]', '', content)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'Cleaned {filepath}')
