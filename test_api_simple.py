#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the simple API endpoint
"""
import requests
import json

test_product = {
    "title": "Test Product Simple",
    "asin": "B08HXVQG7K",
    "price": "25.99"
}

headers = {
    'Content-Type': 'application/json',
    'X-GIFTIA-TOKEN': 'nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5'
}

url = "https://giftia.es/wp-content/plugins/giftfinder-core/api-test-simple.php"

print(f"Testing: {url}")
print(f"Headers: {headers}")
print(f"Payload: {test_product}\n")

try:
    response = requests.post(url, json=test_product, headers=headers, timeout=10, verify=False)
    print(f"HTTP Status: {response.status_code}")
    print(f"Response: {response.text}\n")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"SUCCESS: {json.dumps(data, indent=2)}")
        except:
            print(f"Response is not JSON")
    else:
        print(f"ERROR: HTTP {response.status_code}")
        
except Exception as e:
    print(f"Exception: {str(e)}")
