#!/usr/bin/env python3
"""Verificar taxonomías registradas en WordPress."""

import requests

def main():
    taxonomies = ['gf_category', 'gf_age', 'gf_gender', 'gf_recipient', 'gf_occasion', 'gf_budget']
    
    print("="*60)
    print("📊 ESTADO DE TAXONOMÍAS EN WORDPRESS")
    print("="*60)
    print()
    
    for tax in taxonomies:
        try:
            r = requests.get(f'https://giftia.es/wp-json/wp/v2/{tax}', timeout=10)
            if r.status_code == 200:
                terms = r.json()
                print(f"✅ {tax}: {len(terms)} términos")
                for t in terms[:5]:
                    slug = t.get('slug', '?')
                    name = t.get('name', '?')
                    count = t.get('count', 0)
                    print(f"   - {slug}: {name} ({count} productos)")
            else:
                print(f"❌ {tax}: HTTP {r.status_code} (NO registrada en REST API)")
                print(f"   → Necesita flush de permalinks en WordPress Admin")
        except Exception as e:
            print(f"⚠️ {tax}: Error - {e}")
        print()

if __name__ == "__main__":
    main()
