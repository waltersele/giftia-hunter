"""
Obtiene inventario completo de productos WordPress
Genera JSON con post_id, title, brand, ean, asin, image_url
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

WP_API_URL = "https://giftia.es/wp-json/wp/v2"
WP_TOKEN = os.getenv("WP_API_TOKEN", "nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5")

def fetch_all_products():
    """Obtiene todos los productos publicados desde WordPress REST API"""
    print("📥 Fetching all published products from WordPress...")
    
    all_products = []
    page = 1
    per_page = 100
    
    while True:
        url = f"{WP_API_URL}/gf_gift?per_page={per_page}&page={page}&status=publish"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            products = response.json()
            
            if not products:
                break
            
            print(f"  Page {page}: {len(products)} products")
            
            for product in products:
                post_id = product.get('id')
                title = product.get('title', {}).get('rendered', '')
                
                # Obtener meta fields
                meta = product.get('meta', {})
                
                product_data = {
                    'post_id': post_id,
                    'title': title,
                    'title_raw': product.get('title', {}).get('raw', title),
                    'brand': meta.get('_gf_brand', ''),
                    'ean': meta.get('_gf_ean', ''),
                    'asin': meta.get('_gf_asin', ''),
                    'image_url': meta.get('_gf_image_url', ''),
                    'price': meta.get('_gf_price', ''),
                    'affiliate_url': meta.get('_gf_affiliate_url', ''),
                    'original_title': meta.get('_gf_original_title', ''),  # Si existe
                    'has_ean': bool(meta.get('_gf_ean', '')),
                    'has_asin': bool(meta.get('_gf_asin', ''))
                }
                
                all_products.append(product_data)
            
            page += 1
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                # No more pages
                break
            else:
                print(f"✗ Error fetching page {page}: {e}")
                break
        except Exception as e:
            print(f"✗ Error: {e}")
            break
    
    return all_products


def analyze_inventory(products):
    """Analiza el inventario para ver estado de EANs"""
    total = len(products)
    with_ean = sum(1 for p in products if p['has_ean'])
    with_asin = sum(1 for p in products if p['has_asin'])
    without_ean = total - with_ean
    
    print(f"\n📊 Inventory Analysis:")
    print(f"  Total products: {total}")
    print(f"  With EAN: {with_ean} ({with_ean/total*100:.1f}%)")
    print(f"  Without EAN: {without_ean} ({without_ean/total*100:.1f}%)")
    print(f"  With ASIN: {with_asin} ({with_asin/total*100:.1f}%)")
    
    # Mostrar ejemplos sin EAN
    print(f"\n🔍 Products WITHOUT EAN (first 10):")
    no_ean_products = [p for p in products if not p['has_ean']][:10]
    for p in no_ean_products:
        print(f"  - [{p['post_id']}] {p['title'][:60]}")
        print(f"    Brand: {p['brand'] or 'N/A'} | ASIN: {p['asin'] or 'N/A'}")
    
    return {
        'total': total,
        'with_ean': with_ean,
        'without_ean': without_ean,
        'with_asin': with_asin
    }


def main():
    print("=" * 80)
    print("WORDPRESS INVENTORY FETCHER")
    print("=" * 80)
    
    # Fetch products
    products = fetch_all_products()
    
    if not products:
        print("✗ No products found")
        return
    
    # Analyze
    stats = analyze_inventory(products)
    
    # Save full inventory
    output_file = "wp_inventory.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Full inventory saved to {output_file}")
    
    # Save products without EAN for enrichment
    no_ean_file = "wp_products_no_ean.json"
    no_ean_products = [p for p in products if not p['has_ean']]
    with open(no_ean_file, "w", encoding="utf-8") as f:
        json.dump(no_ean_products, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Products without EAN saved to {no_ean_file}")
    
    # Recommendation
    print("\n💡 NEXT STEPS:")
    if stats['without_ean'] > 0:
        print(f"  1. {stats['without_ean']} products need EAN enrichment")
        print(f"  2. Run Awin importer to download products with EANs")
        print(f"  3. Use fuzzy matching to match Awin EANs with WordPress titles")
        print(f"  4. Update WordPress products with matched EANs")
    else:
        print("  ✓ All products have EAN, ready for multi-vendor matching!")


if __name__ == "__main__":
    main()
