#!/usr/bin/env python3
"""
Analizar productos existentes y detectar los que tienen datos incompletos
"""
import requests
import json

print("="*60)
print("ANALISIS DE PRODUCTOS EXISTENTES")
print("="*60)

# Obtener todos los productos (paginado)
all_products = []
page = 1
while True:
    url = f'https://giftia.es/wp-json/wp/v2/gf_gift?per_page=100&page={page}'
    r = requests.get(url)
    if r.status_code != 200:
        break
    products = r.json()
    if not products:
        break
    all_products.extend(products)
    page += 1
    print(f"  Pagina {page-1}: {len(products)} productos")

print(f"\nTotal productos: {len(all_products)}")

# Analizar
sin_categoria = []
sin_edad = []
sin_recipient = []
sin_occasion = []
sin_seo = []

for p in all_products:
    meta = p.get('meta', {})
    pid = p['id']
    title = p.get('title', {}).get('rendered', '')[:50]
    
    if not p.get('gf_category'):
        sin_categoria.append({'id': pid, 'title': title})
    if not p.get('gf_age'):
        sin_edad.append({'id': pid, 'title': title})
    if not p.get('gf_recipient'):
        sin_recipient.append({'id': pid, 'title': title})
    if not p.get('gf_occasion'):
        sin_occasion.append({'id': pid, 'title': title})
    if not meta.get('_gf_seo_title'):
        sin_seo.append({'id': pid, 'title': title})

print(f"\n--- PRODUCTOS CON PROBLEMAS ---")
print(f"  Sin gf_category: {len(sin_categoria)}")
print(f"  Sin gf_age: {len(sin_edad)}")
print(f"  Sin gf_recipient: {len(sin_recipient)}")
print(f"  Sin gf_occasion: {len(sin_occasion)}")
print(f"  Sin _gf_seo_title: {len(sin_seo)}")

# Productos que necesitan reprocesar (sin edad o sin SEO = criterio principal)
problematicos = sin_edad  # Cambiar a sin_edad que tiene 437
print(f"\n--- PRODUCTOS A REPROCESAR: {len(problematicos)} ---")
for p in problematicos[:10]:
    print(f"  [{p['id']}] {p['title']}")
if len(problematicos) > 10:
    print(f"  ... y {len(problematicos)-10} mas")

# Guardar lista para reprocesar
with open('productos_a_reprocesar.json', 'w', encoding='utf-8') as f:
    json.dump(problematicos, f, ensure_ascii=False, indent=2)

print(f"\nLista guardada en productos_a_reprocesar.json")
