from PIL import Image
import os

img_path = r'C:\Users\DELL\.gemini\antigravity\brain\50657c5c-0966-4e79-b441-1a8d3b266ada\nova_saas_logo_v5_1787689603879.jpg'
img = Image.open(img_path).convert('RGB')

# Save as logo.jpg
img.save(os.path.join('static', 'logo.jpg'), 'JPEG', quality=95)

# Generate favicon.ico (multiple sizes)
icon_sizes = [(16,16), (32, 32), (48, 48), (64,64), (128, 128), (256, 256)]
img.save(os.path.join('static', 'favicon.ico'), format='ICO', sizes=icon_sizes)

print('Logo and favicon successfully generated in static directory.')
