#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import requests
from pathlib import Path

print("=" * 60)
print("DIAGNOSTIC: Checking API errors")
print("=" * 60)

# 1. Test API endpoint directly with better error handling
print("\n[1] Testing API endpoint...")
test_product = {
    "title": "[TEST] Debug Product",
    "asin": "B999999999",
    "price": "99.99",
    "original_price": "129.99",
    "image_url": "https://via.placeholder.com/200",
    "url": "https://www.amazon.es/s?k=test",
    "rating": 4.5,
    "reviews": 100,
    "in_stock": True,
    "gift_score": 75,
    "gift_categories": ["Tech"],
    "reason": "Test product"
}

api_url = "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php"

try:
    response = requests.post(
        api_url,
        json=test_product,
        timeout=10,
        verify=False
    )
    print(f"HTTP Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: '{response.text}'")
    
    if response.status_code == 500:
        print("\n⚠️  API RETURNS HTTP 500 - SERVER ERROR")
        print("Need to check error log on server")
        
except Exception as e:
    print(f"ERROR: {str(e)}")

# 2. Try to read debug.log if accessible
print("\n[2] Checking WordPress debug.log...")
debug_log_paths = [
    "c:\\webproject\\giftia\\wp-content\\debug.log",
    "c:\\webproject\\giftia\\debug.log",
    "C:\\webproject\\giftia\\wp-content\\debug.log"
]

for log_path in debug_log_paths:
    if os.path.exists(log_path):
        print(f"Found: {log_path}")
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            # Last 30 lines
            last_lines = lines[-30:] if len(lines) > 30 else lines
            print(f"\n--- Last {len(last_lines)} lines ---")
            for line in last_lines:
                print(line.rstrip())
        break
else:
    print("debug.log not found in standard locations")

# 3. Check if API file exists
print("\n[3] Checking API file...")
api_file = "c:\\webproject\\giftia\\wp-content\\plugins\\giftfinder-core\\api-ingest.php"
if os.path.exists(api_file):
    print(f"✓ API file exists: {api_file}")
    with open(api_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        if 'ERROR' in content or 'error' in content:
            print("⚠️  'error' keyword found in api-ingest.php")
        if 'die(' in content:
            print("Found die() calls in api-ingest.php")
else:
    print(f"✗ API file not found: {api_file}")

print("\n" + "=" * 60)
