#!/usr/bin/env python3
"""
Patch hunter.py to capture delivery_time text
"""

with open('hunter.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar el código actual de envío gratis y reemplazar con versión mejorada
old_code = '''                            try:
                                # Detectar envío gratis
                                delivery_text = ""
                                delivery_els = item.find_elements(By.CSS_SELECTOR, "span[data-component-type='s-shipping-label-block'] span.a-color-base, span.s-align-children-center span.a-text-bold")
                                for el in delivery_els:
                                    delivery_text += el.text.lower() + " "
                                free_shipping = "envío gratis" in delivery_text or "entrega gratis" in delivery_text or is_prime
                            except:
                                pass'''

new_code = '''                            # Detectar tiempo de envío y envío gratis
                            delivery_time = ""
                            try:
                                # Buscar texto de envío en múltiples selectores
                                delivery_selectors = [
                                    "span[data-component-type='s-shipping-label-block']",
                                    "div[data-cy='delivery-recipe']",
                                    "span.a-text-bold[aria-label*='Entrega']",
                                    "span.a-color-base.a-text-bold",
                                    "div.s-align-children-center span"
                                ]
                                for selector in delivery_selectors:
                                    try:
                                        els = item.find_elements(By.CSS_SELECTOR, selector)
                                        for el in els:
                                            text = el.text.strip()
                                            # Buscar patrones de entrega
                                            if any(kw in text.lower() for kw in ['entrega', 'envío', 'llega', 'recíbelo', 'mañana', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo', 'días']):
                                                if len(text) > len(delivery_time):
                                                    delivery_time = text
                                    except:
                                        continue
                            except:
                                pass
                            
                            # Determinar si es envío gratis basado en texto o Prime
                            delivery_lower = delivery_time.lower()
                            free_shipping = is_prime or "gratis" in delivery_lower or "envío gratis" in delivery_lower'''

if old_code in content:
    content = content.replace(old_code, new_code)
    print("✅ Código de envío actualizado")
else:
    print("⚠️ No encontré el código exacto, buscando alternativa...")
    # Buscar patrón más flexible
    import re
    pattern = r'try:\s+# Detectar envío gratis.*?free_shipping = .*?is_prime\s+except:\s+pass'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_code.strip(), content, flags=re.DOTALL)
        print("✅ Código de envío actualizado (regex)")
    else:
        print("❌ No se pudo encontrar el código a reemplazar")
        exit(1)

# Ahora añadir delivery_time al payload
old_payload = '"free_shipping": free_shipping'
new_payload = '"free_shipping": free_shipping,\n                                    "delivery_time": delivery_time'

if old_payload in content and "delivery_time" not in content.split(old_payload)[1][:50]:
    content = content.replace(old_payload, new_payload)
    print("✅ Campo delivery_time añadido al payload")
else:
    print("⚠️ delivery_time ya estaba en el payload o no se encontró")

with open('hunter.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Patch aplicado correctamente")
