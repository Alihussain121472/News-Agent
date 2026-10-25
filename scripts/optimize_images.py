#!/usr/bin/env python3
"""
Image Optimization & WebP Conversion Script.
Optimizes JPEG and PNG images and generates compressed WebP versions.
"""

import os
from pathlib import Path
try:
    from PIL import Image
except ImportError:
    Image = None

def optimize_image(image_path: Path, max_dimension=1600, webp_quality=82, jpeg_quality=82):
    orig_size = image_path.stat().st_size
    name = image_path.name.lower()
    ext = image_path.suffix.lower()

    if ext not in ('.jpg', '.jpeg', '.png'):
        return

    try:
        with Image.open(image_path) as img:
            # Check dimensions and resize if excessively large
            w, h = img.size
            needs_resize = w > max_dimension or h > max_dimension
            if needs_resize:
                ratio = min(max_dimension / w, max_dimension / h)
                new_w, new_h = int(w * ratio), int(h * ratio)
                resample = getattr(Image, 'Resampling', Image).LANCZOS
                img_resized = img.resize((new_w, new_h), resample)
            else:
                img_resized = img.copy()

            # Generate WebP version
            webp_path = image_path.with_suffix('.webp')
            if img_resized.mode in ('RGBA', 'LA'):
                img_resized.save(webp_path, 'WEBP', quality=webp_quality, method=6)
            else:
                rgb_img = img_resized.convert('RGB')
                rgb_img.save(webp_path, 'WEBP', quality=webp_quality, method=6)

            webp_size = webp_path.stat().st_size

            # If image was resized or re-compressible, optimize the original format as well
            if needs_resize or ext in ('.jpg', '.jpeg'):
                if ext in ('.jpg', '.jpeg'):
                    rgb_img = img_resized.convert('RGB')
                    rgb_img.save(image_path, 'JPEG', quality=jpeg_quality, optimize=True)
                elif ext == '.png':
                    img_resized.save(image_path, 'PNG', optimize=True)
                new_size = image_path.stat().st_size
            else:
                new_size = orig_size

            saved = orig_size - webp_size
            pct = (saved / orig_size) * 100 if orig_size > 0 else 0
            print(f"[{image_path.name}] {orig_size/1024:.1f}KB -> {webp_size/1024:.1f}KB WebP ({pct:.1f}% saved)")
    except Exception as e:
        print(f"Error optimizing {image_path}: {e}")

def run():
    if Image is None:
        print("Pillow not installed, skipping dynamic image optimization.")
        return
    target_dirs = [
        Path("static"),
        Path("portfolio-review/site-repo/assets/images"),
        Path("portfolio-review/assets/images"),
    ]

    for d in target_dirs:
        if not d.exists():
            continue
        print(f"\n--- Scanning directory: {d} ---")
        for p in d.rglob("*"):
            if p.is_file() and p.suffix.lower() in ('.jpg', '.jpeg', '.png'):
                # Avoid touching git or tmp folders
                if any(x in str(p) for x in ['.git', 'tmp', 'node_modules']):
                    continue
                optimize_image(p)

if __name__ == '__main__':
    run()
