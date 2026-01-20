#!/usr/bin/env python3
"""
RECUPERAR ASINs DE AMAZON
Busca productos por título en Amazon y extrae el ASIN
"""
import json
import os
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

AMAZON_TAG = os.getenv('AMAZON_TAG', 'GIFTIA-21')
WP_TOKEN = os.getenv('WP_API_TOKEN')
WP_API_URL = os.getenv('WP_API_URL')

print("=" * 70)
print("RECUPERADOR DE ASINs - Búsqueda en Amazon")
print("=" * 70)
print(f"Amazon Tag: {AMAZON_TAG}")

# Configurar Chrome
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

def search_amazon_for_asin(title, driver):
    """Buscar producto en Amazon y obtener ASIN"""
    # Limpiar título para búsqueda (quitar entidades HTML y caracteres especiales)
    search_title = re.sub(r'&#\d+;', '', title)  # Quitar &#8211; etc
    search_title = re.sub(r'[^\w\s]', ' ', search_title)  # Solo letras y espacios
    search_title = ' '.join(search_title.split()[:8])  # Primeras 8 palabras
    
    search_url = f"https://www.amazon.es/s?k={requests.utils.quote(search_title)}"
    
    try:
        driver.get(search_url)
        time.sleep(2)
        
        # Buscar primer resultado con ASIN
        products = driver.find_elements(By.CSS_SELECTOR, '[data-asin]')
        
        for product in products[:5]:
            asin = product.get_attribute('data-asin')
            if asin and len(asin) == 10 and asin.startswith('B'):
                # Verificar que el título coincide mínimamente
                try:
                    prod_title = product.find_element(By.CSS_SELECTOR, 'h2 span, .a-text-normal').text
                    # Comparar primeras palabras
                    title_words = set(search_title.lower().split()[:4])
                    prod_words = set(prod_title.lower().split()[:4])
                    if len(title_words & prod_words) >= 2:  # Al menos 2 palabras coinciden
                        return asin, prod_title
                except:
                    pass
        
        # Si no encontramos con coincidencia, devolver el primero
        for product in products[:3]:
            asin = product.get_attribute('data-asin')
            if asin and len(asin) == 10 and asin.startswith('B'):
                return asin, "(título no verificado)"
                
    except Exception as e:
        print(f"    Error buscando: {e}")
    
    return None, None

def update_product_with_asin(post_id, asin, title):
    """Actualizar producto en WordPress con el ASIN y affiliate URL"""
    affiliate_url = f"https://www.amazon.es/dp/{asin}?tag={AMAZON_TAG}"
    
    # Obtener datos actuales
    response = requests.get(f"https://giftia.es/wp-json/wp/v2/gf_gift/{post_id}", timeout=30)
    if response.status_code != 200:
        print(f"    Error obteniendo datos: {response.status_code}")
        return False
    
    details = response.json()
    meta = details.get('meta', {})
    
    # Obtener featured image URL
    featured_id = details.get('featured_media', 0)
    image_url = ""
    if featured_id:
        media_response = requests.get(f"https://giftia.es/wp-json/wp/v2/media/{featured_id}", timeout=30)
        if media_response.status_code == 200:
            image_url = media_response.json().get('source_url', '')
    
    # Payload mínimo - usar datos existentes
    payload = {
        "asin": asin,
        "affiliate_url": affiliate_url,
        "image_url": image_url or meta.get('_gf_image_url', ''),
        "title": title,
        "original_title": title,
        "price": str(meta.get('_gf_current_price', 0) or 0),
        "source": "asin-recovery",
        # Usar taxonomías existentes o defaults
        "category": meta.get('_gf_category', 'Tech') or "Tech",
        "ages": meta.get('_gf_ages', ['adultos']) or ['adultos'],
        "occasions": meta.get('_gf_occasions', ['cumpleanos']) or ['cumpleanos'],
        "recipients": meta.get('_gf_recipients', ['amigo']) or ['amigo'],
        # SEO existente
        "seo_title": meta.get('_gf_seo_title', '') or '',
        "meta_description": meta.get('_gf_meta_description', '') or '',
        "short_description": meta.get('_gf_short_description', '') or '',
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-GIFTIA-TOKEN': WP_TOKEN
    }
    
    try:
        response = requests.post(
            WP_API_URL,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers=headers,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            return True
        else:
            print(f"    WP Error: {response.status_code} - {response.text[:100]}")
            return False
    except Exception as e:
        print(f"    Exception: {e}")
        return False

# Cargar productos
with open('productos_a_reprocesar.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

print(f"\nProductos a procesar: {len(products)}")
print("Iniciando Chrome...")

driver = None
try:
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5)
    
    success = 0
    failed = 0
    
    # Procesar en lotes pequeños para test
    TEST_LIMIT = 10  # Cambiar a len(products) para todos
    
    for i, product in enumerate(products[:TEST_LIMIT]):
        post_id = product['id']
        title = product['title']
        
        print(f"\n[{i+1}/{TEST_LIMIT}] Post {post_id}: {title[:50]}...")
        
        # Buscar ASIN en Amazon
        asin, found_title = search_amazon_for_asin(title, driver)
        
        if asin:
            print(f"    ASIN encontrado: {asin}")
            
            # Actualizar en WordPress
            if update_product_with_asin(post_id, asin, title):
                print(f"    ✅ Actualizado con affiliate: amazon.es/dp/{asin}?tag={AMAZON_TAG}")
                success += 1
            else:
                print(f"    ❌ Error actualizando WordPress")
                failed += 1
        else:
            print(f"    ❌ ASIN no encontrado en Amazon")
            failed += 1
        
        time.sleep(2)  # Evitar rate limiting
    
    print("\n" + "=" * 70)
    print(f"RESUMEN: {success} actualizados, {failed} fallidos")
    print("=" * 70)

finally:
    if driver:
        driver.quit()
