#!/usr/bin/env python3
"""
GIFTIA - Detector y Verificador de Datos Completos
===================================================
Detecta productos con campos faltantes y los lista para actualización.

CAMPOS OBLIGATORIOS POR PRODUCTO:
=================================

A. DATOS BÁSICOS (Hunter captura desde Amazon):
   1.  title              - Título del producto
   2.  image              - URL de imagen principal
   3.  asin               - ASIN de Amazon
   4.  affiliate_url      - URL de afiliado
   5.  price              - Precio actual
   6.  rating             - Rating de Amazon (1-5)
   7.  reviews_count      - Número de reseñas
   8.  is_prime           - ¿Es Prime? (yes/no)
   9.  free_shipping      - ¿Envío gratis? (yes/no)
   10. delivery_time      - Tiempo de entrega estimado
   11. amazon_reviews     - Array de reseñas extraídas

B. DATOS SEO (Gemini genera):
   12. seo_title          - Título SEO optimizado
   13. meta_description   - Meta description SEO
   14. h1_title           - H1 para la página
   15. short_description  - Descripción breve (headline)
   16. full_description   - Descripción completa HTML
   17. expert_opinion     - Análisis experto (para IA Insight)
   18. pros               - Array de pros (beneficios)
   19. cons               - Array de cons (desventajas)
   20. who_is_for         - Para quién es ideal
   21. faqs               - Array de FAQs [{q: "", a: ""}]
   22. verdict            - Veredicto final

C. TAXONOMÍAS:
   23. category           - Categoría (Tech, Gaming, etc.)
   24. ages               - Edades objetivo
   25. occasions          - Ocasiones (Cumpleaños, Navidad...)
   26. recipients         - Destinatarios (Padre, Madre...)
   27. budget             - Rango de presupuesto

D. CALIDAD:
   28. gift_quality       - Puntuación calidad (1-10)
   29. giftia_score       - Score Giftia (1-5)
   30. marketing_hook     - Hook de marketing

USO:
    python verify_product_data.py [--limit N] [--export] [--fill-missing]
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

# Configuración
INGEST_URL = os.getenv('INGEST_URL', 'https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php')
GIFTIA_TOKEN = os.getenv('GIFTIA_TOKEN', '') or os.getenv('WP_API_TOKEN', '')

# Campos requeridos por categoría
REQUIRED_FIELDS = {
    'basic': [
        ('asin', '_gf_asin', 'ASIN de Amazon'),
        ('affiliate_url', '_gf_affiliate_url', 'URL de afiliado'),
        ('price', '_gf_current_price', 'Precio'),
        ('rating', '_gf_rating', 'Rating Amazon'),
        ('reviews_count', '_gf_reviews', 'Número de reseñas'),
        ('is_prime', '_gf_is_prime', 'Prime'),
        ('free_shipping', '_gf_free_shipping', 'Envío gratis'),
        ('image', '_thumbnail_id', 'Imagen'),
    ],
    'seo': [
        ('seo_title', '_gf_seo_title', 'Título SEO'),
        ('meta_description', '_gf_meta_description', 'Meta description'),
        ('short_description', '_gf_short_description', 'Descripción breve'),
        ('full_description', '_gf_full_description', 'Descripción completa'),
        ('expert_opinion', '_gf_expert_opinion', 'Opinión experta IA'),
        ('pros', '_gf_pros', 'Pros'),
        ('cons', '_gf_cons', 'Cons'),
        ('who_is_for', '_gf_who_is_for', 'Para quién es'),
        ('faqs', '_gf_faqs', 'FAQs'),
        ('verdict', '_gf_verdict', 'Veredicto'),
    ],
    'taxonomies': [
        ('category', 'gf_category', 'Categoría'),
        ('ages', 'gf_age', 'Edades'),
        ('occasions', 'gf_occasion', 'Ocasiones'),
        ('recipients', 'gf_recipient', 'Destinatarios'),
        ('budget', 'gf_budget', 'Presupuesto'),
    ],
    'quality': [
        ('gift_quality', '_gf_gift_quality', 'Calidad regalo'),
        ('giftia_score', '_gf_giftia_score', 'Score Giftia'),
    ],
    'reviews': [
        ('amazon_reviews', '_gf_amazon_reviews', 'Reseñas Amazon'),
    ]
}

def log(msg, level="INFO"):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    symbols = {"INFO": "ℹ", "WARN": "⚠", "ERROR": "✗", "OK": "✓"}
    print(f"[{timestamp}] {symbols.get(level, '•')} {msg}")

def get_all_products():
    """Obtiene todos los productos con sus meta fields"""
    log("Obteniendo productos desde WordPress...")
    
    try:
        response = requests.get(
            f"{INGEST_URL}?action=get_all_products_meta",
            headers={'X-GIFTIA-TOKEN': GIFTIA_TOKEN},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('products', [])
        
        log(f"Error API: {response.status_code}", "ERROR")
        return []
    except Exception as e:
        log(f"Error: {e}", "ERROR")
        return []

def analyze_product(product):
    """Analiza un producto y retorna campos faltantes"""
    missing = defaultdict(list)
    meta = product.get('meta', {})
    taxonomies = product.get('taxonomies', {})
    
    # Verificar campos básicos
    for field_key, meta_key, label in REQUIRED_FIELDS['basic']:
        value = meta.get(meta_key, '')
        if not value or value in ['', '0', 0, None, 'null', 'no']:
            # is_prime y free_shipping pueden ser 'no' válido
            if field_key in ['is_prime', 'free_shipping'] and value == 'no':
                continue
            missing['basic'].append((field_key, label))
    
    # Verificar campos SEO
    for field_key, meta_key, label in REQUIRED_FIELDS['seo']:
        value = meta.get(meta_key, '')
        if not value or value in ['', None, 'null', '[]', '{}']:
            missing['seo'].append((field_key, label))
    
    # Verificar taxonomías
    for field_key, tax_key, label in REQUIRED_FIELDS['taxonomies']:
        terms = taxonomies.get(tax_key, [])
        if not terms:
            missing['taxonomies'].append((field_key, label))
    
    # Verificar calidad
    for field_key, meta_key, label in REQUIRED_FIELDS['quality']:
        value = meta.get(meta_key, '')
        if not value or value in ['', '0', 0, None]:
            missing['quality'].append((field_key, label))
    
    # Verificar reseñas
    reviews = meta.get('_gf_amazon_reviews', '')
    if not reviews or reviews in ['', '[]', 'null', None]:
        missing['reviews'].append(('amazon_reviews', 'Reseñas Amazon'))
    
    return dict(missing) if any(missing.values()) else None

def generate_report(products):
    """Genera reporte de productos con datos faltantes"""
    report = {
        'total_products': len(products),
        'complete': 0,
        'incomplete': 0,
        'by_category': defaultdict(int),
        'products_needing_update': []
    }
    
    field_missing_count = defaultdict(int)
    
    for product in products:
        missing = analyze_product(product)
        
        if missing:
            report['incomplete'] += 1
            
            product_info = {
                'post_id': product.get('id'),
                'title': product.get('title', '')[:50],
                'asin': product.get('meta', {}).get('_gf_asin', ''),
                'missing': missing
            }
            report['products_needing_update'].append(product_info)
            
            # Contar campos faltantes
            for category, fields in missing.items():
                report['by_category'][category] += 1
                for field_key, _ in fields:
                    field_missing_count[field_key] += 1
        else:
            report['complete'] += 1
    
    report['field_missing_count'] = dict(field_missing_count)
    return report

def print_report(report):
    """Imprime reporte formateado"""
    print("\n" + "=" * 70)
    print("       REPORTE DE COMPLETITUD DE DATOS - GIFTIA")
    print("=" * 70)
    
    print(f"\n📊 RESUMEN GENERAL:")
    print(f"   Total productos:     {report['total_products']}")
    print(f"   ✓ Completos:         {report['complete']}")
    print(f"   ✗ Incompletos:       {report['incomplete']}")
    pct = (report['complete'] / report['total_products'] * 100) if report['total_products'] > 0 else 0
    print(f"   Completitud:         {pct:.1f}%")
    
    print(f"\n📁 CATEGORÍAS CON DATOS FALTANTES:")
    for cat, count in sorted(report['by_category'].items(), key=lambda x: -x[1]):
        cat_labels = {
            'basic': 'Datos básicos (Hunter)',
            'seo': 'Contenido SEO (Gemini)',
            'taxonomies': 'Taxonomías',
            'quality': 'Calidad/Score',
            'reviews': 'Reseñas Amazon'
        }
        print(f"   {cat_labels.get(cat, cat):30} {count:4} productos")
    
    print(f"\n🔍 CAMPOS MÁS FRECUENTEMENTE FALTANTES:")
    sorted_fields = sorted(report['field_missing_count'].items(), key=lambda x: -x[1])
    for field, count in sorted_fields[:15]:
        pct = count / report['total_products'] * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"   {field:25} {count:4} ({pct:5.1f}%) {bar}")
    
    print("\n" + "=" * 70)
    
    if report['products_needing_update']:
        print("\n🔧 PRIMEROS 10 PRODUCTOS QUE NECESITAN ACTUALIZACIÓN:")
        for i, p in enumerate(report['products_needing_update'][:10], 1):
            missing_list = []
            for cat, fields in p['missing'].items():
                for field_key, _ in fields:
                    missing_list.append(field_key)
            print(f"\n   {i}. [{p['post_id']}] {p['title']}")
            print(f"      ASIN: {p['asin'] or 'SIN ASIN'}")
            print(f"      Faltan: {', '.join(missing_list[:5])}{'...' if len(missing_list) > 5 else ''}")

def export_report(report, filename):
    """Exporta reporte a JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    log(f"Reporte exportado a {filename}", "OK")

def main():
    parser = argparse.ArgumentParser(description='Verificar completitud de datos de productos')
    parser.add_argument('--limit', type=int, default=0, help='Límite de productos a analizar (0=todos)')
    parser.add_argument('--export', type=str, help='Exportar reporte a archivo JSON')
    parser.add_argument('--export-asins', type=str, help='Exportar ASINs que necesitan actualización')
    parser.add_argument('--only-missing', type=str, help='Filtrar por campo faltante específico')
    args = parser.parse_args()
    
    log("=" * 60)
    log("GIFTIA - Verificador de Datos Completos")
    log("=" * 60)
    
    if not GIFTIA_TOKEN:
        log("ERROR: GIFTIA_TOKEN no configurado", "ERROR")
        sys.exit(1)
    
    products = get_all_products()
    
    if not products:
        log("No se pudieron obtener productos. Verifica el endpoint.", "ERROR")
        print("\nNOTA: Necesitas añadir el endpoint 'get_all_products_meta' a api-ingest.php")
        print("      O usar el script con --local para analizar datos locales.")
        sys.exit(1)
    
    if args.limit > 0:
        products = products[:args.limit]
    
    log(f"Analizando {len(products)} productos...")
    
    report = generate_report(products)
    print_report(report)
    
    if args.export:
        export_report(report, args.export)
    
    if args.export_asins:
        asins = [p['asin'] for p in report['products_needing_update'] if p['asin']]
        with open(args.export_asins, 'w') as f:
            f.write('\n'.join(asins))
        log(f"Exportados {len(asins)} ASINs a {args.export_asins}", "OK")
    
    # Instrucciones finales
    if report['incomplete'] > 0:
        print("\n" + "=" * 70)
        print("   SIGUIENTE PASO: Ejecutar actualización")
        print("=" * 70)
        print("\n   Para productos sin datos básicos (Prime, envío):")
        print("   python update_shipping_info.py --limit 50")
        print("\n   Para productos sin contenido SEO:")
        print("   python process_queue.py --regenerate-seo")
        print("\n   Para productos sin reseñas:")
        print("   python extract_reviews.py --limit 50")

if __name__ == '__main__':
    main()
