#!/usr/bin/env python3
"""
Test directo de Gemini para verificar generación de SEO content.
No usa scraping, usa productos de ejemplo para testear el prompt Gold Master v50.
"""

import sys
import json
import time

# Configurar path para imports
sys.path.insert(0, '.')

# Productos de prueba simulados (como si vinieran de Amazon)
TEST_PRODUCTS = [
    {
        'asin': 'B09XYZ1234',
        'title': 'Auriculares Bluetooth Sony WH-1000XM5 con Cancelación de Ruido Activa',
        'price': '349',
        'image_url': 'https://example.com/sony-headphones.jpg',
        'affiliate_url': 'https://www.amazon.es/dp/B09XYZ1234?tag=giftiaes-21',
        'rating': '4.7',
        'reviews_count': 15234,
        'category': 'Tech',
        'source': 'amazon'
    },
    {
        'asin': 'B08ABC5678',
        'title': 'Set de Café Specialty con Molinillo Manual y Cafetera Chemex',
        'price': '89',
        'image_url': 'https://example.com/coffee-set.jpg',
        'affiliate_url': 'https://www.amazon.es/dp/B08ABC5678?tag=giftiaes-21',
        'rating': '4.5',
        'reviews_count': 2341,
        'category': 'Gourmet',
        'source': 'amazon'
    },
    {
        'asin': 'B07DEF9012',
        'title': 'Lámpara LED Gaming RGB con Sincronización Musical Bluetooth',
        'price': '45',
        'image_url': 'https://example.com/led-lamp.jpg',
        'affiliate_url': 'https://www.amazon.es/dp/B07DEF9012?tag=giftiaes-21',
        'rating': '4.3',
        'reviews_count': 8765,
        'category': 'Gamer',
        'source': 'amazon'
    }
]

def test_gemini_seo():
    """Testea la generación de contenido SEO con Gemini."""
    
    print("=" * 70)
    print("🧪 TEST: Generación SEO con Gemini (Gold Master v50)")
    print("=" * 70)
    print()
    
    # Importar después para ver errores
    try:
        from process_queue import classify_batch_with_gemini, call_gemini
        print("✅ Módulos importados correctamente")
    except Exception as e:
        print(f"❌ Error importando: {e}")
        return
    
    print()
    print(f"📦 Enviando {len(TEST_PRODUCTS)} productos a Gemini...")
    print()
    
    # DEBUG: Ver qué prompt se envía - llamar directamente
    print("🔍 DEBUG: Probando llamada directa a Gemini...")
    test_prompt = """Responde con este JSON exacto:
[{"i":1, "ok":true, "test": "funcionando"}]"""
    
    debug_response = call_gemini(test_prompt)
    print(f"📨 Respuesta debug: {debug_response[:200] if debug_response else 'NONE'}...")
    print()
    
    # Llamar a Gemini
    start_time = time.time()
    results = classify_batch_with_gemini(TEST_PRODUCTS)
    elapsed = time.time() - start_time
    
    print()
    print(f"⏱️ Tiempo de respuesta: {elapsed:.2f}s")
    print()
    
    if not results:
        print("❌ No se obtuvieron resultados de Gemini")
        return
    
    # Mostrar resultados detallados
    print("=" * 70)
    print("📝 RESULTADOS SEO GENERADOS")
    print("=" * 70)
    
    for i, result in enumerate(results):
        product = TEST_PRODUCTS[i] if i < len(TEST_PRODUCTS) else {}
        
        print()
        print(f"{'━' * 70}")
        print(f"📦 PRODUCTO {i+1}: {product.get('title', 'N/A')[:55]}...")
        print(f"   Precio original: €{product.get('price')} | Rating: ⭐{product.get('rating')}")
        print(f"{'━' * 70}")
        
        # Verificar si es None
        if result is None:
            print(f"   ⚠️ Sin resultado de Gemini (None)")
            continue
        
        # El mapeo usa is_good_gift y gift_quality
        if not result.get('is_good_gift', False):
            print(f"   ❌ RECHAZADO - Quality: {result.get('gift_quality', 0)}/10")
            print(f"   Razón: No cumple estándares Giftia (q < 6)")
            continue
        
        print()
        
        # Títulos
        print(f"🎯 MARKETING TITLE (H1):")
        print(f"   {result.get('marketing_title', 'N/A')}")
        print()
        
        print(f"🔍 SEO TITLE (Meta Title):")
        print(f"   {result.get('seo_title', 'N/A')}")
        print()
        
        print(f"📝 META DESCRIPTION:")
        print(f"   {result.get('meta_description', 'N/A')}")
        print()
        
        # Scores
        print(f"📊 SCORES:")
        print(f"   ⭐ Giftia Score: {result.get('giftia_score', 0)}/5")
        print(f"   📈 Quality: {result.get('gift_quality', 0)}/10")
        print()
        
        # Hook
        print(f"🪝 MARKETING HOOK:")
        print(f"   {result.get('marketing_hook', 'N/A')}")
        print()
        
        # Taxonomías (nota: usa 'ages' no 'age')
        print(f"📂 TAXONOMÍAS:")
        print(f"   Categoría: {result.get('category', 'N/A')}")
        print(f"   Destinatarios: {result.get('recipients', [])}")
        print(f"   Edades: {result.get('ages', [])}")
        print(f"   Género: {result.get('gender', 'N/A')}")
        print(f"   Ocasiones: {result.get('occasions', [])}")
        print()
        
        # Precios
        if 'price_range' in result:
            print(f"💰 PRECIOS:")
            pr = result.get('price_range', {})
            print(f"   Actual: €{result.get('current_price', 'N/A')}")
            print(f"   Rango: €{pr.get('min')}-€{pr.get('max')}")
            print()
        
        # Pros (beneficios emocionales)
        print(f"✨ PROS (Beneficios emocionales):")
        pros = result.get('pros', [])
        if isinstance(pros, list):
            for p in pros:
                print(f"   • {p}")
        else:
            print(f"   {pros}")
        print()
        
        # Why Selected
        print(f"💡 WHY SELECTED (Nota del curador):")
        print(f"   {result.get('why_selected', 'N/A')}")
        print()
        
        # SEO CONTENT - El más importante para long tails
        print(f"{'─' * 70}")
        print(f"📋 SEO CONTENT (150-200 palabras para posicionamiento Long Tail):")
        print(f"{'─' * 70}")
        seo_content = result.get('seo_content', '')
        if seo_content:
            # Contar palabras
            word_count = len(seo_content.split())
            print()
            for line in seo_content.split('\n'):
                if line.strip():
                    print(f"   {line}")
            print()
            print(f"   📏 Longitud: {word_count} palabras")
            if 150 <= word_count <= 200:
                print(f"   ✅ Dentro del rango óptimo (150-200 palabras)")
            elif word_count < 150:
                print(f"   ⚠️ Por debajo del mínimo (150 palabras)")
            else:
                print(f"   ⚠️ Por encima del máximo (200 palabras)")
        else:
            print(f"   ⚠️ No se generó seo_content")
        print(f"{'─' * 70}")
        
        # Short description
        print()
        print(f"📖 SHORT DESCRIPTION (Above the fold):")
        print(f"   {result.get('short_description', 'N/A')}")
    
    # Resumen final
    print()
    print("=" * 70)
    print("📊 RESUMEN")
    print("=" * 70)
    approved = sum(1 for r in results if r and r.get('is_good_gift', False))
    rejected = len(results) - approved
    
    print(f"   ✅ Aprobados: {approved}")
    print(f"   ❌ Rechazados: {rejected}")
    print(f"   📦 Total: {len(results)}")
    print()
    
    # Verificar campos SEO
    print(f"🔍 VERIFICACIÓN CAMPOS SEO:")
    fields_to_check = ['marketing_title', 'seo_title', 'meta_description', 'seo_content', 'pros', 'why_selected', 'marketing_hook']
    for field in fields_to_check:
        has_field = sum(1 for r in results if r and r.get(field) and r.get('is_good_gift'))
        status = "✅" if has_field == approved else "⚠️" if has_field > 0 else "❌"
        print(f"   {status} {field}: {has_field}/{approved} productos")
    
    print()

if __name__ == '__main__':
    test_gemini_seo()
