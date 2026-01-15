#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST API GIFTIA - Enviar producto de prueba desde Python
Uso: python3 test_api.py --token=TU_TOKEN --url=https://tu-dominio.com
"""

import requests
import json
import sys
import argparse
from datetime import datetime

class Colors:
    """Colores para terminal"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def log_info(msg):
    """Log info"""
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {msg}")

def log_success(msg):
    """Log success"""
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {msg}")

def log_error(msg):
    """Log error"""
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {msg}")

def log_warning(msg):
    """Log warning"""
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {msg}")

def test_api(url, token):
    """Test API by sending a test product"""
    
    log_info(f"Probando API de Giftia")
    log_info(f"URL: {url}")
    log_info(f"Token: {token[:10]}..." if len(token) > 10 else f"Token: {token}")
    
    # Prepare test product
    product = {
        'title': 'Test Product - Apple AirPods Pro (Python Test)',
        'asin': 'B08HXVQG7K',
        'price': '229.99',
        'image_url': 'https://m.media-amazon.com/images/I/31sKJUAp9PL.jpg',
        'vendor': 'Amazon',
        'affiliate_url': 'https://amazon.es/dp/B08HXVQG7K?tag=GIFTIA-21',
        'description': 'Premium wireless earbuds with active noise cancellation.',
    }
    
    print()
    log_info(f"Producto a enviar:")
    print(json.dumps(product, indent=2, ensure_ascii=False))
    
    print()
    log_info(f"Enviando a: {url}/wp-content/plugins/giftfinder-core/api-ingest.php")
    
    try:
        response = requests.post(
            f"{url}/wp-content/plugins/giftfinder-core/api-ingest.php",
            json=product,
            headers={
                'Content-Type': 'application/json',
                'X-GIFTIA-TOKEN': token,
                'User-Agent': 'GiftiaTestPython/1.0'
            },
            timeout=15,
            verify=False  # Para testing local
        )
        
        print()
        log_info(f"HTTP Status: {response.status_code}")
        
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
            
            if response.status_code == 200:
                log_success("Producto enviado correctamente!")
                if 'post_id' in response_json:
                    log_info(f"Post ID: {response_json['post_id']}")
                    log_info(f"Verifica en: {url}/wp-admin/edit.php?post_type=gf_gift")
                return True
            elif response.status_code == 403:
                log_error("Token incorrecto o no autorizado")
                return False
            elif response.status_code == 400:
                log_error(f"Datos inválidos: {response_json.get('error', 'Unknown')}")
                return False
            elif response.status_code == 500:
                log_error(f"Error del servidor: {response_json.get('error', 'Unknown')}")
                log_warning(f"Revisa: {url}/wp-content/debug.log")
                return False
        except json.JSONDecodeError:
            log_warning("Respuesta no es JSON válido")
            print(response.text[:500])
            return False
            
    except requests.exceptions.ConnectionError as e:
        log_error(f"No se puede conectar a {url}: {e}")
        log_info("Verifica que el URL es correcto y la web está disponible")
        return False
    except requests.exceptions.Timeout:
        log_error("Timeout - la solicitud tardó demasiado")
        return False
    except Exception as e:
        log_error(f"Error inesperado: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Test Giftia API by sending a test product',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_api.py --token=abc123 --url=https://giftia.es
  python3 test_api.py --token=abc123 (usa https://giftia.es por defecto)
        """
    )
    
    parser.add_argument('--token', '-t', required=True, help='API Token (X-GIFTIA-TOKEN)')
    parser.add_argument('--url', '-u', default='https://giftia.es', help='Base URL (default: https://giftia.es)')
    
    args = parser.parse_args()
    
    print()
    print("=" * 60)
    print("GIFTIA API TEST SCRIPT v1.0")
    print("=" * 60)
    print()
    
    success = test_api(args.url.rstrip('/'), args.token)
    
    print()
    print("=" * 60)
    if success:
        log_success("Test completado exitosamente")
        log_info("Próximos pasos:")
        log_info("1. Ve a WordPress Admin → Products → All Gifts")
        log_info("2. Deberías ver 'Test Product - Apple AirPods Pro (Python Test)'")
        log_info("3. Si aparece, ejecuta: python3 hunter.py")
    else:
        log_error("Test falló")
        log_info("Diagnóstico:")
        log_info("1. Abre: " + args.url.rstrip('/') + "/wp-content/plugins/giftfinder-core/verify.php")
        log_info("2. Copia el error exacto")
        log_info("3. Revisa: " + args.url.rstrip('/') + "/wp-content/debug.log")
    print("=" * 60)
    print()

if __name__ == '__main__':
    main()
