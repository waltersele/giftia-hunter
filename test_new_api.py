#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the new REST API endpoint for product ingestion
"""
import requests
import json

test_product = {
    "title": "[TEST] Lámpara Luna 3D 16 Colores LED",
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
    "reason": "Test para nuevo endpoint REST",
    "description": "Hermosa lámpara decorativa con múltiples colores LED"
}

headers = {
    'Content-Type': 'application/json',
    'X-GIFTIA-TOKEN': 'nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5'
}

# NUEVA RUTA REST API
url = "https://giftia.es/wp-json/giftia/v1/ingest"

print("\n" + "="*70)
print("Testing NEW REST API Endpoint")
print("="*70 + "\n")

print(f"URL: {url}")
print(f"Method: POST")
print(f"Headers: {headers}")
print(f"Payload: {json.dumps(test_product, indent=2, ensure_ascii=False)}")
print()

try:
    response = requests.post(
        url,
        json=test_product,
        headers=headers,
        timeout=10,
        verify=False
    )
    
    print(f"HTTP Status: {response.status_code}")
    print(f"Response Text:\n{response.text}\n")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print("✓ SUCCESS!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            print(f"Response is not JSON: {response.text[:100]}")
    else:
        print(f"ERROR: HTTP {response.status_code}")
        if response.text:
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error response: {response.text}")
        
except Exception as e:
    print(f"Exception: {str(e)}")

print("\n" + "="*70 + "\n")
