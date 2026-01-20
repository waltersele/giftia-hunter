#!/usr/bin/env python3
"""
GIFTIA - Actualizador de información de envío
=============================================
Detecta productos sin información de Prime/envío y los actualiza desde Amazon.

Uso:
    python update_shipping_info.py [--limit N] [--dry-run]
"""

import os
import sys
import json
import time
import random
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv

# Cargar configuración
load_dotenv()

# Configuración
WORDPRESS_API = os.getenv('WORDPRESS_API_URL', 'https://giftia.es/wp-json/giftia/v1')
GIFTIA_TOKEN = os.getenv('GIFTIA_TOKEN', '') or os.getenv('WP_API_TOKEN', '')
INGEST_URL = os.getenv('INGEST_URL', 'https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php')

# Headers para requests a Amazon
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

def log(msg, level="INFO"):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

def get_products_without_shipping_info():
    """Obtiene productos que no tienen información de envío"""
    log("Consultando WordPress para productos sin info de envío...")
    
    try:
        response = requests.get(
            f"{INGEST_URL}?action=products_without_shipping&limit=200",
            headers={'X-GIFTIA-TOKEN': GIFTIA_TOKEN},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                log(f"Encontrados {data.get('count', 0)} productos sin info de envío")
                return data.get('products', [])
            else:
                log(f"Error: {data.get('error', 'Unknown')}", "ERROR")
                return []
        else:
            log(f"Error API: {response.status_code} - {response.text[:200]}", "ERROR")
            return []
    except Exception as e:
        log(f"Error conectando a WordPress: {e}", "ERROR")
        return []

def get_all_products_with_asin():
    """Obtiene todos los productos con ASIN para verificar manualmente"""
    log("Obteniendo lista de productos con ASIN...")
    
    try:
        # Usar endpoint estándar de WordPress
        products = []
        page = 1
        per_page = 100
        
        while True:
            response = requests.get(
                f"https://giftia.es/wp-json/wp/v2/gf_gift",
                params={
                    'page': page,
                    'per_page': per_page,
                    '_fields': 'id,title,meta'
                },
                headers={'X-GIFTIA-TOKEN': GIFTIA_TOKEN},
                timeout=30
            )
            
            if response.status_code != 200:
                break
                
            data = response.json()
            if not data:
                break
                
            products.extend(data)
            
            # Verificar si hay más páginas
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))
            if page >= total_pages:
                break
            page += 1
            
        log(f"Encontrados {len(products)} productos totales")
        return products
        
    except Exception as e:
        log(f"Error: {e}", "ERROR")
        return []

def extract_shipping_from_amazon(asin):
    """Extrae información de envío desde Amazon"""
    url = f"https://www.amazon.es/dp/{asin}"
    
    try:
        time.sleep(random.uniform(2, 4))  # Rate limiting
        
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            log(f"  Amazon devolvió {response.status_code} para {asin}", "WARN")
            return None
            
        html = response.text.lower()
        
        # Detectar Prime
        is_prime = False
        prime_indicators = [
            'id="prime-badge"',
            'class="prime-badge"',
            'prime-logo',
            'amazon prime',
            'id="fast-track-message"',
            'data-feature-name="primedelivery"',
            '/gp/prime',
        ]
        for indicator in prime_indicators:
            if indicator in html:
                is_prime = True
                break
        
        # Detectar envío gratis
        free_shipping = is_prime  # Si es Prime, envío gratis
        shipping_indicators = [
            'envío gratis',
            'entrega gratis',
            'free delivery',
            'envío gratuito',
        ]
        for indicator in shipping_indicators:
            if indicator in html:
                free_shipping = True
                break
        
        # Extraer tiempo de entrega
        delivery_time = ''
        import re
        
        # Buscar patrones de fecha de entrega
        delivery_patterns = [
            r'entrega[^\d]*(\d{1,2})[^\d]*-[^\d]*(\d{1,2})[^\d]*(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)',
            r'llega[^\d]*(\d{1,2})[^\d]*(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)',
            r'recíbelo[^\d]*(mañana|hoy|lunes|martes|miércoles|jueves|viernes|sábado|domingo)',
        ]
        
        for pattern in delivery_patterns:
            match = re.search(pattern, html)
            if match:
                delivery_time = match.group(0)[:50]  # Limitar longitud
                break
        
        return {
            'is_prime': is_prime,
            'free_shipping': free_shipping,
            'delivery_time': delivery_time
        }
        
    except Exception as e:
        log(f"  Error scrapeando {asin}: {e}", "ERROR")
        return None

def update_product_shipping(post_id, asin, shipping_info, dry_run=False):
    """Actualiza la información de envío de un producto"""
    
    if dry_run:
        log(f"  [DRY-RUN] Actualizaría post {post_id} ({asin}): Prime={shipping_info['is_prime']}, Free={shipping_info['free_shipping']}")
        return True
    
    try:
        payload = {
            'post_id': post_id,
            'is_prime': shipping_info['is_prime'],
            'free_shipping': shipping_info['free_shipping'],
            'delivery_time': shipping_info['delivery_time']
        }
        
        response = requests.post(
            f"{INGEST_URL}?action=update_shipping",
            json=payload,
            headers={
                'X-GIFTIA-TOKEN': GIFTIA_TOKEN,
                'Content-Type': 'application/json'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                log(f"  ✓ Actualizado post {post_id}: Prime={shipping_info['is_prime']}")
                return True
            else:
                log(f"  ✗ Error: {result.get('error', 'Unknown')}", "ERROR")
                return False
        else:
            log(f"  ✗ HTTP {response.status_code}: {response.text[:100]}", "ERROR")
            return False
            
    except Exception as e:
        log(f"  ✗ Error actualizando: {e}", "ERROR")
        return False

def scan_local_database():
    """
    Alternativa: escanear directamente la base de datos local de productos
    pendientes para detectar los que necesitan actualización de envío
    """
    pending_file = 'pending_products.json'
    if not os.path.exists(pending_file):
        return []
    
    with open(pending_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    # Filtrar los que no tienen info de envío
    needs_update = []
    for p in products:
        if 'is_prime' not in p or p.get('is_prime') is None:
            needs_update.append(p)
    
    return needs_update

def main():
    parser = argparse.ArgumentParser(description='Actualizar información de envío de productos')
    parser.add_argument('--limit', type=int, default=50, help='Límite de productos a procesar')
    parser.add_argument('--dry-run', action='store_true', help='Simular sin hacer cambios')
    parser.add_argument('--from-file', type=str, help='Procesar ASINs desde archivo (uno por línea)')
    parser.add_argument('--asin', type=str, help='Procesar un ASIN específico')
    args = parser.parse_args()
    
    log("=" * 60)
    log("GIFTIA - Actualizador de Información de Envío")
    log("=" * 60)
    
    if args.dry_run:
        log("MODO DRY-RUN - No se harán cambios reales", "WARN")
    
    # Verificar token
    if not GIFTIA_TOKEN:
        log("ERROR: GIFTIA_TOKEN no configurado en .env", "ERROR")
        sys.exit(1)
    
    products_to_process = []
    
    # Opción 1: ASIN específico
    if args.asin:
        log(f"Procesando ASIN específico: {args.asin}")
        products_to_process = [{'asin': args.asin, 'post_id': None}]
    
    # Opción 2: Desde archivo
    elif args.from_file:
        if os.path.exists(args.from_file):
            with open(args.from_file, 'r') as f:
                asins = [line.strip() for line in f if line.strip()]
            products_to_process = [{'asin': a, 'post_id': None} for a in asins]
            log(f"Cargados {len(products_to_process)} ASINs desde {args.from_file}")
        else:
            log(f"Archivo no encontrado: {args.from_file}", "ERROR")
            sys.exit(1)
    
    # Opción 3: Consultar WordPress
    else:
        products_to_process = get_products_without_shipping_info()
        
        if not products_to_process:
            log("No se encontraron productos sin información de envío")
            log("Intentando escanear productos locales...")
            products_to_process = scan_local_database()
    
    if not products_to_process:
        log("No hay productos para procesar")
        return
    
    # Aplicar límite
    products_to_process = products_to_process[:args.limit]
    log(f"Procesando {len(products_to_process)} productos...")
    
    stats = {'updated': 0, 'failed': 0, 'skipped': 0, 'prime': 0, 'free': 0}
    
    for i, product in enumerate(products_to_process, 1):
        asin = product.get('asin', '')
        post_id = product.get('post_id') or product.get('id')
        title = product.get('title', {})
        if isinstance(title, dict):
            title = title.get('rendered', '')[:40]
        
        if not asin:
            log(f"[{i}/{len(products_to_process)}] Sin ASIN, saltando")
            stats['skipped'] += 1
            continue
        
        log(f"[{i}/{len(products_to_process)}] {asin} - {title}")
        
        # Extraer info de Amazon
        shipping_info = extract_shipping_from_amazon(asin)
        
        if shipping_info is None:
            stats['failed'] += 1
            continue
        
        # Estadísticas
        if shipping_info['is_prime']:
            stats['prime'] += 1
        if shipping_info['free_shipping']:
            stats['free'] += 1
        
        # Actualizar producto
        if post_id:
            success = update_product_shipping(post_id, asin, shipping_info, args.dry_run)
            if success:
                stats['updated'] += 1
            else:
                stats['failed'] += 1
        else:
            # Sin post_id, solo mostramos la info
            log(f"  → Prime: {shipping_info['is_prime']}, Free: {shipping_info['free_shipping']}, Delivery: {shipping_info['delivery_time']}")
            stats['updated'] += 1
    
    # Resumen
    log("")
    log("=" * 60)
    log("RESUMEN")
    log("=" * 60)
    log(f"  Procesados: {len(products_to_process)}")
    log(f"  Actualizados: {stats['updated']}")
    log(f"  Fallidos: {stats['failed']}")
    log(f"  Saltados: {stats['skipped']}")
    log(f"  Con Prime: {stats['prime']}")
    log(f"  Con envío gratis: {stats['free']}")

if __name__ == '__main__':
    main()
