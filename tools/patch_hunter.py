#!/usr/bin/env python3
"""
Patch hunter.py to add Prime/shipping capture
"""
import re

# Leer archivo
with open('hunter.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar línea con "# Construir payload"
insert_idx = None
for i, line in enumerate(lines):
    if '# Construir payload' in line and 'description' in lines[i-2]:
        insert_idx = i
        break

if insert_idx is None:
    print("ERROR: No encontré la línea '# Construir payload'")
    exit(1)

print(f"Encontrado '# Construir payload' en línea {insert_idx + 1}")

# Verificar si ya está el código
if any('is_prime' in line for line in lines[insert_idx-15:insert_idx]):
    print("Ya está añadido el código de Prime. Saliendo.")
    exit(0)

# Código a insertar (con la indentación correcta)
prime_code = '''
                            # Prime y envío gratis
                            is_prime = False
                            free_shipping = False
                            try:
                                # Detectar Prime badge
                                prime_elements = item.find_elements(By.CSS_SELECTOR, "i.a-icon-prime, .a-icon-prime, span[aria-label*='Prime']")
                                is_prime = len(prime_elements) > 0
                            except:
                                pass
                            
                            try:
                                # Detectar envío gratis
                                delivery_text = ""
                                delivery_els = item.find_elements(By.CSS_SELECTOR, "span[data-component-type='s-shipping-label-block'] span.a-color-base, span.s-align-children-center span.a-text-bold")
                                for el in delivery_els:
                                    delivery_text += el.text.lower() + " "
                                free_shipping = "envío gratis" in delivery_text or "entrega gratis" in delivery_text or is_prime
                            except:
                                pass

'''

# Insertar antes del "# Construir payload"
lines.insert(insert_idx, prime_code)

# Ahora buscar el payload dict para añadir los campos
# Buscar "source_vibe": vibe
payload_idx = None
for i, line in enumerate(lines):
    if '"source_vibe": vibe' in line or "'source_vibe': vibe" in line:
        payload_idx = i
        break

if payload_idx:
    print(f"Encontrado 'source_vibe' en línea {payload_idx + 1}")
    # Añadir los campos después de source_vibe
    current_line = lines[payload_idx]
    if current_line.strip().endswith('}'):
        # Es la última línea del dict, añadir antes del }
        new_line = current_line.replace(
            '"source_vibe": vibe',
            '"source_vibe": vibe,\n                                    "is_prime": is_prime,\n                                    "free_shipping": free_shipping'
        )
    else:
        # No es la última, solo añadir coma y los campos
        new_line = current_line.rstrip('\n').rstrip() 
        if not new_line.endswith(','):
            new_line += ','
        new_line += '\n                                    "is_prime": is_prime,\n                                    "free_shipping": free_shipping\n'
    lines[payload_idx] = new_line
    print("Añadidos campos is_prime y free_shipping al payload")

# Guardar
with open('hunter.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("OK - Patch aplicado correctamente")
