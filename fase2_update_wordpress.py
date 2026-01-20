#!/usr/bin/env python3
"""
FASE 2: ACTUALIZAR WORDPRESS CON ASINs
Lee los ASINs de fase1 y actualiza WordPress con pausas largas
Usa endpoint especializado ?action=update_asin
"""
import json
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

AMAZON_TAG = os.getenv('AMAZON_TAG', 'GIFTIA-21')
WP_TOKEN = os.getenv('WP_API_TOKEN')
WP_API_URL = os.getenv('WP_API_URL')

# Endpoint especializado para actualizar ASINs
UPDATE_ASIN_URL = WP_API_URL + "?action=update_asin"

DELAY_BETWEEN_UPDATES = 2  # 2 segundos entre actualizaciones

print("=" * 70)
print("FASE 2: ACTUALIZAR WORDPRESS CON ASINs")
print("=" * 70)
print(f"API URL: {UPDATE_ASIN_URL}")
print(f"Delay entre updates: {DELAY_BETWEEN_UPDATES}s")

# Cargar ASINs encontrados
try:
    with open('asins_encontrados.json', 'r', encoding='utf-8') as f:
        asins = json.load(f)
except FileNotFoundError:
    print("ERROR: No se encuentra asins_encontrados.json")
    print("Ejecuta primero: python fase1_collect_asins.py")
    exit(1)

print(f"\nASINs a procesar: {len(asins)}")

def update_product(post_id, asin, affiliate_url):
    """Actualizar ASIN en WordPress usando endpoint especializado"""
    
    payload = {
        "post_id": post_id,
        "asin": asin,
        "affiliate_url": affiliate_url
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-GIFTIA-TOKEN': WP_TOKEN
    }
    
    response = requests.post(
        UPDATE_ASIN_URL,
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers=headers,
        timeout=30
    )
    
    if response.status_code in [200, 201]:
        return True, "OK"
    elif response.status_code == 429:
        return False, "RATE_LIMIT"
    else:
        return False, f"Error {response.status_code}: {response.text[:100]}"

# Procesar
success = 0
failed = 0
rate_limited = 0

for i, item in enumerate(asins):
    post_id = item['post_id']
    asin = item['asin']
    affiliate_url = item['affiliate_url']
    
    print(f"[{i+1}/{len(asins)}] {post_id}: {asin}...", end=" ")
    
    ok, msg = update_product(post_id, asin, affiliate_url)
    
    if ok:
        print("✅")
        success += 1
    elif msg == "RATE_LIMIT":
        print("⏳ Rate limit, esperando 30s...")
        rate_limited += 1
        time.sleep(30)
        # Reintentar
        ok, msg = update_product(post_id, asin, affiliate_url)
        if ok:
            print(f"    Reintento: ✅")
            success += 1
        else:
            print(f"    Reintento: ❌ {msg}")
            failed += 1
    else:
        print(f"❌ {msg}")
        failed += 1
    
    time.sleep(DELAY_BETWEEN_UPDATES)

print("\n" + "=" * 70)
print(f"RESUMEN FASE 2:")
print(f"  ✅ Actualizados: {success}")
print(f"  ❌ Fallidos: {failed}")
print(f"  ⏳ Rate limits: {rate_limited}")
print("=" * 70)
