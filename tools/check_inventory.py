#!/usr/bin/env python3
"""Ver inventario publicado."""

import json

def main():
    with open('published_inventory.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    
    print(f"Categorías en inventario: {list(d.keys())}")
    print()
    
    # Ver productos Gourmet (termómetros deberían estar aquí)
    gourmet = d.get('Gourmet', [])
    print(f"=== GOURMET ({len(gourmet)} productos) ===")
    for p in gourmet[-5:]:
        print(f"  - {p.get('title', '?')[:50]} ({p.get('added_at', '?')[:16]})")
    
    print()
    
    # Ver todas las categorías con sus conteos
    for cat, products in d.items():
        print(f"  {cat}: {len(products)} productos")

if __name__ == "__main__":
    main()
