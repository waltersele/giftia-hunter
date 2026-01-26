#!/usr/bin/env python3
"""Ver estructura completa del post 2943 para encontrar la imagen"""
import requests
import re

r = requests.get('https://giftia.es/wp-json/wp/v2/gf_gift/2943', timeout=30)
data = r.json()

print('=== Campos principales ===')
print(f'ID: {data.get("id")}')
print(f'Title: {data.get("title", {}).get("rendered", "")[:60]}')
print(f'Featured Media: {data.get("featured_media")}')
print(f'Link: {data.get("link")}')

# Ver contenido
content = data.get('content', {}).get('rendered', '')
print(f'\n=== Content (primeros 500 chars) ===')
print(content[:500] if content else "(vacío)")

# Buscar URLs de imágenes
img_urls = re.findall(r'(https?://[^"\s]+\.(jpg|jpeg|png|gif|webp))', content, re.I)
if img_urls:
    print(f'\n=== Imágenes encontradas en content ===')
    for url, ext in img_urls:
        print(f'  {url}')

# Ver featured media
featured_id = data.get('featured_media')
if featured_id and featured_id > 0:
    print(f'\n=== Obteniendo featured media {featured_id} ===')
    media = requests.get(f'https://giftia.es/wp-json/wp/v2/media/{featured_id}', timeout=30)
    if media.status_code == 200:
        media_data = media.json()
        print(f'  URL: {media_data.get("source_url", "N/A")}')
        print(f'  Alt: {media_data.get("alt_text", "N/A")}')
