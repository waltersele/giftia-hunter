#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIAGNÓSTICO HUNTER - Ver exactamente qué está pasando
"""

import sys
import json

print("=" * 70)
print("DIAGNÓSTICO GIFTIA")
print("=" * 70)
print()

# 1. Verificar que hunter.py existe
import os
if os.path.exists("hunter.py"):
    print("✓ hunter.py encontrado")
else:
    print("✗ hunter.py NO encontrado")
    sys.exit(1)

print()

# 2. Verificar tokens
print("-" * 70)
print("CONFIGURACIÓN")
print("-" * 70)

from hunter import WP_TOKEN, WP_API_URL, AMAZON_TAG
print(f"✓ WP_TOKEN: {WP_TOKEN[:15]}...")
print(f"✓ WP_API_URL: {WP_API_URL}")
print(f"✓ AMAZON_TAG: {AMAZON_TAG}")
print()

# 3. Ver qué búsquedas hace
from hunter import SMART_SEARCHES
print("-" * 70)
print("BÚSQUEDAS CONFIGURADAS")
print("-" * 70)
for vibe, searches in SMART_SEARCHES.items():
    print(f"\n{vibe}: {len(searches)} búsquedas")
    for search in searches[:2]:
        print(f"  - {search}")
    if len(searches) > 2:
        print(f"  ... y {len(searches) - 2} más")

print()

# 4. Ver filtros de calidad
print("-" * 70)
print("FILTROS DE CALIDAD")
print("-" * 70)
from hunter import GIFT_KEYWORDS, BLACKLIST

print(f"\nPrecio aceptado: {BLACKLIST['min_price_eur']}€ - {BLACKLIST['max_price_eur']}€")
print(f"Rango preferido: {BLACKLIST['preferred_price_range'][0]}€ - {BLACKLIST['preferred_price_range'][1]}€")
print(f"\nPalabras prohibidas: {len(BLACKLIST['banned_keywords'])}")
print(f"Ejemplo: {BLACKLIST['banned_keywords'][:3]}")
print(f"\nPalabras sospechosas: {len(BLACKLIST['suspicious_keywords'])}")
print(f"Ejemplo: {BLACKLIST['suspicious_keywords'][:3]}")
print(f"\nPalabras clave positivas: {len(GIFT_KEYWORDS)}")
print("Ejemplos:")
for keyword, points in list(GIFT_KEYWORDS.items())[:5]:
    print(f"  {keyword}: +{points} puntos")

print()

# 5. Test de scoring
print("-" * 70)
print("TEST DE SCORING")
print("-" * 70)

from hunter import calculate_gift_score, is_garbage

test_products = [
    ("Apple AirPods Pro - Auriculares Premium Bluetooth", "229.99", "Auriculares inalámbricos con cancelación de ruido"),
    ("Lámpara LED RGB 3D", "25.50", "Decorativa"),
    ("Pack papel higiénico 24 rollos", "15.00", "Supermercado"),
    ("Drone DJI Mini 3 4K Profesional", "449.99", "Drone con cámara 4K"),
    ("Calcetines deportivos", "12.99", "Para correr"),
]

for title, price, desc in test_products:
    score = calculate_gift_score(title, price, desc)
    garbage = is_garbage(title, price, desc)
    
    status = "❌ RECHAZADO" if garbage else ("✓ ACEPTO" if score >= 45 else "⚠️ BAJO SCORE")
    print(f"\n{status}")
    print(f"  Título: {title[:50]}")
    print(f"  Precio: {price}€")
    print(f"  Score: {score}/100")
    if garbage:
        print(f"  Razón: Es basura")

print()
print("=" * 70)
print("CONCLUSIÓN")
print("=" * 70)
print()
print("Si ves muchos '⚠️ BAJO SCORE', ese es el problema:")
print("Los productos que Hunter encuentra no tienen suficientes palabras clave.")
print()
print("Si ves '❌ RECHAZADO', significa que están en la lista negra.")
print()
print("SIGUIENTE PASO:")
print("Ejecuta: python3 hunter.py")
print("Y mira los logs para ver cuántos productos pasan cada filtro.")
print()
