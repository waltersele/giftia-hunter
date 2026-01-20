#!/usr/bin/env python3
"""Revisar affiliate URLs de productos existentes"""
import json
import requests

with open('productos_a_reprocesar.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

print('Revisando affiliate URLs de los productos...\n')

con_aff = 0
sin_aff = 0
con_asin = 0
sin_asin = 0

for i, p in enumerate(products[:30]):
    post_id = p['id']
    try:
        r = requests.get(f'https://giftia.es/wp-json/wp/v2/gf_gift/{post_id}', timeout=10)
        meta = r.json().get('meta', {})
        aff = meta.get('_gf_affiliate_url', '')
        asin = meta.get('_gf_asin', '')
        
        if aff:
            con_aff += 1
        else:
            sin_aff += 1
            
        if asin:
            con_asin += 1
        else:
            sin_asin += 1
        
        status_aff = 'SI' if aff else 'NO'
        status_asin = asin[:12] if asin else 'VACIO'
        print(f'{post_id}: ASIN={status_asin:14} AffURL={status_aff}')
        
        if aff:
            print(f'         URL: {aff[:80]}...')
            
    except Exception as e:
        print(f'{post_id}: Error: {e}')

print(f'\n--- RESUMEN ---')
print(f'Con affiliate URL: {con_aff}')
print(f'Sin affiliate URL: {sin_aff}')
print(f'Con ASIN: {con_asin}')
print(f'Sin ASIN: {sin_asin}')
