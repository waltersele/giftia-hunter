#!/usr/bin/env python3
"""
GIFTIA - Procesar 506 productos sin SEO con Gemini v51
====================================================

Este script toma los 506 productos de hoy que NO tienen campos SEO
y los procesa con Gemini para generar todo el contenido SEO v51.
"""

import os
import json
import time
import requests
from datetime import date, timedelta
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

# Configuración
WP_API_URL = "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php"
WP_TOKEN = os.getenv("WP_API_TOKEN", "nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Pacing para no saturar APIs
GEMINI_PACING_SECONDS = 3  # 20 RPM, muy conservador
WORDPRESS_PACING_SECONDS = 2  # 30 RPM

def get_products_without_seo():
    """Obtener productos de hoy sin SEO."""
    today_str = date.today().strftime('%Y-%m-%d')
    
    base_url = 'https://giftia.es/wp-json/wp/v2/gf_gift'
    products_without_seo = []
    page = 1
    
    print(f"🔍 Obteniendo productos de {today_str} sin SEO...")
    
    while True:
        params = {
            'per_page': 100,
            'page': page,
            'status': 'publish',
            'after': f'{today_str}T00:00:00',
            'before': f'{today_str}T23:59:59',
            'orderby': 'id',
            'order': 'asc'
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"Error obteniendo página {page}: {response.status_code}")
                break
                
            products = response.json()
            
            if not products:
                break
            
            # Filtrar los que no tienen SEO
            for product in products:
                meta = product.get('meta', {})
                
                # Verificar si faltan campos SEO críticos
                critical_fields = ['_gf_seo_title', '_gf_meta_description', '_gf_h1_title']
                missing_seo = any(not meta.get(field, '').strip() for field in critical_fields)
                
                if missing_seo:
                    # Extraer ASIN de la URL de afiliado si no está en meta
                    asin = meta.get('_gf_asin', '').strip()
                    if not asin:
                        affiliate_url = meta.get('_gf_affiliate_url', '')
                        if '/dp/' in affiliate_url:
                            import re
                            match = re.search(r'/dp/([A-Z0-9]{10})', affiliate_url)
                            if match:
                                asin = match.group(1)
                    
                    product_data = {
                        'id': product.get('id'),
                        'title': product.get('title', {}).get('rendered', ''),
                        'asin': asin,
                        'price': meta.get('_gf_price', '0'),
                        'meta': meta
                    }
                    products_without_seo.append(product_data)
            
            print(f"  Página {page}: {len(products)} productos, {len([p for p in products if not p.get('meta', {}).get('_gf_seo_title', '').strip()])} sin SEO")
            
            if len(products) < 100:
                break
                
            page += 1
            
        except Exception as e:
            print(f"Error: {e}")
            break
    
    return products_without_seo

def generate_seo_with_gemini(title, price, asin):
    """Generar contenido SEO v51 con Gemini."""
    
    prompt = f"""Eres el curador premium de Giftia.es, experto en crear contenido SEO que convierte visitantes en compradores.

PRODUCTO: {title}
PRECIO: {price}€

Tu misión: Crear CLASIFICACIÓN COMPLETA + contenido SEO v51 irresistible que posicione en Google y genere ventas.

CATEGORÍAS: Tech, Gamer, Gourmet, Deporte, Outdoor, Viajes, Moda, Belleza, Decoración, Zen, Lector, Música, Artista, Fotografía, Friki, Mascotas, Lujo
EDADES: ninos, adolescentes, jovenes, adultos, seniors, abuelos
GÉNEROS: unisex, male, female, kids
DESTINATARIOS: pareja, padre, madre, hermano, hermana, hijo, hija, abuelo, abuela, amigo, amiga, cuñado, jefe, colega, yo
OCASIONES: cumpleanos, navidad, amigo-invisible, san-valentin, aniversario, dia-de-la-madre, dia-del-padre, graduacion, bodas, agradecimiento, sin-motivo
HOOKS PSICOLÓGICOS: core (pasión principal), habitat (mejora entorno), estilo (identidad pública), hedonismo (placer inmediato), wildcard (descubrimiento inesperado)

Responde SOLO JSON válido:
{{
    "is_good_gift": true/false,
    "category": "categoría principal del inventario",
    "target_gender": "género objetivo principal", 
    "ages": ["edad1", "edad2"],
    "recipients": ["destinatario1", "destinatario2"],
    "occasions": ["ocasion1", "ocasion2"],
    "marketing_hook": "hook psicológico principal (core/habitat/estilo/hedonismo/wildcard)",
    "gift_quality": 8,
    "seo_title": "título SEO magnético 50-60 chars que genere clics",
    "meta_description": "meta description irresistible 150-160 chars",
    "h1_title": "título H1 persuasivo 40-70 chars que venda",
    "short_description": "descripción gancho 80-120 palabras que genere deseo inmediato de comprar",
    "expert_opinion": "reseña experta 100-150 palabras que genere confianza y autoridad",
    "pros": ["5 beneficios emocionales irresistibles", "enfoque en experiencia y sensaciones"],
    "cons": ["2-3 consideraciones honestas", "para generar confianza"],
    "full_description": "descripción SEO completa 600-800 palabras con H2s naturales, casos de uso reales, storytelling que emocione",
    "who_is_for": "buyer persona específico 80-100 palabras, perfil psicográfico detallado",
    "faqs": [
        {{"question": "¿Por qué es el regalo perfecto?", "answer": "respuesta emocional"}},
        {{"question": "¿Para qué ocasiones sirve?", "answer": "respuesta específica"}},
        {{"question": "¿Qué lo hace especial?", "answer": "diferenciación clara"}},
        {{"question": "¿Vale la pena el precio?", "answer": "justificación de valor"}}
    ],
    "verdict": "conclusión persuasiva 50-80 palabras que cierre la venta",
    "seo_slug": "url-amigable-max-5-palabras-clave"
}}

IMPORTANTE:
- Solo aprobar productos que realmente son buenos regalos
- Tono emocional, no técnico
- Crear DESEO, no solo informar
- SEO natural optimizado para conversión"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2500
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=45)
        
        if response.status_code == 429:
            print(f"⚠️ Gemini rate limit, esperando 60s...")
            time.sleep(60)
            response = requests.post(url, json=payload, timeout=45)
        
        if response.status_code != 200:
            print(f"❌ Gemini error {response.status_code}: {response.text[:200]}")
            return None
            
        data = response.json()
        text_response = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        # Limpiar respuesta
        text_response = text_response.strip()
        if text_response.startswith("```"):
            import re
            text_response = re.sub(r'^```json?\s*', '', text_response)
            text_response = re.sub(r'\s*```$', '', text_response)
        
        result = json.loads(text_response)
        return result
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON inválido: {text_response[:200]}")
        return None
    except Exception as e:
        print(f"❌ Error Gemini: {e}")
        return None

def update_product_with_seo(product_id, asin, price, seo_data):
    """Actualizar producto en WordPress."""
    
    update_payload = {
        "product_id": product_id,
        "asin": asin,
        "price": price,
        "update_existing": True,
        "title": f"SEO Update for {product_id}",
        **seo_data
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-GIFTIA-TOKEN': WP_TOKEN,
        'User-Agent': 'GiftiaHunter/SEOFixer'
    }
    
    try:
        response = requests.post(
            WP_API_URL,
            data=json.dumps(update_payload, ensure_ascii=False).encode('utf-8'),
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Error WP {response.status_code}: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error actualizando: {e}")
        return False

def main():
    print("🚀 GIFTIA - ARREGLAR 506 PRODUCTOS SIN SEO v51")
    print("="*60)
    
    # 1. Obtener productos sin SEO
    products = get_products_without_seo()
    
    print(f"\n📦 Productos sin SEO encontrados: {len(products)}")
    
    if not products:
        print("✅ Todos los productos ya tienen SEO")
        return
    
    # 2. Confirmar antes de procesar
    print(f"\n⚠️  Esto procesará {len(products)} productos con Gemini")
    print(f"⏱️  Tiempo estimado: {len(products) * (GEMINI_PACING_SECONDS + WORDPRESS_PACING_SECONDS) / 60:.1f} minutos")
    
    confirm = input("\n¿Continuar? (s/N): ").lower().strip()
    if confirm != 's':
        print("Cancelado")
        return
    
    # 3. Procesar productos
    processed = 0
    success = 0
    failed = 0
    
    print(f"\n🧠 Iniciando procesamiento...")
    print(f"⏱️ Pacing: {GEMINI_PACING_SECONDS}s Gemini + {WORDPRESS_PACING_SECONDS}s WordPress")
    print("─" * 60)
    
    for i, product in enumerate(products):
        # Obtener datos del producto con precio válido
        product_id = product['id']
        title = product['title']
        asin = product['asin']
        price = product.get('price', 0)
        
        # Si precio es 0, usar precio por defecto basado en título
        if not price or price == 0:
            if any(word in title.lower() for word in ['luxury', 'premium', 'oro', 'plata', 'diamante']):
                price = 89.99
            elif any(word in title.lower() for word in ['set', 'kit', 'pack', 'bundle']):
                price = 59.99
            elif any(word in title.lower() for word in ['mini', 'pequeño', 'basic']):
                price = 19.99
            else:
                price = 39.99
        
        progress = f"[{i+1}/{len(products)}]"
        print(f"\n{progress} ID {product_id}: {title[:50]}...")
        
        # Generar SEO con Gemini
        seo_data = generate_seo_with_gemini(title, price, asin)
        
        if not seo_data or not seo_data.get('is_good_gift', False):
            print(f"  ⚠️ Gemini rechazó el producto")
            failed += 1
            time.sleep(1)  # Breve pausa
            continue
        
        print(f"  ✅ SEO generado: {seo_data.get('seo_title', '')[:40]}...")
        
        # Actualizar en WordPress
        if update_product_with_seo(product_id, asin, price, seo_data):
            print(f"  ✅ WordPress actualizado")
            success += 1
        else:
            print(f"  ❌ Error actualizando WordPress")
            failed += 1
        
        processed += 1
        
        # Mostrar progreso cada 10
        if processed % 10 == 0:
            print(f"\n📊 Progreso: {processed}/{len(products)} | ✅ {success} éxito | ❌ {failed} fallos")
        
        # Pacing para APIs
        time.sleep(GEMINI_PACING_SECONDS)
        time.sleep(WORDPRESS_PACING_SECONDS)
    
    print(f"\n" + "="*60)
    print(f"🏆 COMPLETADO")
    print(f"   Procesados: {processed}")
    print(f"   Éxitos: {success}")
    print(f"   Fallos: {failed}")
    print(f"   Tasa de éxito: {(success/max(processed,1)*100):.1f}%")

if __name__ == "__main__":
    main()