#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract the real WP_API_TOKEN from WordPress
"""
import requests
import os
import json

print("\n" + "="*70)
print("Getting WP_API_TOKEN from WordPress")
print("="*70 + "\n")

# Try different methods to get the token
methods = {
    "verify.php": {
        "url": "https://giftia.es/wp-content/plugins/giftfinder-core/verify.php",
        "parse": "Look for 'WP_API_TOKEN'"
    },
    "status.php": {
        "url": "https://giftia.es/wp-content/plugins/giftfinder-core/status.php",
        "parse": "Look for 'WP_API_TOKEN'"
    },
    "debug.php": {
        "url": "https://giftia.es/wp-content/plugins/giftfinder-core/debug.php",
        "parse": "Look for 'WP_API_TOKEN'"
    },
}

for method_name, info in methods.items():
    try:
        print(f"[{method_name}] Trying: {info['url']}")
        response = requests.get(info['url'], timeout=5, verify=False)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            # Look for token in response
            content = response.text
            
            # Try JSON parse
            try:
                data = json.loads(content)
                if 'WP_API_TOKEN' in data:
                    print(f"  ✓ Found token: {data['WP_API_TOKEN'][:10]}...")
                    print(f"  Full token: {data['WP_API_TOKEN']}")
                else:
                    print(f"  No token in JSON")
            except:
                # Look for in HTML
                if 'WP_API_TOKEN' in content:
                    print(f"  ✓ Token found in HTML")
                    # Extract from content
                    lines = content.split('\n')
                    for line in lines:
                        if 'WP_API_TOKEN' in line:
                            print(f"  Line: {line[:100]}")
                else:
                    print(f"  Token not found in response")
        else:
            print(f"  Error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"  Exception: {str(e)}")
    
    print()

# Direct WordPress API approach
print("[WordPress] Trying direct WordPress REST API...")
try:
    response = requests.get(
        "https://giftia.es/wp-json/wp/v2/settings",
        timeout=5,
        verify=False
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if 'gf_wp_api_token' in data:
            print(f"  ✓ Found token: {data['gf_wp_api_token'][:10]}...")
        else:
            print(f"  No token in REST API settings")
except Exception as e:
    print(f"  Exception: {str(e)}")

print("\n" + "="*70)
print("If token not found above, check WordPress admin panel:")
print("  1. Go to https://giftia.es/wp-admin/admin.php?page=giftia-settings")
print("  2. Find 'Token de API (WP_API_TOKEN)'")
print("  3. Copy the token value")
print("  4. Update Hunter.py line 29: WP_TOKEN = '...'")
print("="*70 + "\n")
