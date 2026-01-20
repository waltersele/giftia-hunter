#!/usr/bin/env python3
"""
GIFTIA - Extractor de Reseñas de Amazon v2
Extrae las 10 mejores reseñas de cada producto y las guarda en WordPress

Uso: python extract_reviews.py [--limit N] [--resume]
"""

import json
import requests
import os
import time
import random
import re
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php"
TOKEN = os.getenv("WP_API_TOKEN")

def setup_driver():
    """Configurar Chrome headless"""
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--lang=es-ES')
    options.add_argument('--accept-language=es-ES,es;q=0.9')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option('prefs', {
        'intl.accept_languages': 'es-ES,es'
    })
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver


def extract_reviews_from_page(driver, asin):
    """Extraer reseñas de la página de producto de Amazon"""
    reviews = []
    
    try:
        # Ir directo a la página del producto (tiene reseñas destacadas)
        url = f"https://www.amazon.es/dp/{asin}"
        driver.get(url)
        time.sleep(random.uniform(2, 4))
        
        # Intentar múltiples selectores de reseñas
        review_selectors = [
            "div[data-hook='review']",
            "div.review",
            "div.a-section.review",
            "div#cm-cr-dp-review-list div[data-hook='review']",
            "div.cr-widget-FocalReviews div[data-hook='review']",
            "div.a-carousel-card div[data-hook='review']",
        ]
        
        review_elements = []
        for selector in review_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    review_elements = elements
                    break
            except:
                continue
        
        # Si no hay reseñas en producto, ir a página de reseñas
        if not review_elements:
            url = f"https://www.amazon.es/product-reviews/{asin}?sortBy=helpful"
            driver.get(url)
            time.sleep(random.uniform(2, 3))
            
            try:
                WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-hook='review']"))
                )
                review_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-hook='review']")
            except:
                pass
        
        for i, review_el in enumerate(review_elements[:10]):
            try:
                review_data = {}
                
                # Rating
                try:
                    rating_selectors = [
                        "i[data-hook='review-star-rating'] span.a-icon-alt",
                        "i.a-icon-star span.a-icon-alt",
                        "span[data-hook='review-star-rating'] span",
                    ]
                    for sel in rating_selectors:
                        try:
                            rating_el = review_el.find_element(By.CSS_SELECTOR, sel)
                            rating_text = rating_el.get_attribute("innerHTML") or rating_el.text
                            match = re.search(r'([0-9]+[,.]?[0-9]*)', rating_text.replace(',', '.'))
                            if match:
                                review_data['rating'] = int(float(match.group(1)))
                                break
                        except:
                            continue
                    if 'rating' not in review_data:
                        review_data['rating'] = 5
                except:
                    review_data['rating'] = 5
                
                # Título
                try:
                    title_selectors = [
                        "a[data-hook='review-title'] span:not(.a-letter-space)",
                        "span[data-hook='review-title']",
                    ]
                    for sel in title_selectors:
                        try:
                            title_el = review_el.find_element(By.CSS_SELECTOR, sel)
                            title_text = title_el.text.strip()
                            if title_text:
                                review_data['title'] = title_text
                                break
                        except:
                            continue
                    if 'title' not in review_data:
                        review_data['title'] = ""
                except:
                    review_data['title'] = ""
                
                # Texto
                try:
                    text_selectors = [
                        "span[data-hook='review-body'] span",
                        "div.review-text span",
                    ]
                    for sel in text_selectors:
                        try:
                            text_el = review_el.find_element(By.CSS_SELECTOR, sel)
                            text_content = text_el.text.strip()
                            if text_content and len(text_content) > 10:
                                review_data['text'] = text_content[:500]
                                break
                        except:
                            continue
                    if 'text' not in review_data:
                        review_data['text'] = ""
                except:
                    review_data['text'] = ""
                
                # Autor
                try:
                    author_el = review_el.find_element(By.CSS_SELECTOR, "span.a-profile-name")
                    review_data['author'] = author_el.text.strip()
                except:
                    review_data['author'] = "Cliente Amazon"
                
                # Compra verificada
                try:
                    review_el.find_element(By.CSS_SELECTOR, "span[data-hook='avp-badge']")
                    review_data['verified'] = True
                except:
                    review_data['verified'] = False
                
                if review_data.get('text'):
                    reviews.append(review_data)
                    
            except Exception as e:
                continue
        
    except Exception as e:
        print(f"⚠️ {str(e)[:30]}")
    
    return reviews


def save_reviews_to_wordpress(post_id, reviews):
    """Guardar reseñas en WordPress"""
    headers = {"X-GIFTIA-TOKEN": TOKEN}
    payload = {
        "post_id": post_id,
        "amazon_reviews": json.dumps(reviews, ensure_ascii=False)
    }
    
    try:
        r = requests.post(
            f"{API_URL}?action=update_reviews",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if r.status_code == 200:
            data = r.json()
            return data.get("success", False)
        return False
    except Exception as e:
        return False


def get_products_with_asins():
    if os.path.exists("asins_encontrados.json"):
        with open("asins_encontrados.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    
    print("=" * 60)
    print("GIFTIA - EXTRACTOR DE RESEÑAS v2")
    print("=" * 60)
    
    productos = get_products_with_asins()
    
    if not productos:
        print("❌ No hay productos")
        return
    
    procesados = set()
    if args.resume and os.path.exists("reviews_procesados.json"):
        with open("reviews_procesados.json", "r") as f:
            procesados = set(json.load(f))
        productos = [p for p in productos if p["post_id"] not in procesados]
        print(f"📋 Continuando... {len(procesados)} ya procesados")
    
    if args.limit:
        productos = productos[:args.limit]
    
    print(f"🔍 Productos: {len(productos)}")
    print()
    
    driver = setup_driver()
    exitos = 0
    sin_reviews = 0
    
    try:
        for i, producto in enumerate(productos, 1):
            post_id = producto["post_id"]
            asin = producto["asin"]
            
            print(f"[{i}/{len(productos)}] {post_id}: {asin}...", end=" ", flush=True)
            
            reviews = extract_reviews_from_page(driver, asin)
            
            if reviews:
                if save_reviews_to_wordpress(post_id, reviews):
                    print(f"✅ {len(reviews)}")
                    exitos += 1
                else:
                    print(f"❌")
            else:
                print(f"⚠️ 0")
                sin_reviews += 1
            
            procesados.add(post_id)
            with open("reviews_procesados.json", "w") as f:
                json.dump(list(procesados), f)
            
            time.sleep(random.uniform(4, 7))
            
            if i % 25 == 0:
                print("🔄 Reiniciando...")
                driver.quit()
                time.sleep(3)
                driver = setup_driver()
    
    except KeyboardInterrupt:
        print("\n⚠️ Interrumpido")
    
    finally:
        driver.quit()
    
    print()
    print("=" * 60)
    print(f"  ✅ Con reseñas: {exitos}")
    print(f"  ⚠️ Sin reseñas: {sin_reviews}")
    print(f"  📋 Procesados: {len(procesados)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
