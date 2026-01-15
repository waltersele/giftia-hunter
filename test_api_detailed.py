#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test API with detailed debugging
"""
import requests
import json

print("\n" + "="*70)
print("Testing API with detailed debugging")
print("="*70 + "\n")

# Datos del test
test_product = {
    "title": "[TEST] Lámpara Luna 3D 16 Colores",
    "asin": "B08HXVQG7K",
    "price": "25.99",
    "original_price": "29.99",
    "image_url": "https://via.placeholder.com/200",
    "url": "https://www.amazon.es/s?k=test",
    "rating": 4.5,
    "reviews": 100,
    "in_stock": True,
    "gift_score": 75,
    "gift_categories": ["Tech"],
    "reason": "Test para debugging API",
    "description": "Hermosa lámpara decorativa con múltiples colores LED"
}

# Headers
headers = {
    'Content-Type': 'application/json',
    'X-GIFTIA-TOKEN': 'nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5'
}

api_url = "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php"

print(f"URL: {api_url}")
print(f"Method: POST")
print(f"Headers: {json.dumps(headers, indent=2)}")
print(f"Payload: {json.dumps(test_product, indent=2)}")
print()

try:
    response = requests.post(
        api_url,
        json=test_product,
        headers=headers,
        timeout=10,
        verify=False
    )
    
    print(f"HTTP Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: '{response.text}'")
    print(f"Response Length: {len(response.text)} bytes")
    
    # Try to parse JSON
    if response.text:
        try:
            data = response.json()
            print(f"\nJSON Response:\n{json.dumps(data, indent=2)}")
        except:
            print(f"\nNot JSON, raw text:\n{response.text[:500]}")
    
    # Analyze HTTP 500
    if response.status_code == 500:
        print("\n" + "="*70)
        print("HTTP 500 ERROR - Server Error")
        print("="*70)
        print("The API returned HTTP 500 but no error message.")
        print("This indicates a PHP fatal error or exception.")
        print("\nPossible causes:")
        print("1. Missing required POST parameters")
        print("2. Invalid data format")
        print("3. PHP error (check server logs)")
        print("4. Missing ASIN validation")
        print("\nTrying alternative formats...")
        
        # Try with required fields only
        minimal = {
            "asin": "B08HXVQG7K",
            "title": "Test Product",
            "price": "25.99"
        }
        
        print(f"\nMinimal payload: {json.dumps(minimal)}")
        response2 = requests.post(
            api_url,
            json=minimal,
            headers=headers,
            timeout=10,
            verify=False
        )
        print(f"Status: {response2.status_code}")
        print(f"Body: {response2.text}")
    
except Exception as e:
    print(f"ERROR: {str(e)}")

print("\n" + "="*70 + "\n")
