#!/usr/bin/env python3
"""
Regenerate all HackWithAI branding assets from the source logo.
Source: /home/kali/HackWithAI/public/logo-mark.png
"""
import subprocess
import os
import sys

BASE = "/home/kali/HackWithAI"
SOURCE = os.path.join(BASE, "public", "logo-mark.png")
PUBLIC = os.path.join(BASE, "public")
TAURI_ICONS = os.path.join(BASE, "packages/desktop/src-tauri/icons")
ICONSET = os.path.join(TAURI_ICONS, "icon.iconset")

def run(cmd):
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}")
        return False
    if result.stdout.strip():
        print(f"  {result.stdout.strip()}")
    return True

def resize(src, dst, size, bg="white"):
    """Resize image to exact dimensions, padding to square first if needed."""
    # First pad to square, then resize
    cmd = f'convert "{src}" -background none -gravity center -extent {size}x{size} -resize {size}x{size} "{dst}"'
    return run(cmd)

def main():
    print("=" * 60)
    print("HackWithAI v2 - Icon Regeneration")
    print("=" * 60)
    print(f"Source: {SOURCE}")
    
    if not os.path.exists(SOURCE):
        print(f"ERROR: Source file not found: {SOURCE}")
        sys.exit(1)
    
    # Get source dimensions
    result = subprocess.run(f'identify "{SOURCE}"', shell=True, capture_output=True, text=True)
    print(f"Source: {result.stdout.strip()}")
    
    # =========================================================
    # 1. PUBLIC/ ASSETS (PWA, Web, Browser)
    # =========================================================
    print("\n--- Public Web Assets ---")
    
    # Create a square version first (pad to square)
    SQUARE = os.path.join(PUBLIC, ".logo-square.png")
    run(f'convert "{SOURCE}" -background none -gravity center -extent 1536x1536 "{SQUARE}"')
    
    # favicon.ico (16x16, 32x32, 48x48 multi-size)
    print("\n  favicon.ico...")
    run(f'convert "{SQUARE}" -resize 16x16 -background none "PNG:{PUBLIC}/favicon-16.png"')
    run(f'convert "{SQUARE}" -resize 32x32 -background none "PNG:{PUBLIC}/favicon-32.png"')
    run(f'convert "{SQUARE}" -resize 48x48 -background none "PNG:{PUBLIC}/favicon-48.png"')
    run(f'convert "{PUBLIC}/favicon-16.png" "{PUBLIC}/favicon-32.png" "{PUBLIC}/favicon-48.png" -background none "{PUBLIC}/favicon.ico"')
    run(f'rm -f "{PUBLIC}/favicon-16.png" "{PUBLIC}/favicon-32.png" "{PUBLIC}/favicon-48.png"')
    
    # apple-touch-icon.png (180x180)
    print("\n  apple-touch-icon.png...")
    run(f'convert "{SQUARE}" -resize 180x180 -background none "{PUBLIC}/apple-touch-icon.png"')
    
    # icon-192x192.png
    print("\n  icon-192x192.png...")
    run(f'convert "{SQUARE}" -resize 192x192 -background none "{PUBLIC}/icon-192x192.png"')
    
    # icon-256x256.png
    print("\n  icon-256x256.png...")
    run(f'convert "{SQUARE}" -resize 256x256 -background none "{PUBLIC}/icon-256x256.png"')
    
    # icon-512x512.png
    print("\n  icon-512x512.png...")
    run(f'convert "{SQUARE}" -resize 512x512 -background none "{PUBLIC}/icon-512x512.png"')
    
    # =========================================================
    # 2. TAURI DESKTOP ICONS
    # =========================================================
    print("\n--- Tauri Desktop Icons ---")
    
    # 32x32.png
    print("\n  32x32.png...")
    run(f'convert "{SQUARE}" -resize 32x32 -background none "{TAURI_ICONS}/32x32.png"')
    
    # 128x128.png
    print("\n  128x128.png...")
    run(f'convert "{SQUARE}" -resize 128x128 -background none "{TAURI_ICONS}/128x128.png"')
    
    # 128x128@2x.png (256x256)
    print("\n  128x128@2x.png...")
    run(f'convert "{SQUARE}" -resize 256x256 -background none "{TAURI_ICONS}/128x128@2x.png"')
    
    # icon.png (1024x1024)
    print("\n  icon.png...")
    run(f'convert "{SQUARE}" -resize 1024x1024 -background none "{TAURI_ICONS}/icon.png"')
    
    # icon.ico (multi-size)
    print("\n  icon.ico...")
    run(f'convert "{SQUARE}" -resize 16x16 -background none "{TAURI_ICONS}/icon-16.png"')
    run(f'convert "{SQUARE}" -resize 32x32 -background none "{TAURI_ICONS}/icon-32.png"')
    run(f'convert "{SQUARE}" -resize 48x48 -background none "{TAURI_ICONS}/icon-48.png"')
    run(f'convert "{SQUARE}" -resize 256x256 -background none "{TAURI_ICONS}/icon-256.png"')
    run(f'convert "{TAURI_ICONS}/icon-16.png" "{TAURI_ICONS}/icon-32.png" "{TAURI_ICONS}/icon-48.png" "{TAURI_ICONS}/icon-256.png" -background none "{TAURI_ICONS}/icon.ico"')
    run(f'rm -f "{TAURI_ICONS}/icon-16.png" "{TAURI_ICONS}/icon-32.png" "{TAURI_ICONS}/icon-48.png" "{TAURI_ICONS}/icon-256.png"')
    
    # icon.icns (macOS)
    print("\n  icon.icns...")
    run(f'convert "{SQUARE}" -resize 1024x1024 -background none "{TAURI_ICONS}/icon-1024.png"')
    run(f'png2icns "{TAURI_ICONS}/icon.icns" "{TAURI_ICONS}/icon-1024.png" 2>/dev/null || convert "{TAURI_ICONS}/icon-1024.png" "{TAURI_ICONS}/icon.icns" 2>/dev/null || echo "  (icon.icns generation skipped - not critical on Linux)"')
    run(f'rm -f "{TAURI_ICONS}/icon-1024.png"')
    
    # =========================================================
    # 3. ICONSET (macOS .iconset)
    # =========================================================
    print("\n--- macOS .iconset ---")
    sizes = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_64x64.png": 64,
        "icon_64x64@2x.png": 128,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
        "icon_1024x1024.png": 1024,
    }
    for name, size in sizes.items():
        dst = os.path.join(ICONSET, name)
        print(f"  {name}...")
        run(f'convert "{SQUARE}" -resize {size}x{size} -background none "{dst}"')
    
    # =========================================================
    # 4. CLEANUP
    # =========================================================
    print("\n--- Cleanup ---")
    run(f'rm -f "{SQUARE}"')
    
    print("\n" + "=" * 60)
    print("Icon regeneration complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
