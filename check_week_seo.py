#!/usr/bin/env python3
"""
Verificar productos de los últimos 7 días y mostrar estado de campos SEO
"""
import requests
from datetime import date, timedelta

def get_products_last_days(days=7):
    """Obtener todos los productos publicados en los últimos N días."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    print(f"🔍 Buscando productos desde {start_str} hasta {end_str}...")
    
    # Usar REST API de WordPress
    base_url = 'https://giftia.es/wp-json/wp/v2/gf_gift'
    
    products = []
    page = 1
    
    while True:
        params = {
            'per_page': 100,
            'page': page,
            'status': 'publish',
            'after': f'{start_str}T00:00:00',
            'before': f'{end_str}T23:59:59',
            'orderby': 'date',
            'order': 'desc'
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
            print(f"  Página {page}: {len(page_products)} productos")
            
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
    date_created = product.get('date', 'N/A')[:10]  # Solo fecha
    
    # Campos SEO v51 críticos
    seo_fields = [
        '_gf_seo_title',
        '_gf_meta_description', 
        '_gf_h1_title',
        '_gf_short_description',
        '_gf_expert_opinion'
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
        'date': date_created,
        'missing_fields': missing_fields,
        'empty_fields': empty_fields,
        'has_seo': len(missing_fields) == 0 and len(empty_fields) == 0,
        'total_meta_fields': len(meta),
        'asin': meta.get('_gf_asin', 'N/A')
    }

def main():
    print("🔍 VERIFICANDO PRODUCTOS ÚLTIMOS 7 DÍAS")
    print("="*60)
    
    products = get_products_last_days(7)
    
    if not products:
        print("❌ No se encontraron productos")
        return
    
    print(f"📦 Total productos encontrados: {len(products)}")
    print()
    
    # Agrupar por fecha
    products_by_date = {}
    products_without_seo = []
    
    for product in products:
        seo_status = check_seo_fields(product)
        date_key = seo_status['date']
        
        if date_key not in products_by_date:
            products_by_date[date_key] = {'total': 0, 'with_seo': 0, 'without_seo': 0}
        
        products_by_date[date_key]['total'] += 1
        
        if seo_status['has_seo']:
            products_by_date[date_key]['with_seo'] += 1
        else:
            products_by_date[date_key]['without_seo'] += 1
            products_without_seo.append(seo_status)
    
    # Mostrar resumen por fecha
    print("📅 RESUMEN POR FECHA:")
    for date_key in sorted(products_by_date.keys(), reverse=True):
        data = products_by_date[date_key]
        print(f"  {date_key}: {data['total']} productos | ✅ {data['with_seo']} con SEO | ❌ {data['without_seo']} sin SEO")
    
    print(f"\n📊 RESUMEN TOTAL:")
    print(f"   Total productos últimos 7 días: {len(products)}")
    print(f"   Con SEO completo: {len(products) - len(products_without_seo)}")
    print(f"   Sin SEO completo: {len(products_without_seo)}")
    
    if products_without_seo:
        print(f"\n❌ PRODUCTOS SIN SEO COMPLETO ({len(products_without_seo)}):")
        for product in products_without_seo[:20]:  # Solo mostrar primeros 20
            empty_summary = f", vacíos: {len(product['empty_fields'])}" if product['empty_fields'] else ""
            missing_summary = f", faltantes: {len(product['missing_fields'])}" if product['missing_fields'] else ""
            print(f"   [{product['date']}] ID {product['id']}: {product['title'][:40]}...{empty_summary}{missing_summary}")
        
        if len(products_without_seo) > 20:
            print(f"   ... y {len(products_without_seo) - 20} más")

if __name__ == "__main__":
    main()