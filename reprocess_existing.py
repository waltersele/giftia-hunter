#!/usr/bin/env python3
"""
GIFTIA - Re-procesar productos existentes con Gemini v51
=========================================================

Este script:
1. Obtiene todos los productos publicados de WordPress
2. Enriquece cada uno con Gemini v51 (SEO completo)
3. Actualiza el producto con los nuevos datos

Uso: python reprocess_existing.py
"""

import os
import sys
import json
import time
import requests
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración - usar valores de process_queue.py si no hay .env
WP_API_URL = os.getenv("WP_API_URL", "https://giftia.es/wp-json/giftia/v1/ingest")
WP_UPDATE_SEO_URL = "https://giftia.es/wp-content/plugins/giftfinder-core/api-update-seo.php"
WP_TOKEN = os.getenv("WP_TOKEN", "nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBJw7dAlTUkFH2m3kfA8lY1idsXcz6m-mg")

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Categorías válidas
VALID_CATEGORIES = ["Tech", "Gamer", "Gourmet", "Deporte", "Viajes", "Moda", "Belleza", 
                    "Hogar", "Decoración", "Bienestar", "Lector", "Música", "Arte", 
                    "Fotografía", "Fandom", "Mascotas", "Lujo", "Outdoor", "Cocina"]

def get_published_products():
    """Obtener productos publicados desde WordPress."""
    # Endpoint para listar productos (necesitas crearlo o usar REST API de WP)
    list_url = os.getenv("WP_LIST_URL", "https://giftia.es/wp-json/wp/v2/gf_gift")
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'X-GIFTIA-TOKEN': WP_TOKEN
        }
        
        all_products = []
        page = 1
        per_page = 100
        
        while True:
            response = requests.get(
                f"{list_url}?per_page={per_page}&page={page}&status=publish",
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Error obteniendo productos: {response.status_code}")
                break
            
            products = response.json()
            if not products:
                break
            
            all_products.extend(products)
            print(f"   📦 Página {page}: {len(products)} productos")
            
            # Si hay menos de per_page, es la última página
            if len(products) < per_page:
                break
            
            page += 1
        
        return all_products
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def enrich_with_gemini(product):
    """Enriquecer producto con Gemini v51."""
    title = product.get("title", {}).get("rendered", "")
    
    prompt = f"""Analiza este producto como regalo y genera contenido SEO completo en español.

PRODUCTO: {title}

Responde SOLO con JSON válido (sin markdown):
{{
    "seo_title": "título SEO 50-60 chars con palabra clave",
    "meta_description": "descripción meta 150-160 chars para Google",
    "h1_title": "título H1 persuasivo 40-70 chars",
    "short_description": "descripción above-the-fold 80-120 palabras, gancho emocional, por qué es buen regalo",
    "expert_opinion": "opinión de experto E-E-A-T 100-150 palabras, por qué lo recomiendas",
    "pros": ["5-6 puntos fuertes emocionales, no técnicos"],
    "cons": ["2-3 puntos honestos menores"],
    "full_description": "descripción SEO 400-600 palabras con H2s markdown, experiencia de regalar, para quién es ideal",
    "who_is_for": "buyer persona 80-100 palabras, quién debería regalar esto y a quién",
    "faqs": [
        {{"q": "pregunta frecuente 1", "a": "respuesta útil 50-80 palabras"}},
        {{"q": "pregunta frecuente 2", "a": "respuesta útil 50-80 palabras"}},
        {{"q": "pregunta frecuente 3", "a": "respuesta útil 50-80 palabras"}}
    ],
    "verdict": "veredicto final 50-80 palabras, conclusión honesta",
    "category": "una de: {', '.join(VALID_CATEGORIES)}",
    "gift_quality": 8
}}

IMPORTANTE:
- Escribe en español natural, persuasivo
- Enfócate en la EXPERIENCIA de regalar, no specs técnicos
- Los pros deben ser beneficios emocionales
- El contenido debe posicionar en Google"""

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        # Parsear respuesta
        text = response.text.strip()
        
        # Limpiar markdown si existe
        if text.startswith("```"):
            lines = text.split("\n")
            # Quitar primera y última línea (```json y ```)
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        text = text.strip()
        
        # Limpiar caracteres problemáticos
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        
        # Intentar parsear
        try:
            result = json.loads(text)
            return result
        except json.JSONDecodeError as je:
            # Intentar arreglar JSON truncado o mal formado
            print(f"   ⚠️ JSON malformado, intentando arreglar...")
            
            # Si hay comillas sin escapar, intentar arreglarlas
            import re
            # Guardar para debug
            with open('last_gemini_error.txt', 'w', encoding='utf-8') as f:
                f.write(f"Error: {je}\n\nTexto:\n{text}")
            
            return None
        
    except Exception as e:
        print(f"   ⚠️ Error Gemini: {e}")
        return None

def update_product(post_id, gemini_data, original_product):
    """Actualizar producto en WordPress con datos de Gemini."""
    
    # Obtener título original
    original_title = ""
    title_obj = original_product.get("title", {})
    if isinstance(title_obj, dict):
        original_title = title_obj.get("rendered", "")
    elif isinstance(title_obj, str):
        original_title = title_obj
    
    # Construir payload para api-update-seo.php
    payload = {
        "post_id": post_id,
        
        # SEO Metadata
        "seo_title": gemini_data.get("seo_title", ""),
        "meta_description": gemini_data.get("meta_description", ""),
        "h1_title": gemini_data.get("h1_title", ""),
        
        # Contenido
        "short_description": gemini_data.get("short_description", ""),
        "seo_content": gemini_data.get("full_description", ""),
        "full_description": gemini_data.get("full_description", ""),
        "expert_opinion": gemini_data.get("expert_opinion", ""),
        
        # Pros y Cons
        "pros": gemini_data.get("pros", []),
        "cons": gemini_data.get("cons", []),
        
        # Buyer persona
        "who_is_for": gemini_data.get("who_is_for", ""),
        
        # FAQs
        "faqs": gemini_data.get("faqs", []),
        
        # Veredicto
        "verdict": gemini_data.get("verdict", ""),
        
        # Categoría
        "category": gemini_data.get("category", "Tech"),
        "gift_quality": gemini_data.get("gift_quality", 8)
    }
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'X-GIFTIA-TOKEN': WP_TOKEN,
            'User-Agent': 'GiftiaReprocessor/1.0'
        }
        
        # Usar endpoint de actualización SEO
        response = requests.post(
            WP_UPDATE_SEO_URL,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"   ❌ Error API: {response.status_code} - {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("")
    print("═══════════════════════════════════════════════════")
    print("🔄 GIFTIA - Re-procesar productos con Gemini v51")
    print("═══════════════════════════════════════════════════")
    print("")
    
    # Verificar configuración
    if not WP_TOKEN:
        print("❌ WP_TOKEN no configurado en .env")
        return
    
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY no configurado en .env")
        return
    
    # Obtener productos
    print("📦 Obteniendo productos publicados...")
    products = get_published_products()
    
    if not products:
        print("⚠️ No se encontraron productos")
        return
    
    print(f"\n✅ {len(products)} productos encontrados")
    print("")
    
    # Confirmar
    confirm = input(f"¿Procesar {len(products)} productos con Gemini v51? (s/n): ")
    if confirm.lower() != 's':
        print("Cancelado.")
        return
    
    print("")
    
    # Procesar cada producto
    success = 0
    errors = 0
    
    for i, product in enumerate(products, 1):
        post_id = product.get("id")
        title = product.get("title", {}).get("rendered", "Sin título")[:50]
        
        print(f"[{i}/{len(products)}] 🔄 {title}...")
        
        # Enriquecer con Gemini
        gemini_data = enrich_with_gemini(product)
        
        if not gemini_data:
            print(f"   ⚠️ Sin datos de Gemini, saltando")
            errors += 1
            continue
        
        # Actualizar en WordPress
        if update_product(post_id, gemini_data, product):
            print(f"   ✅ Actualizado")
            success += 1
        else:
            errors += 1
        
        # Rate limiting - 1 segundo entre productos
        time.sleep(1)
    
    print("")
    print("═══════════════════════════════════════════════════")
    print(f"✅ Completado: {success} actualizados, {errors} errores")
    print("═══════════════════════════════════════════════════")

if __name__ == "__main__":
    main()
