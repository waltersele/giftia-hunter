#!/usr/bin/env python3
"""
Test de ingesta a WordPress con campos SEO v51.
Envía un producto simulado procesado por Gemini a la API de WordPress.
"""

import sys
import json
import time
import requests
from dotenv import load_dotenv
import os

sys.path.insert(0, '.')
load_dotenv()

# Configuración (fallback igual que hunter.py)
WP_API_URL = os.getenv('WP_API_URL', 'https://giftia.es/wp-json/giftia/v1/ingest')
WP_API_TOKEN = os.getenv('WP_API_TOKEN', 'nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5')

# Producto de prueba
TEST_PRODUCT = {
    'asin': 'TEST-SEO-V51',
    'title': 'Auriculares Bluetooth Sony WH-1000XM5 con Cancelación de Ruido',
    'price': '349',
    'image_url': 'https://example.com/sony-headphones.jpg',
    'affiliate_url': 'https://www.amazon.es/dp/B09XYZ1234?tag=giftiaes-21',
    'rating': '4.7',
    'reviews_count': 15234,
    'category': 'Tech',
    'source': 'amazon'
}

def test_ingest():
    """Testea el flujo completo: Gemini -> WordPress."""
    
    print("=" * 80)
    print("🧪 TEST: Ingesta WordPress con SEO v51")
    print("=" * 80)
    print()
    
    # 1. Verificar configuración
    print("📋 Verificando configuración...")
    print(f"   API URL: {WP_API_URL}")
    print(f"   Token: {'✅ Configurado' if WP_API_TOKEN else '❌ No configurado'}")
    print()
    
    if not WP_API_TOKEN:
        print("❌ Error: WP_API_TOKEN no configurado en .env")
        return
    
    # 2. Procesar con Gemini
    print("🤖 Procesando producto con Gemini v51...")
    try:
        from process_queue import classify_batch_with_gemini
        
        start = time.time()
        results = classify_batch_with_gemini([TEST_PRODUCT])
        elapsed = time.time() - start
        
        print(f"   ⏱️ Tiempo Gemini: {elapsed:.2f}s")
        
        if not results:
            print("❌ Error: Gemini no devolvió resultados")
            return
            
        result = results[0]
        print("   ✅ Gemini procesó el producto correctamente")
        
    except Exception as e:
        print(f"❌ Error con Gemini: {e}")
        return
    
    # 3. Mostrar campos SEO generados
    print()
    print("📊 Campos SEO generados:")
    seo_fields = [
        'seo_title', 'meta_description', 'h1_title', 'short_description',
        'expert_opinion', 'pros', 'cons', 'full_description',
        'who_is_for', 'faqs', 'verdict', 'slug'
    ]
    
    for field in seo_fields:
        value = result.get(field, '')
        if isinstance(value, list):
            count = len(value)
            print(f"   {field}: {count} items")
        elif isinstance(value, str):
            words = len(value.split()) if value else 0
            chars = len(value) if value else 0
            print(f"   {field}: {words} palabras / {chars} chars")
        else:
            print(f"   {field}: {value}")
    
    # 4. Preparar payload para WordPress
    print()
    print("📦 Preparando payload para WordPress...")
    
    payload = {
        'asin': result.get('asin', TEST_PRODUCT['asin']),
        'title': result.get('title', TEST_PRODUCT['title']),
        'price': str(TEST_PRODUCT['price']),  # WordPress espera string
        'image_url': TEST_PRODUCT['image_url'],
        'affiliate_url': TEST_PRODUCT['affiliate_url'],
        'rating': str(TEST_PRODUCT['rating']),  # WordPress espera string
        'reviews_count': str(TEST_PRODUCT['reviews_count']),  # WordPress espera string
        'source': TEST_PRODUCT['source'],
        
        # Campos SEO v51
        'seo_title': result.get('seo_title', ''),
        'meta_description': result.get('meta_description', ''),
        'h1_title': result.get('h1_title', ''),
        'short_description': result.get('short_description', ''),
        'expert_opinion': result.get('expert_opinion', ''),
        'pros': result.get('pros', []),
        'cons': result.get('cons', []),
        'full_description': result.get('full_description', ''),
        'who_is_for': result.get('who_is_for', ''),
        'faqs': result.get('faqs', []),
        'verdict': result.get('verdict', ''),
        'slug': result.get('slug', ''),
        
        # Taxonomías
        'category': result.get('category', 'Tech'),
        'age_ranges': result.get('age_ranges', []),
        'gender': result.get('gender', 'unisex'),
        'recipients': result.get('recipients', []),
        'occasions': result.get('occasions', []),
        'marketing_hook': result.get('marketing_hook', ''),
        'giftia_rating': result.get('giftia_rating', 4.5),
        'quality_score': result.get('quality_score', 8),
    }
    
    print(f"   Payload preparado: {len(json.dumps(payload))} bytes")
    
    # 5. Enviar a WordPress
    print()
    print("🚀 Enviando a WordPress...")
    
    headers = {
        'Content-Type': 'application/json',
        'X-Giftia-Token': WP_API_TOKEN
    }
    
    try:
        response = requests.post(
            WP_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Producto ingresado correctamente")
            print(f"   📝 Post ID: {data.get('post_id', 'N/A')}")
            print(f"   🔗 URL: {data.get('url', 'N/A')}")
            print(f"   📊 Mensaje: {data.get('message', 'N/A')}")
        else:
            print(f"   ❌ Error: {response.text[:500]}")
            
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
    
    print()
    print("=" * 80)
    print("✅ Test completado")
    print("=" * 80)

if __name__ == '__main__':
    test_ingest()
