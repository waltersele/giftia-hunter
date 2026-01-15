#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Understand WordPress installation structure
"""
import requests
import re

urls_to_test = [
    ("WordPress Home", "https://giftia.es/"),
    ("WP REST API", "https://giftia.es/wp-json/"),
    ("Admin", "https://giftia.es/wp-admin/"),
    ("Plugin Info", "https://giftia.es/wp-admin/plugins.php"),
    ("Settings", "https://giftia.es/wp-admin/admin.php?page=giftia-settings"),
]

print("\n" + "="*70)
print("WordPress Structure Diagnosis")
print("="*70 + "\n")

for name, url in urls_to_test:
    try:
        print(f"[{name}]")
        print(f"  URL: {url}")
        response = requests.get(url, timeout=5, verify=False)
        print(f"  Status: {response.status_code}")
        
        # Extract useful info
        if response.status_code == 200:
            if "wp-json" in response.text or "WordPress" in response.text:
                print(f"  ✓ WordPress is installed")
            
            # Try to find plugin references
            if "giftfinder" in response.text or "giftia" in response.text:
                print(f"  ✓ Found giftia/giftfinder references")
        elif response.status_code == 404:
            print(f"  ✗ Not found (404)")
        elif response.status_code == 302 or response.status_code == 301:
            print(f"  → Redirects to: {response.headers.get('Location', 'Unknown')}")
        
    except Exception as e:
        print(f"  ERROR: {str(e)[:50]}")
    
    print()

print("="*70)
print("\nKEY FINDINGS:")
print("- WordPress responds at https://giftia.es/")
print("- Plugin files must be in /wp-content/plugins/ or /wp-content/mu-plugins/")
print("- Direct PHP file access (api-ingest.php) won't work unless exposed via WordPress")
print("\nSolution:")
print("1. Option A: Move plugin to standard location")
print("2. Option B: Create WordPress REST API endpoint")
print("3. Option C: Create action hook that Hunter can call")
print("="*70 + "\n")
