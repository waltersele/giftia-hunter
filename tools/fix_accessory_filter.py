#!/usr/bin/env python3
"""Script para añadir filtro de accesorios/consumibles al hunter"""

with open('hunter.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar la línea de validación de precio y añadir código antes
target = '    # Validación de precio'

if target in content:
    accessory_code = '''    # =========================================================================
    # DETECCIÓN DE ACCESORIOS/CONSUMIBLES (no son regalos)
    # =========================================================================
    accessory_patterns = [
        r'\\d+\\s*(piezas|unidades|pcs|pack|ud|uds)',  # "200 piezas", "50 unidades"
        r'(filtros?|recambios?|repuestos?)\\s+(para|de|compatible)',  # "filtros para cafetera"
        r'(compatible con|compatible para)',  # accesorios genéricos
        r'(pack|set|kit)\\s+de\\s+\\d+',  # "pack de 100"
    ]
    
    for pattern in accessory_patterns:
        if re.search(pattern, title_lower):
            gift_exceptions = ["set de regalo", "kit de regalo", "set premium", "kit premium", 
                              "set completo", "kit completo", "kit de café", "set de café"]
            if not any(exc in title_lower for exc in gift_exceptions):
                logger.info(f"🔧 ACCESORIO/CONSUMIBLE: {title[:50]}...")
                return True

'''
    content = content.replace(target, accessory_code + target)
    with open('hunter.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Filtro de accesorios añadido")
else:
    print("❌ No se encontró '# Validación de precio'")
    # Debug
    if 'precio' in content.lower():
        print("'precio' está en el archivo")
    if 'is_garbage' in content:
        print("'is_garbage' está en el archivo")
