#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST HUNTER - Simular exactamente lo que hace hunter.py
"""

import requests
import json
import sys

# Configuración
WP_TOKEN = "nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5"
WP_API_URL = "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php"

# Producto de test (lo que Hunter enviaría)
test_product = {
    'title': '[TEST] Lámpara Luna 3D - Control Táctil',
    'asin': 'B08HXVQG7K',
    'price': '29.99',
    'image_url': 'https://m.media-amazon.com/images/I/51Test.jpg',
    'vendor': 'amazon',
    'affiliate_url': 'https://amazon.es/dp/B08HXVQG7K?tag=giftia0a-21',
    'description': 'Lámpara LED 3D con diseño de luna realista. Control táctil para 16 colores diferentes.',
}

print("=" * 70)
print("HUNTER TEST - Enviando producto de prueba")
print("=" * 70)
print()

print(f"URL: {WP_API_URL}")
print(f"Token: {WP_TOKEN[:15]}...")
print()

print("Producto a enviar:")
print(json.dumps(test_product, indent=2, ensure_ascii=False))
print()

# Enviar
print("-" * 70)
print("ENVIANDO...")
print("-" * 70)
print()

try:
    response = requests.post(
        WP_API_URL,
        json=test_product,
        headers={
            'Content-Type': 'application/json',
            'X-GIFTIA-TOKEN': WP_TOKEN,
            'User-Agent': 'HunterTest/1.0'
        },
        timeout=30,
        verify=False
    )
    
    print(f"HTTP Status: {response.status_code}")
    print()
    
    try:
        response_json = response.json()
        print("Respuesta de la API:")
        print(json.dumps(response_json, indent=2, ensure_ascii=False))
    except:
        print("Respuesta (text):")
        print(response.text[:500])
    
    print()
    print("=" * 70)
    
    if response.status_code == 200:
        print("✅ ÉXITO - Producto enviado")
        print()
        print("Próximos pasos:")
        print("1. Ve a WordPress Admin → Products → All Gifts")
        print("2. Deberías ver '[TEST] Lámpara Luna 3D' en la lista")
        print("3. Si la ves, Hunter.py funcionará correctamente")
        print()
    else:
        print(f"❌ ERROR - HTTP {response.status_code}")
        print()
        print("Esto significa que la API está rechazando las peticiones.")
        print("Revisa:")
        print("1. wp-content/debug.log para ver el error exacto")
        print("2. El token es correcto? Cópialo de nuevo desde WordPress Admin")
        print("3. El URL de la API es correcto?")
        print()
        
except Exception as e:
    print(f"❌ ERROR DE CONEXIÓN: {e}")
    print()
    print("Verifica:")
    print("1. ¿La URL es correcta?")
    print("2. ¿giftia.es responde?")
    print("3. ¿Hay conexión a internet?")
    print()

print("=" * 70)
