#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import requests
from pathlib import Path

print("\n" + "="*70)
print("DIAGNOSTIC: Plugin Structure & Installation")
print("="*70)

# 1. Estructura actual del workspace
print("\n[1] Current workspace structure:")
workspace_paths = [
    "c:\\webproject\\giftia\\",
    "c:\\webproject\\giftia\\giftfinder-core\\",
    "d:\\HunterScrap\\",
]

for path in workspace_paths:
    if os.path.exists(path):
        print(f"✓ {path}")
        if path.endswith("giftfinder-core\\"):
            items = os.listdir(path)
            print(f"  Contains: {len(items)} items")
            for item in sorted(items)[:10]:
                print(f"    - {item}")

# 2. Check if this is a WordPress plugin installation
print("\n[2] WordPress installation check:")
wp_files = [
    "c:\\webproject\\wp-load.php",
    "c:\\webproject\\giftia\\wp-load.php", 
    "d:\\wp-load.php",
]

for wp_file in wp_files:
    if os.path.exists(wp_file):
        print(f"✓ Found: {wp_file}")
        with open(wp_file, 'r', errors='ignore') as f:
            content = f.read()[:200]
            if 'wp-load' in content.lower():
                print(f"  This is wp-load.php")

# 3. Check if plugin is in mu-plugins or plugins
print("\n[3] Plugin directory structure:")
plugin_dirs = [
    ("mu-plugins", "c:\\webproject\\wp-content\\mu-plugins\\giftfinder-core\\"),
    ("plugins", "c:\\webproject\\wp-content\\plugins\\giftfinder-core\\"),
    ("plugins (alt)", "c:\\webproject\\giftia\\wp-content\\plugins\\giftfinder-core\\"),
]

for name, path in plugin_dirs:
    if os.path.exists(path):
        print(f"✓ Plugin found in {name}: {path}")
    else:
        print(f"✗ Not found in {name}: {path}")

# 4. Check current installation location
print("\n[4] Current installation location (from workspace):")
current_plugin = "c:\\webproject\\giftia\\giftfinder-core\\api-ingest.php"
if os.path.exists(current_plugin):
    print(f"✓ Current location: {current_plugin}")
    print(f"  Appears to be: Custom/Standalone installation (not standard WordPress plugin)")
    
    # Test if this is causing issues
    print(f"\n  Analyzing paths in api-ingest.php:")
    with open(current_plugin, 'r', errors='ignore') as f:
        content = f.read()
        if "dirname(dirname(dirname" in content:
            print(f"  - Uses relative paths (dirname() calls)")
            print(f"  - May not work if not in standard WordPress directory")

# 5. The actual problem
print("\n[5] ANALYSIS:")
print("""
The plugin is installed in a CUSTOM location:
  c:\\webproject\\giftia\\giftfinder-core\\

But Hunter.py is looking for it at:
  https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php

These don't match!

SOLUTIONS:
A) If giftia.es is NOT at c:\\webproject\\giftia\\:
   - Find the real WordPress root
   - Update Hunter.py WP_API_URL to the correct path
   
B) If giftia.es IS at c:\\webproject\\giftia\\:
   - The plugin needs to be installed at: c:\\webproject\\giftia\\wp-content\\plugins\\giftfinder-core\\
   - Or expose api-ingest.php via a web server route
   
C) Quick fix (if you can't move the plugin):
   - Create a symlink or alias
   - Or update WP_API_URL in Hunter.py to match your actual path
""")

print("="*70 + "\n")
