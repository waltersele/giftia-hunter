#!/usr/bin/env python3
"""
Fix: Mover inicialización de Chrome driver dentro del bloque main
"""

with open("hunter.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Encontrar y comentar la sección de driver setup (líneas ~1660-1687)
new_lines = []
in_driver_section = False
skip_until_function = False

for i, line in enumerate(lines):
    # Detectar inicio de la sección SELENIUM DRIVER SETUP
    if "# SELENIUM DRIVER SETUP" in line and not in_driver_section:
        in_driver_section = True
        new_lines.append("# ============================================================================\n")
        new_lines.append("# SELENIUM DRIVER SETUP - initialized in main()\n")
        new_lines.append("# ============================================================================\n")
        new_lines.append("driver = None  # Global driver variable\n")
        new_lines.append("\n")
        skip_until_function = True
        continue
    
    # Saltar todo hasta la siguiente función
    if skip_until_function:
        if line.startswith("def ") or "# FUNCION DE ENVIO" in line or "# FUNCIÓN DE ENVÍO" in line:
            skip_until_function = False
            new_lines.append(line)
        continue
    
    new_lines.append(line)

# Escribir archivo modificado
with open("hunter.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("OK: Driver setup comentado")
print(f"Total líneas: {len(new_lines)}")
