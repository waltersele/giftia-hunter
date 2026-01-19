#!/usr/bin/env python3
"""Procesar un producto de prueba"""
import json
from process_queue import load_pending_queue, save_pending_queue, classify_batch_with_gemini

queue = load_pending_queue()
if not queue:
    print('Cola vacía')
    exit()

# Tomar solo 1 producto
product = queue[0]
title = product.get('title', '')[:60]
print(f'Procesando: {title}...')

# Clasificar con Gemini
classifications = classify_batch_with_gemini([product])
classification = classifications[0] if classifications else None

if not classification:
    print('❌ Gemini no respondió')
    exit()

print(f'\n✅ Clasificación recibida:')
print(f'   ok: {classification.get("is_good_gift")}')
print(f'   quality: {classification.get("gift_quality")}')
print(f'   category: {classification.get("category")}')

short_desc = classification.get('short_description', '')[:100]
expert_op = classification.get('expert_opinion', '')[:100]
full_desc = classification.get('full_description', '')

print(f'   short_description: {short_desc}...')
print(f'   expert_opinion: {expert_op}...')
print(f'   pros: {len(classification.get("pros", []))} items')
print(f'   cons: {len(classification.get("cons", []))} items')
print(f'   full_description: {len(full_desc)} chars')
print(f'   faqs: {len(classification.get("faqs", []))} items')
print(f'   verdict: {classification.get("verdict", "")[:80]}...')

# Si es bueno, quitar de cola
if classification.get('is_good_gift') and classification.get('gift_quality', 0) >= 5:
    queue.pop(0)
    save_pending_queue(queue)
    print(f'\n✅ Producto quitado de cola. Quedan: {len(queue)}')
else:
    print(f'\n❌ Producto rechazado (quality={classification.get("gift_quality")})')
