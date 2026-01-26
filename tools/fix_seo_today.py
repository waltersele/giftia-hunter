#!/usr/bin/env python3
"""
GIFTIA - Arreglar productos de hoy sin SEO
==========================================

Este script:
1. Obtiene productos de hoy desde nuestra API personalizada
2. Identifica cuáles NO tienen campos SEO v51
3. Los procesa con Gemini y actualiza en WordPress

Uso: python fix_seo_today.py
"""

import os
import json
import time
import requests
from datetime import datetime, date
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

# Configuración
WP_API_URL = "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php"
WP_TOKEN = os.getenv("WP_API_TOKEN", "nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GEMINI_PACING_SECONDS = 2
WORDPRESS_PACING_SECONDS = 1

def check_products_today():
    """Verificar qué productos hay de hoy en WordPress."""
    today = date.today().strftime('%Y-%m-%d')
    
    # Usar nuestro script check_seo.py existente
    import subprocess
    
    print(f"🔍 Verificando productos del {today}...")
    
    try:
        result = subprocess.run([
            'python', 'check_seo.py'
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        output = result.stdout
        print(f"📊 Resultado de check_seo.py:")
        print(output)
        
        return output
        
    except Exception as e:
        print(f"❌ Error ejecutando check_seo.py: {e}")
        return ""

def classify_with_gemini(title, price, asin):
    """Generar contenido SEO v51 con Gemini."""
    
    # Schema válidas desde giftia_schema.json
    categories = ["Tech", "Gamer", "Gourmet", "Deporte", "Outdoor", "Viajes", "Moda", 
                 "Belleza", "Decoración", "Zen", "Lector", "Música", "Artista", 
                 "Fotografía", "Friki", "Mascotas", "Lujo"]
    ages = ["ninos", "adolescentes", "jovenes", "adultos", "seniors", "abuelos"]
    genders = ["unisex", "male", "female", "kids"]
    occasions = ["cumpleanos", "navidad", "amigo-invisible", "san-valentin", 
                "aniversario", "dia-madre", "dia-padre", "graduacion", "bodas", 
                "agradecimiento", "sin-motivo"]
    
    prompt = f"""Eres el curador premium de Giftia.es, especialista en regalos inteligentes.

PRODUCTO: {title}
PRECIO: {price}€

Tu misión: Crear contenido SEO v51 persuasivo que posicione este producto y genere conversiones.

CATEGORÍAS disponibles: {', '.join(categories)}
EDADES objetivo: {', '.join(ages)}
GÉNEROS: {', '.join(genders)}
OCASIONES: {', '.join(occasions)}

Responde SOLO JSON válido (sin markdown):
{{
    "is_good_gift": true/false,
    "category": "UNA de la lista categorías",
    "target_gender": "uno de la lista géneros",
    "target_ages": ["edad1", "edad2"],
    "target_occasions": ["ocasion1", "ocasion2"],
    "seo_title": "título SEO viral 50-60 chars con gancho emocional",
    "meta_description": "descripción meta 150-160 chars que genere clic",
    "h1_title": "título H1 persuasivo 40-70 chars que venda",
    "short_description": "descripción above-the-fold 80-120 palabras, gancho emocional potente, por qué es el regalo perfecto",
    "expert_opinion": "opinión experta E-E-A-T 100-150 palabras, por qué lo recomiendas como curador premium",
    "pros": ["5-6 beneficios emocionales que generen deseo", "enfoque en experiencia no specs"],
    "cons": ["2-3 aspectos honestos a considerar", "para generar confianza"],
    "full_description": "descripción SEO completa 600-800 palabras con H2s naturales, storytelling, casos de uso, optimizada para búsquedas",
    "who_is_for": "buyer persona ideal 80-100 palabras, perfil psicográfico específico",
    "faqs": [
        {{"question": "pregunta frecuente 1", "answer": "respuesta optimizada"}},
        {{"question": "pregunta frecuente 2", "answer": "respuesta optimizada"}},
        {{"question": "pregunta frecuente 3", "answer": "respuesta optimizada"}},
        {{"question": "pregunta frecuente 4", "answer": "respuesta optimizada"}}
    ],
    "verdict": "conclusión persuasiva 50-80 palabras que cierre la venta",
    "seo_slug": "url-amigable-max-5-palabras"
}}

CRITERIOS:
- is_good_gift: Solo true si realmente es un regalo deseable
- Tono persuasivo, no técnico
- Enfocar en emociones y experiencias
- SEO natural, no keyword stuffing
- Generar DESEO no solo informar
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2000
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 429:
            print(f"⚠️ Gemini rate limit, esperando 60s...")
            time.sleep(60)
            response = requests.post(url, json=payload, timeout=30)
        
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
        print(f"✅ Gemini OK: {result.get('seo_title', '')[:50]}...")
        return result
        
    except json.JSONDecodeError:
        print(f"❌ JSON inválido de Gemini: {text_response[:100]}")
        return None
    except Exception as e:
        print(f"❌ Error Gemini: {e}")
        return None

def update_product_seo(asin, seo_data):
    """Actualizar producto en WordPress con datos SEO."""
    
    # Agregar metadatos necesarios para WordPress
    update_data = {
        "asin": asin,
        "action": "update_seo",
        **seo_data
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-GIFTIA-TOKEN': WP_TOKEN
    }
    
    try:
        response = requests.post(
            WP_API_URL,
            data=json.dumps(update_data, ensure_ascii=False).encode('utf-8'),
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ WordPress actualizado: {asin}")
            return True
        else:
            print(f"❌ Error WordPress {response.status_code}: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error actualizando: {e}")
        return False

def main():
    """Función principal."""
    print("🚀 GIFTIA - Arreglar productos sin SEO v51")
    print("="*50)
    
    # 1. Verificar productos de hoy
    check_output = check_products_today()
    
    # 2. Extraer ASINs que necesitan SEO
    # Los productos sin _gf_seo_title aparecen en el output
    import re
    
    # Buscar productos con campos vacíos
    missing_seo_products = []
    lines = check_output.split('\n')
    
    current_product = None
    for line in lines:
        # Buscar ID del producto
        if "Producto ID:" in line:
            current_product = {'id': line.split(':')[1].strip()}
        elif "ASIN:" in line and current_product:
            current_product['asin'] = line.split(':')[1].strip()
        elif "Título:" in line and current_product:
            current_product['title'] = line.split(':', 1)[1].strip()
        elif "Precio:" in line and current_product:
            current_product['price'] = line.split(':')[1].strip().replace('€', '').strip()
        elif "_gf_seo_title:" in line and current_product:
            seo_title_value = line.split(':', 1)[1].strip()
            if not seo_title_value or seo_title_value == "None":
                missing_seo_products.append(current_product.copy())
            current_product = None
    
    print(f"\n📊 Productos sin SEO encontrados: {len(missing_seo_products)}")
    
    if not missing_seo_products:
        print("✅ Todos los productos ya tienen SEO v51")
        return
    
    # 3. Procesar cada producto
    processed = 0
    for product in missing_seo_products:
        asin = product.get('asin', '')
        title = product.get('title', '')
        price = product.get('price', '0')
        
        if not asin or not title:
            continue
            
        print(f"\n🧠 Procesando [{processed+1}/{len(missing_seo_products)}]: {title[:50]}...")
        
        # Generar SEO con Gemini
        seo_data = classify_with_gemini(title, price, asin)
        
        if seo_data and seo_data.get('is_good_gift', False):
            # Actualizar en WordPress
            if update_product_seo(asin, seo_data):
                processed += 1
            
            # Pacing
            time.sleep(WORDPRESS_PACING_SECONDS)
        else:
            print(f"⚠️ Gemini rechazó el producto")
        
        # Pacing para Gemini
        time.sleep(GEMINI_PACING_SECONDS)
    
    print(f"\n🏆 COMPLETADO: {processed} productos actualizados con SEO v51")

if __name__ == "__main__":
    main()