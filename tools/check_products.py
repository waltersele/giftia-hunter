#!/usr/bin/env python3
"""Verificar productos recientes en WordPress."""

import requests

def main():
    r = requests.get('https://giftia.es/wp-json/wp/v2/gf_gift', params={'per_page': 100})
    products = r.json()
    
    print(f"Total productos: {len(products)}")
    print()
    print("=== ÚLTIMOS 10 POR FECHA DE MODIFICACIÓN ===")
    
    for p in sorted(products, key=lambda x: x.get('modified', ''), reverse=True)[:10]:
        mod_date = p.get('modified', '')[:16]
        post_id = p.get('id')
        title = p.get('title', {}).get('rendered', '')[:50]
        slug = p.get('slug', '')[:40]
        gf_category = p.get('gf_category', [])
        gf_recipient = p.get('gf_recipient', [])
        gf_age = p.get('gf_age', [])
        gf_occasion = p.get('gf_occasion', [])
        
        print(f"{mod_date} | ID:{post_id}")
        print(f"  Title: {title}")
        print(f"  Slug: {slug}")
        print(f"  Taxonomías: cat={gf_category} recip={gf_recipient} age={gf_age} occ={gf_occasion}")
        print()

if __name__ == "__main__":
    main()
