#!/usr/bin/env python3
"""
Test: Captura 3 productos de Amazon y los procesa con Gemini.
Muestra el contenido SEO generado (seo_content, marketing_title, etc.)
"""

import sys
import time
import json

# Importar módulos del hunter
from hunter import (
    driver, logger, parse_price, add_to_pending_queue, get_pending_count,
    AMAZON_TAG, By
)
from process_queue import process_product, get_next_from_queue, classify_batch_with_gemini, get_batch_from_queue

def capture_products(max_products=3):
    """Captura productos de Amazon y los añade a la cola."""
    
    logger.info("🧪 PRUEBA: Capturando productos de Amazon")
    
    # Búsqueda de gadgets regalo
    amazon_url = 'https://www.amazon.es/s?k=auriculares+bluetooth&s=review-rank'
    logger.info(f"URL: {amazon_url}")
    
    driver.get(amazon_url)
    time.sleep(4)
    
    # Scroll para cargar más
    driver.execute_script('window.scrollTo(0, 800);')
    time.sleep(2)
    
    # Buscar productos
    items = driver.find_elements(By.CSS_SELECTOR, 'div[data-component-type="s-search-result"]')
    logger.info(f"Encontrados {len(items)} resultados en página")
    
    captured = 0
    for idx, item in enumerate(items[:15]):  # Revisar los primeros 15
        if captured >= max_products:
            break
            
        try:
            asin = item.get_attribute('data-asin')
            if not asin or len(asin) < 10:
                logger.debug(f"  [{idx}] Sin ASIN válido")
                continue
            
            # Título - intentar múltiples selectores
            title = None
            for sel in ['h2 a span', 'h2 span', '.a-text-normal']:
                try:
                    title_elem = item.find_element(By.CSS_SELECTOR, sel)
                    title = title_elem.text.strip()
                    if title:
                        break
                except:
                    pass
            
            if not title or len(title) < 10:
                logger.debug(f"  [{idx}] Sin título válido")
                continue
            
            logger.info(f"  [{idx}] Encontrado: {title[:50]}...")
            
            # Precio - intentar múltiples selectores
            price = 0
            for sel in ['.a-price .a-offscreen', '.a-price-whole']:
                try:
                    price_elem = item.find_element(By.CSS_SELECTOR, sel)
                    price_text = price_elem.get_attribute('innerHTML') or price_elem.text
                    price = parse_price(price_text)
                    if price > 0:
                        break
                except:
                    pass
            
            logger.info(f"       Precio: €{price}")
            
            if price < 15 or price > 200:
                logger.info(f"       ❌ Precio fuera de rango")
                continue
            
            # Imagen
            try:
                img_elem = item.find_element(By.CSS_SELECTOR, 'img.s-image')
                image = img_elem.get_attribute('src')
            except:
                image = ''
            
            # Rating
            rating = 0
            try:
                rating_elem = item.find_element(By.CSS_SELECTOR, 'span.a-icon-alt')
                rating_text = rating_elem.get_attribute('innerHTML')
                rating = float(rating_text.split()[0].replace(',', '.'))
            except:
                pass
            
            logger.info(f"       Rating: ⭐{rating}")
            
            if rating < 3.5:
                logger.info(f"       ❌ Rating muy bajo")
                continue
            
            # Reviews count
            reviews = 0
            try:
                reviews_elem = item.find_element(By.CSS_SELECTOR, 'span.a-size-base.s-underline-text')
                reviews_text = reviews_elem.text.replace('.', '').replace(',', '')
                reviews = int(''.join(c for c in reviews_text if c.isdigit()) or 0)
            except:
                pass
            
            product = {
                'asin': asin,
                'title': title,
                'price': str(price),
                'image_url': image,
                'affiliate_url': f'https://www.amazon.es/dp/{asin}?tag={AMAZON_TAG}',
                'rating': str(rating),
                'reviews_count': reviews,
                'category': 'Tech',
                'source': 'amazon'
            }
            
            add_to_pending_queue(product)
            captured += 1
            logger.info(f"       ✅ CAPTURADO [{captured}/{max_products}]")
                
        except Exception as e:
            logger.debug(f"  [{idx}] Error: {e}")
            continue
    
    logger.info(f"")
    logger.info(f"📦 Capturados {captured} productos")
    logger.info(f"📭 Cola: {get_pending_count()} productos pendientes")
    return captured


def process_and_show_results():
    """Procesa la cola con Gemini y muestra los resultados SEO."""
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("🤖 PROCESANDO CON GEMINI AI (Gold Master v50)")
    logger.info("=" * 70)
    
    # Obtener productos de la cola
    products = get_batch_from_queue(batch_size=3)
    
    if not products:
        logger.info("⚠️ Cola vacía")
        return
    
    logger.info(f"📦 Procesando {len(products)} productos...")
    
    # Clasificar con Gemini
    results = classify_batch_with_gemini(products)
    
    # Mostrar resultados
    logger.info("")
    logger.info("=" * 70)
    logger.info("📝 CONTENIDO SEO GENERADO")
    logger.info("=" * 70)
    
    if results:
        for i, r in enumerate(results):
            original = products[i] if i < len(products) else {}
            
            logger.info("")
            logger.info(f"{'─' * 60}")
            logger.info(f"📦 PRODUCTO {i+1}: {original.get('title', 'Sin título')[:50]}...")
            logger.info(f"   Precio: €{original.get('price', '?')} | Rating: {original.get('rating', '?')}")
            logger.info(f"{'─' * 60}")
            
            if not r.get('ok', False):
                logger.info(f"   ❌ RECHAZADO (q={r.get('q', 0)}) - No cumple estándares Giftia")
                continue
            
            logger.info(f"")
            logger.info(f"🎯 Marketing Title: {r.get('marketing_title', 'N/A')}")
            logger.info(f"🔍 SEO Title: {r.get('seo_title', 'N/A')}")
            logger.info(f"📝 Meta Description: {r.get('meta_description', 'N/A')[:100]}...")
            logger.info(f"")
            logger.info(f"⭐ Giftia Score: {r.get('giftia_score', 0)}/5")
            logger.info(f"📊 Quality: {r.get('q', 0)}/10")
            logger.info(f"🪝 Hook: {r.get('marketing_hook', 'N/A')}")
            logger.info(f"📦 Categoría: {r.get('category', 'N/A')}")
            logger.info(f"👥 Destinatarios: {r.get('recipients', [])}")
            logger.info(f"🎂 Edades: {r.get('age', [])}")
            logger.info(f"")
            logger.info(f"📋 SEO CONTENT (Long Tail para posicionamiento):")
            logger.info(f"   {'─' * 50}")
            seo_content = r.get('seo_content', '')
            if seo_content:
                for line in seo_content.split('\n'):
                    if line.strip():
                        logger.info(f"   {line}")
            logger.info(f"   {'─' * 50}")
            logger.info(f"")
            logger.info(f"✨ Why Selected (Nota del Curador):")
            logger.info(f"   {r.get('why_selected', 'N/A')}")
            logger.info(f"")
            pros = r.get('pros', [])
            if pros:
                logger.info(f"👍 Pros (Bullets de venta):")
                for pro in pros[:4]:
                    logger.info(f"   • {pro}")
    else:
        logger.info("⚠️ No se obtuvieron resultados de Gemini")


if __name__ == "__main__":
    try:
        # Paso 1: Capturar productos
        captured = capture_products(max_products=3)
        
        if captured > 0:
            # Paso 2: Procesar con Gemini
            process_and_show_results()
        else:
            logger.info("⚠️ No se capturaron productos")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Cancelado por usuario")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        logger.info("🏁 Test completado")
