import json
q = json.load(open('pending_products.json', encoding='utf-8'))
print(f'Productos en cola: {len(q)}')
print('\nPrimeros 3:')
for p in q[:3]:
    print(f'  - {p["title"][:50]}')
    print(f'    Vendor: {p.get("vendor", "?")} / {p.get("merchant_name", "?")}')
