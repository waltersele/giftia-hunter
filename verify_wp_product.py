#!/usr/bin/env python3
"""
Verificar producto en WordPress - obtener post y meta fields
"""
import requests
import json

print("="*60)
print("VERIFICAR PRODUCTO EN WORDPRESS")
print("="*60)

# Verificar el post 1868 directamente via endpoint de edición
url = "https://giftia.es/wp-json/wp/v2/posts/1868"
r = requests.get(url)
print(f"\n1. /wp/v2/posts/1868: {r.status_code}")
if r.status_code == 200:
    print(json.dumps(r.json(), indent=2)[:500])

# Intentar CPT custom
url2 = "https://giftia.es/wp-json/wp/v2/gf_gift/1868"
r2 = requests.get(url2)
print(f"\n2. /wp/v2/gf_gift/1868: {r2.status_code}")
if r2.status_code == 200:
    print(json.dumps(r2.json(), indent=2)[:500])
else:
    print(r2.text[:200])

# Listar CPTs disponibles
url3 = "https://giftia.es/wp-json/wp/v2/types"
r3 = requests.get(url3)
print(f"\n3. CPTs disponibles:")
if r3.status_code == 200:
    types = r3.json()
    for name, info in types.items():
        print(f"   - {name}: {info.get('rest_base', 'N/A')}")

# Intentar listar regalos
url4 = "https://giftia.es/wp-json/wp/v2/gf_gifts"
r4 = requests.get(url4)
print(f"\n4. /wp/v2/gf_gifts: {r4.status_code}")

# Ver la URL del producto directamente
print(f"\n5. Intentar abrir: https://giftia.es/?p=1868")
