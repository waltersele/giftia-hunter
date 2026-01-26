#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GIFTIA INVENTORY SYNC (SELF-HEALING)
------------------------------------
Sistema diario de mantenimiento de inventario que:
1. Obtiene snapshot del inventario en Wordpress (IDs, EANs, Precios).
2. Carga el Feed maestro del día (Awin/Amazon).
3. Detecta cambios:
   - Precio modificado -> Update WP
   - Producto exhausto -> Soft 404 (Zombie Mode)
   - Link roto -> Resurrección por EAN matching
   
Uso: python inventory_sync.py
"""

import os
import json
import csv
import sys
import requests
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
WP_API_BASE = "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php"
WP_TOKEN = os.getenv("WP_API_TOKEN", "nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5")

# Archivos de Feeds (asumimos que download_awin.py ya corrió)
FEED_AWIN = "feed_eci.csv" 
LOG_FILE = "inventory_sync_log.json"

def get_wp_snapshot():
    """Obtiene el estado actual del inventario desde WP."""
    print("📡 Obteniendo snapshot de inventario WP...")
    try:
        url = f"{WP_API_BASE}?action=inventory_snapshot&token={WP_TOKEN}"
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get('success'):
            print(f"✅ Snapshot recibido: {data['count']} productos activos.")
            return data['inventory'] # Dict key=vendor_id
        else:
            print(f"❌ Error API: {data.get('message')}")
            return {}
    except Exception as e:
        print(f"❌ Error conexión WP: {e}")
        return {}

def load_master_feed():
    """Carga el feed CSV en memoria indexado por ID y por EAN."""
    print(f"📂 Cargando feed maestro: {FEED_AWIN} ...")
    
    if not os.path.exists(FEED_AWIN):
        print(f"❌ No se encuentra el archivo {FEED_AWIN}. Ejecuta download_awin.py primero.")
        return None, None

    feed_by_id = {}
    feed_by_ean = {}
    
    try:
        # Detectar delimitador
        with open(FEED_AWIN, 'r', encoding='utf-8', errors='ignore') as f:
            sample = f.read(2048)
            sniffer = csv.Sniffer()
            try:
                dialect = sniffer.sniff(sample)
                delimiter = dialect.delimiter
            except:
                delimiter = ',' # Default fallback
                
        with open(FEED_AWIN, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            
            # Mapeo de columnas
            cols = reader.fieldnames
            col_id = next((c for c in cols if 'aw_product_id' in c or 'merchant_product_id' in c), 'aw_product_id')
            col_ean = next((c for c in cols if 'ean' in c or 'isbn' in c or 'gtin' in c), 'ean')
            col_price = next((c for c in cols if 'search_price' in c or 'store_price' in c), 'search_price')
            col_url = next((c for c in cols if 'merchant_deep_link' in c or 'aw_deep_link' in c), 'aw_deep_link')
            col_stock = next((c for c in cols if 'stock_status' in c or 'in_stock' in c), 'stock_status')
            
            count = 0
            for row in reader:
                pid = row.get(col_id, '').strip()
                ean = row.get(col_ean, '').strip()
                
                # Normalizar datos
                item_data = {
                    'price': row.get(col_price, '0').replace(',', '.'),
                    'url': row.get(col_url, ''),
                    'stock': row.get(col_stock, 'in stock'),
                    'vendor_id': pid,
                    'vendor_name': row.get('merchant_name', 'Vendor')
                }
                
                if pid:
                    feed_by_id[pid] = item_data
                
                # Indexar por EAN (si es válido)
                if ean and len(ean) > 5 and ean != '0':
                    if ean not in feed_by_ean:
                        feed_by_ean[ean] = []
                    feed_by_ean[ean].append(item_data)
                    
                count += 1
                if count % 50000 == 0:
                    print(f"   ⏳ Procesados {count} items...")
                    
        print(f"✅ Feed cargado: {len(feed_by_id)} items únicos. indexados por EAN: {len(feed_by_ean)}")
        return feed_by_id, feed_by_ean
        
    except Exception as e:
        print(f"❌ Error leyendo CSV: {e}")
        return None, None

def update_product_batch(updates):
    """Envía actualizaciones a WP una por una (por seguridad)."""
    # En el futuro se podría hacer batch endpoint
    print(f"🚀 Iniciando actualización de {len(updates)} productos...")
    
    success_count = 0
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {WP_TOKEN}'}
    
    for up in updates:
        try:
            url = f"{WP_API_BASE}?action=update_stock&token={WP_TOKEN}"
            resp = requests.post(url, json=up, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                print(f"   ✅ OK ID {up['post_id']}: {up['reason']}")
                success_count += 1
            else:
                print(f"   ⚠️ Falló ID {up['post_id']}: {resp.text}")
                
            time.sleep(0.1) # Rate limit suave
            
        except Exception as e:
            print(f"   ❌ Error req ID {up['post_id']}: {e}")
            
    print(f"🏁 Finalizado. Éxito: {success_count}/{len(updates)}")

def main():
    print("=== GIFTIA INVENTORY SELF-HEALING ===")
    
    # 1. Obtener snapshot
    inventory = get_wp_snapshot()
    if not inventory:
        return
        
    # 2. Cargar Feed
    feed_id, feed_ean = load_master_feed()
    if not feed_id:
        return
        
    updates_to_send = []
    stats = {'zombies': 0, 'price_updates': 0, 'resurrections': 0, 'ok': 0}
    
    # 3. Comparar
    print("🔍 Analizando inventario...")
    
    for vendor_id, wp_item in inventory.items():
        post_id = wp_item['wp_id']
        wp_ean = wp_item['ean']
        
        # Caso A: El producto existe en el feed
        if vendor_id in feed_id:
            feed_item = feed_id[vendor_id]
            
            # Chequear precio (margen diferencia 1€)
            try:
                # ToDo: Comparar precio si lo tuviéramos en el snapshot. 
                # Por ahora solo actualizamos si tenemos el dato localmente en un futuro.
                # (El snapshot actual solo trae IDs)
                pass 
            except:
                pass
                
            # Si stock status es explícitamente "out of stock"
            stk = str(feed_item['stock']).lower()
            if 'out' in stk or 'agotado' in stk or stk == '0':
                 # Confirmar zombi
                 updates_to_send.append({
                    'post_id': post_id,
                    'stock_status': 'outdated',
                    'reason': 'Stock agotado en feed'
                })
                 stats['zombies'] += 1
            else:
                stats['ok'] += 1
                
        # Caso B: El producto NO existe en el feed (Posible 404/Descatalogado)
        else:
            # Intentar resurrección por EAN
            found_match = None
            if wp_ean and wp_ean in feed_ean:
                candidates = feed_ean[wp_ean]
                # Tomar el primero disponible
                if candidates:
                    found_match = candidates[0]
            
            if found_match:
                # RESURRECCIÓN EXITOSA
                updates_to_send.append({
                    'post_id': post_id,
                    'stock_status': 'in_stock',
                    'vendor_id': found_match['vendor_id'],
                    'vendor': found_match['vendor_name'],
                    'affiliate_url': found_match['url'],
                    'price': found_match['price'],
                    'reason': f"Resurrected via EAN {wp_ean}"
                })
                stats['resurrections'] += 1
            else:
                # ZOMBIE MODE (No hay match, producto muerto)
                updates_to_send.append({
                    'post_id': post_id,
                    'stock_status': 'outdated',
                    'reason': 'Missing in feed & No EAN match'
                })
                stats['zombies'] += 1

    print(f"\n📊 Resultados Análisis:")
    print(f"   Zombies (Outdated): {stats['zombies']}")
    print(f"   Resurrecciones: {stats['resurrections']}")
    print(f"   Healthy: {stats['ok']}")
    print(f"   Total Updates: {len(updates_to_send)}")
    
    if updates_to_send:
        update_product_batch(updates_to_send)
    else:
        print("✨ Inventario sincronizado. Sin cambios.")

if __name__ == "__main__":
    main()
