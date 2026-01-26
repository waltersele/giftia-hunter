import requests

# Verificar producto debug más reciente
url = 'https://giftia.es/wp-json/wp/v2/gf_gift/2947'
r = requests.get(url)
if r.status_code == 200:
    product = r.json()
    title = product.get('title', {}).get('rendered', 'N/A')
    meta = product.get('meta', {})
    
    print(f'Producto: {title}')
    print(f'Total meta fields: {len(meta)}')
    
    # Verificar campos SEO con prefijo _gf_
    gf_seo_fields = ['_gf_seo_title', '_gf_meta_description', '_gf_h1_title', 
                     '_gf_short_description', '_gf_expert_opinion']
    
    print('\n📋 Campos SEO con prefijo _gf_:')
    for field in gf_seo_fields:
        value = meta.get(field, '')
        status = 'SI' if value else 'NO'
        print(f'  {field}: {status}')
        
        if value and len(str(value)) > 20:
            print(f'    Contenido: {str(value)[:80]}...')
    
    print('\n🔍 Todos los _gf_ fields:')
    gf_fields = {k: v for k, v in meta.items() if k.startswith('_gf_')}
    for k, v in gf_fields.items():
        print(f'  {k}: {v}')
        
else:
    print(f'Error: {r.status_code}')