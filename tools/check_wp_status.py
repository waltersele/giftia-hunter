#!/usr/bin/env python3
"""
Verificar productos en WordPress y el rate limit
"""
import requests
import json
from datetime import datetime

def check_wordpress_products():
    """Verificar productos en WordPress de hoy"""
    url = 'https://giftia.es/wp-json/wp/v2/gf_gift'
    params = {
        'per_page': 100,
        'order': 'desc',
        'orderby': 'date'
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        print(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            products = response.json()
            today_count = 0
            today = datetime.now().strftime('%Y-%m-%d')
            
            for product in products:
                product_date = product['date'][:10]  # 2025-01-19T...
                if product_date == today:
                    today_count += 1
            
            print(f'📊 Productos de hoy ({today}): {today_count}')
            print(f'📦 Total productos: {len(products)}')
            
            if today_count > 0:
                print(f'✅ Últimos 3 productos de hoy:')
                today_products = [p for p in products if p['date'][:10] == today][:3]
                for i, p in enumerate(today_products):
                    title = p['title']['rendered'][:60]
                    print(f'  {i+1}. ID {p["id"]}: {title}...')
                return True
            else:
                print('❌ NO hay productos de hoy')
                return False
        else:
            print(f'❌ Error: {response.status_code}')
            print(response.text[:200])
            return False
            
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

def reset_rate_limit():
    """Resetear el rate limit para permitir procesamiento"""
    # Usar el endpoint normal (no emergency)
    url = 'https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php?action=reset_rate_limit'
    headers = {'X-GIFTIA-TOKEN': 'nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5'}

    print('\n🔄 Reseteando rate limit...')
    try:
        response = requests.post(url, headers=headers, timeout=30)
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
        
        if response.status_code == 200:
            print('✅ Rate limit reseteado exitosamente')
            return True
        else:
            print(f'❌ Error reseteando: {response.status_code}')
            return False
            
    except Exception as e:
        print(f'❌ Error de conexión: {e}')
        return False

def main():
    print('=== DIAGNÓSTICO WORDPRESS ===')
    has_products = check_wordpress_products()
    
    print('\n=== RESET RATE LIMIT ===')
    reset_success = reset_rate_limit()
    
    if not has_products:
        print('\n🚨 PROBLEMA CONFIRMADO: Hunter corrió 6 horas pero NO hay productos de hoy')
        print('💡 CAUSA: Rate limit 429 bloqueó TODAS las inserciones')
        if reset_success:
            print('✅ Rate limit reseteado - Ejecutar process_queue.py ahora')
        else:
            print('❌ Falló el reset - Revisar endpoint')
    else:
        print('\n✅ Hay productos, pero pueden faltar datos SEO')

if __name__ == '__main__':
    main()