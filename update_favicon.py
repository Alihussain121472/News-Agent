from PIL import Image
import os

img_path = r'C:\Users\DELL\.gemini\antigravity\brain\50657c5c-0966-4e79-b441-1a8d3b266ada\.user_uploaded\media_1787939937414.png'
img = Image.open(img_path).convert('RGBA')

# Create a proper multi-size favicon.ico (Google loves 48x48 multiples)
sizes = [(48, 48), (96, 96), (144, 144), (192, 192), (256, 256)]
img.save('static/favicon.ico', format='ICO', sizes=sizes)

# Save standard icons for PWA and apple-touch-icon
img.resize((192, 192)).save('static/icon-192.png')
img.resize((512, 512)).save('static/icon-512.png')
img.resize((180, 180)).save('static/apple-touch-icon.png')
img.save('static/logo.png')

print("Favicons and logos successfully generated.")
