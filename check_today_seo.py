#!/usr/bin/env python3
"""
Verificar productos de HOY y mostrar estado de campos SEO
"""
import requests
from datetime import date

def get_products_today():
    """Obtener todos los productos publicados hoy."""
    today_str = date.today().strftime('%Y-%m-%d')
    
    # Usar REST API de WordPress para obtener productos de hoy
    base_url = 'https://giftia.es/wp-json/wp/v2/gf_gift'
    
    products = []
    page = 1
    
    while True:
        params = {
            'per_page': 100,
            'page': page,
            'status': 'publish',
            'after': f'{today_str}T00:00:00',
            'before': f'{today_str}T23:59:59'
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"Error obteniendo página {page}: {response.status_code}")
                break
                
            page_products = response.json()
            
            if not page_products:
                break
                
            products.extend(page_products)
            print(f"Página {page}: {len(page_products)} productos")
            
            if len(page_products) < 100:
                break
                
            page += 1
            
        except Exception as e:
            print(f"Error: {e}")
            break
    
    return products

def check_seo_fields(product):
    """Verificar campos SEO de un producto."""
    meta = product.get('meta', {})
    title = product.get('title', {}).get('rendered', 'Sin título')
    product_id = product.get('id', 'N/A')
    
    # Campos SEO v51 críticos
    seo_fields = [
        '_gf_seo_title',
        '_gf_meta_description', 
        '_gf_h1_title',
        '_gf_short_description',
        '_gf_expert_opinion',
        '_gf_pros',
        '_gf_cons',
        '_gf_full_description',
        '_gf_who_is_for',
        '_gf_faqs',
        '_gf_verdict',
        '_gf_seo_slug'
    ]
    
    missing_fields = []
    empty_fields = []
    
    for field in seo_fields:
        value = meta.get(field, '')
        if field not in meta:
            missing_fields.append(field)
        elif not value or str(value).strip() == '':
            empty_fields.append(field)
    
    return {
        'id': product_id,
        'title': title,
        'missing_fields': missing_fields,
        'empty_fields': empty_fields,
        'has_seo': len(missing_fields) == 0 and len(empty_fields) == 0,
        'total_meta_fields': len(meta)
    }

def main():
    today_str = date.today().strftime('%Y-%m-%d')
    print(f"🔍 Verificando productos de {today_str}...")
    print("="*60)
    
    products = get_products_today()
    
    if not products:
        print("❌ No se encontraron productos de hoy")
        return
    
    print(f"📦 Total productos encontrados: {len(products)}")
    print()
    
    products_without_seo = []
    
    for product in products:
        seo_status = check_seo_fields(product)
        
        print(f"Producto ID: {seo_status['id']}")
        print(f"Título: {seo_status['title'][:60]}...")
        print(f"Total meta fields: {seo_status['total_meta_fields']}")
        print(f"Tiene SEO completo: {'✅ SÍ' if seo_status['has_seo'] else '❌ NO'}")
        
        if seo_status['missing_fields']:
            print(f"  Campos faltantes: {', '.join(seo_status['missing_fields'])}")
        
        if seo_status['empty_fields']:
            print(f"  Campos vacíos: {', '.join(seo_status['empty_fields'])}")
            
        if not seo_status['has_seo']:
            products_without_seo.append(seo_status)
            
        print("-" * 40)
    
    print(f"\n📊 RESUMEN:")
    print(f"   Total productos: {len(products)}")
    print(f"   Con SEO completo: {len(products) - len(products_without_seo)}")
    print(f"   Sin SEO completo: {len(products_without_seo)}")
    
    if products_without_seo:
        print(f"\n❌ Productos que necesitan SEO:")
        for product in products_without_seo:
            print(f"   ID {product['id']}: {product['title'][:50]}...")

if __name__ == "__main__":
    main()