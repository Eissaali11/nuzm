#!/usr/bin/env python3
"""Compress large images to improve performance"""
import os
from PIL import Image
import sys

def compress_images(folder, max_size=(1920, 1920), quality=75):
    """Compress all images in folder"""
    compressed = 0
    saved_bytes = 0
    
    for root, dirs, files in os.walk(folder):
        for filename in files:
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join(root, filename)
                try:
                    original_size = os.path.getsize(filepath)
                    if original_size < 100 * 1024:  # Skip files < 100KB
                        continue
                    
                    img = Image.open(filepath)
                    
                    # Resize if too large
                    if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                        img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # Convert RGBA to RGB for JPEG
                    if filepath.lower().endswith(('.jpg', '.jpeg')) and img.mode == 'RGBA':
                        bg = Image.new('RGB', img.size, (255, 255, 255))
                        bg.paste(img, mask=img.split()[3])
                        img = bg
                    
                    # Save with compression
                    if filepath.lower().endswith(('.jpg', '.jpeg')):
                        img.save(filepath, 'JPEG', quality=quality, optimize=True)
                    else:
                        img.save(filepath, optimize=True)
                    
                    new_size = os.path.getsize(filepath)
                    if new_size < original_size:
                        saved = original_size - new_size
                        saved_bytes += saved
                        compressed += 1
                        print(f"✓ {filename}: {original_size//1024}KB → {new_size//1024}KB")
                    
                except Exception as e:
                    print(f"✗ {filename}: {e}")
    
    print(f"\n=== Summary ===")
    print(f"Compressed: {compressed} files")
    print(f"Saved: {saved_bytes // (1024*1024)} MB")
    return compressed, saved_bytes

if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "static/uploads/handover"
    compress_images(folder)
