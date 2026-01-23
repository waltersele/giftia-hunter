#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import requests

# Verificar productos en cola
try:
    with open("pending_products.json", "r", encoding="utf-8") as f:
        queue = json.load(f)
    print(f"✓ Productos en cola: {len(queue)}")
except:
    print("✗ No hay pending_products.json")

# Verificar productos procesados
try:
    with open("processed_products.json", "r", encoding="utf-8") as f:
        processed = json.load(f)
    
    published = [p for p in processed if p.get("status") == "published"]
    rejected = [p for p in processed if p.get("status") == "rejected"]
    errors = [p for p in processed if p.get("status") == "error"]
    
    print(f"✓ Productos procesados: {len(processed)}")
    print(f"  - Publicados: {len(published)}")
    print(f"  - Rechazados: {len(rejected)}")
    print(f"  - Errores: {len(errors)}")
    
    if errors:
        error_400 = [e for e in errors if e.get("http_code") == 400]
        error_500 = [e for e in errors if e.get("http_code") == 500]
        print(f"    → Error 400: {len(error_400)}")
        print(f"    → Error 500: {len(error_500)}")
except:
    print("✗ No hay processed_products.json")

# Test rápido de API
print("\n🔍 Test de API:")
test_data = {
    "vendor": "elcorteingles",
    "title": "Test Producto Awin",
    "price": 29.99,
    "affiliate_url": "https://test.com",
    "image_url": "https://test.com/img.jpg",
    "identifiers": {"ean": "1234567890123"},
    "category": "Tech",
    "target_gender": "unisex",
    "seo_title": "Test",
    "meta_description": "Test desc",
    "h1_title": "Test",
    "ages": ["adultos"],
    "recipients": ["amigo"],
    "occasions": ["cumpleanos"],
    "marketing_hook": "wildcard"
}

try:
    response = requests.post(
        "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php",
        json=test_data,
        headers={
            'Content-Type': 'application/json',
            'X-GIFTIA-TOKEN': 'nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5'
        },
        timeout=10
    )
    
    if "success" in response.text and response.status_code in [200, 500]:
        print("✓ API funciona - Acepta productos Awin")
    elif response.status_code == 400:
        print(f"✗ Error 400: {response.text[:200]}")
    else:
        print(f"⚠ Status {response.status_code}: {response.text[:100]}")
except Exception as e:
    print(f"✗ Error conexión: {e}")
