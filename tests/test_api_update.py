#!/usr/bin/env python3
"""
GIFTIA - Test API Update para productos existentes
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

WP_API_URL = "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php"
WP_TOKEN = os.getenv("WP_API_TOKEN", "")

def test_product_update():
    """Probar actualización de producto con ASIN extraído."""
    
    # Datos del producto 1871 que vimos
    asin = "B0DW9BG3PL"  # Extraído de la URL
    product_id = 1871
    
    update_payload = {
        "product_id": product_id,
        "asin": asin,
        "price": "49.99",
        "title": "Kaiza 5 Gin Test",
        "update_existing": True,  # Flag para actualizar productos existentes
        "short_description": "Descripción corta de prueba para activar actualización",
        "h1_title": "¡Prueba H1 Title actualizado!",
        "seo_title": "Prueba SEO Title actualizado"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-GIFTIA-TOKEN': WP_TOKEN,
        'User-Agent': 'GiftiaHunter/TestUpdate'
    }
    
    print(f"🔧 Probando actualización producto {product_id}")
    print(f"📦 ASIN: {asin}")
    print(f"📊 Payload: {json.dumps(update_payload, indent=2)}")
    
    try:
        response = requests.post(
            WP_API_URL,
            data=json.dumps(update_payload, ensure_ascii=False).encode('utf-8'),
            headers=headers,
            timeout=30
        )
        
        print(f"\n📈 Status: {response.status_code}")
        print(f"📋 Response: {response.text[:500]}")
        
        if response.status_code == 200:
            print("✅ Actualización exitosa!")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False

if __name__ == "__main__":
    test_product_update()