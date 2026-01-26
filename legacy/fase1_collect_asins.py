#!/usr/bin/env python3
"""
FASE 1: RECOLECTAR ASINs DE AMAZON
Solo busca en Amazon y guarda los ASINs en un archivo JSON
No toca WordPress para evitar rate limits
"""
import json
import os
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

load_dotenv()

AMAZON_TAG = os.getenv('AMAZON_TAG', 'GIFTIA-21')

print("=" * 70)
print("FASE 1: RECOLECTAR ASINs DE AMAZON")
print("=" * 70)

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
    # Limpiar título para búsqueda
    search_title = re.sub(r'&#\d+;', '', title)
    search_title = re.sub(r'[^\w\s]', ' ', search_title)
    search_title = ' '.join(search_title.split()[:8])
    
    search_url = f"https://www.amazon.es/s?k={requests.utils.quote(search_title)}"
    
    try:
        driver.get(search_url)
        time.sleep(2)
        
        products = driver.find_elements(By.CSS_SELECTOR, '[data-asin]')
        
        for product in products[:5]:
            asin = product.get_attribute('data-asin')
            if asin and len(asin) == 10 and asin.startswith('B'):
                try:
                    prod_title = product.find_element(By.CSS_SELECTOR, 'h2 span, .a-text-normal').text
                    title_words = set(search_title.lower().split()[:4])
                    prod_words = set(prod_title.lower().split()[:4])
                    if len(title_words & prod_words) >= 2:
                        return asin, prod_title
                except:
                    pass
        
        for product in products[:3]:
            asin = product.get_attribute('data-asin')
            if asin and len(asin) == 10 and asin.startswith('B'):
                return asin, "(sin verificar)"
                
    except Exception as e:
        print(f"    Error: {e}")
    
    return None, None

# Cargar productos
with open('productos_a_reprocesar.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

# Cargar progreso existente (para reanudar)
asins_encontrados = []
asins_no_encontrados = []
processed_ids = set()

if os.path.exists('asins_encontrados.json'):
    try:
        with open('asins_encontrados.json', 'r', encoding='utf-8') as f:
            asins_encontrados = json.load(f)
            processed_ids.update(p['post_id'] for p in asins_encontrados)
        print(f"Reanudando: {len(asins_encontrados)} ASINs ya encontrados")
    except:
        pass

if os.path.exists('asins_no_encontrados.json'):
    try:
        with open('asins_no_encontrados.json', 'r', encoding='utf-8') as f:
            asins_no_encontrados = json.load(f)
            processed_ids.update(p['post_id'] for p in asins_no_encontrados)
        print(f"Reanudando: {len(asins_no_encontrados)} no encontrados previos")
    except:
        pass

# Filtrar productos ya procesados
products_pending = [p for p in products if p['id'] not in processed_ids]
print(f"Total productos: {len(products)}")
print(f"Ya procesados: {len(processed_ids)}")
print(f"Pendientes: {len(products_pending)}")
print("Iniciando Chrome...")

def create_driver():
    """Crear nueva instancia de Chrome"""
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5)
    return driver

driver = None
consecutive_errors = 0
MAX_CONSECUTIVE_ERRORS = 3

try:
    driver = create_driver()
    
    for i, product in enumerate(products_pending):
        post_id = product['id']
        title = product['title']
        
        total_processed = len(processed_ids) + i + 1
        print(f"[{total_processed}/{len(products)}] {post_id}: {title[:50]}...", end=" ")
        
        try:
            asin, found_title = search_amazon_for_asin(title, driver)
            consecutive_errors = 0  # Reset en éxito
            
            if asin:
                print(f"✅ {asin}")
                asins_encontrados.append({
                    'post_id': post_id,
                    'title': title,
                    'asin': asin,
                    'affiliate_url': f"https://www.amazon.es/dp/{asin}?tag={AMAZON_TAG}"
                })
            else:
                print("❌")
                asins_no_encontrados.append({
                    'post_id': post_id,
                    'title': title
                })
        except Exception as e:
            print(f"    Error: {e}")
            consecutive_errors += 1
            asins_no_encontrados.append({
                'post_id': post_id,
                'title': title
            })
            
            # Reiniciar Chrome si hay muchos errores
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                print("    [Reiniciando Chrome...]")
                try:
                    driver.quit()
                except:
                    pass
                time.sleep(5)
                driver = create_driver()
                consecutive_errors = 0
        
        # Guardar progreso cada 10 productos
        if (i + 1) % 10 == 0:
            with open('asins_encontrados.json', 'w', encoding='utf-8') as f:
                json.dump(asins_encontrados, f, ensure_ascii=False, indent=2)
            with open('asins_no_encontrados.json', 'w', encoding='utf-8') as f:
                json.dump(asins_no_encontrados, f, ensure_ascii=False, indent=2)
            print(f"    [Guardado progreso: {len(asins_encontrados)} ASINs]")
        
        time.sleep(2)

finally:
    if driver:
        driver.quit()
    
    # Guardar resultados finales
    with open('asins_encontrados.json', 'w', encoding='utf-8') as f:
        json.dump(asins_encontrados, f, ensure_ascii=False, indent=2)
    
    with open('asins_no_encontrados.json', 'w', encoding='utf-8') as f:
        json.dump(asins_no_encontrados, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 70)
print(f"RESUMEN FASE 1:")
print(f"  ✅ ASINs encontrados: {len(asins_encontrados)}")
print(f"  ❌ No encontrados: {len(asins_no_encontrados)}")
print(f"\nArchivos guardados:")
print(f"  - asins_encontrados.json")
print(f"  - asins_no_encontrados.json")
print("=" * 70)
print("\nEjecuta 'python update_affiliate_urls.py' para actualizar WordPress")
