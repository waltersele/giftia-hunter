#!/usr/bin/env python3
"""
Verificar estado de la cola de productos pendientes
"""
import json
import os
from datetime import datetime

def main():
    queue_file = 'pending_products.json'
    if not os.path.exists(queue_file):
        print('❌ No hay archivo pending_products.json')
        return
    
    with open(queue_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f'📦 PRODUCTOS EN COLA: {len(products)}')
    
    if len(products) == 0:
        print('✅ La cola está vacía')
        return
    
    print(f'▶️ Último agregado: {products[-1]["title"][:80]}...')
    
    # Contar por categorías
    categories = {}
    for p in products:
        cat = p.get('category', 'Sin categoría')
        categories[cat] = categories.get(cat, 0) + 1
    
    print('\n📊 Por categorías:')
    for cat, count in sorted(categories.items()):
        print(f'  - {cat}: {count}')
    
    print(f'\n🔍 Primeros 3 productos:')
    for i, p in enumerate(products[:3]):
        print(f'  {i+1}. [{p.get("category", "?")}] {p["title"][:60]}...')
    
    if len(products) > 3:
        print(f'  ... y {len(products) - 3} más')

if __name__ == '__main__':
    main()