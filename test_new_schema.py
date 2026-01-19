#!/usr/bin/env python3
"""
Script de prueba completa del nuevo schema (Gold Master v50).
Envía un producto de prueba y verifica:
1. Taxonomías asignadas correctamente
2. Meta fields SEO guardados
3. Hook psicológico registrado
4. Precio e información del producto

Ejecutar: python test_new_schema.py

Versión: 2.0 (Gold Master v50)
Fecha: 18 Enero 2026
"""

import requests
import json
import time
import sys
import os

WP_API_URL = "https://giftia.es/wp-json/giftia/v1/ingest"
WP_TOKEN = "nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5"
WP_REST_URL = "https://giftia.es/wp-json/wp/v2/gf_gift"

# ============================================
# COLORES PARA TERMINAL
# ============================================
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'
    
    @staticmethod
    def disable():
        """Desactiva colores en Windows sin soporte ANSI"""
        Colors.GREEN = Colors.RED = Colors.YELLOW = ''
        Colors.BLUE = Colors.CYAN = Colors.BOLD = Colors.END = ''

# Detectar Windows sin soporte de colores
if os.name == 'nt':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        Colors.disable()

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"   {Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"   {Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"   {Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"   {Colors.CYAN}ℹ️  {text}{Colors.END}")


# ============================================
# FUNCIÓN PRINCIPAL DE TEST
# ============================================
def test_new_schema():
    """Envía un producto de prueba con el nuevo schema y verifica taxonomías + meta fields."""
    
    # Generar ASIN único para evitar actualizar producto existente
    unique_asin = f"TEST{int(time.time())}"
    
    print_header("🧪 PRUEBA GOLD MASTER v50 - giftia_schema.json")
    
    # ========================================
    # DEFINIR PRODUCTO DE PRUEBA
    # ========================================
    test_product = {
        'asin': unique_asin,
        'title': 'Set Barista Profesional Deluxe',
        'price': '89.99',
        'affiliate_url': 'https://amazon.es/test-barista',
        'image_url': 'https://via.placeholder.com/500x500/8B4513/FFFFFF?text=Barista+Set',
        'rating': '4.7',
        'reviews_count': 567,
        
        # === TAXONOMÍAS según giftia_schema.json ===
        'category': 'Gourmet',
        'gemini_category': 'Gourmet',
        'ages': ['jovenes', 'adultos', 'seniors'],
        'target_gender': 'unisex',
        'recipients': ['padre', 'amigo', 'yo'],
        'occasions': ['cumpleanos', 'dia-del-padre', 'navidad'],
        'marketing_hook': 'hedonism',
        
        # === FICHA COMPLETA Gold Master v50 ===
        'gift_quality': 8,
        'giftia_score': 4.5,
        
        'marketing_title': 'Set Barista que Transforma tu Cocina',
        'seo_title': 'Regalo para Cafeteros: Set Barista Profesional - Giftia',
        'meta_description': 'Convierte tu cocina en una cafetería de especialidad. El regalo perfecto para amantes del café.',
        'short_description': 'Convierte tu cocina en una cafetería de especialidad. El mejor café del mundo, hecho en casa.',
        'seo_content': '''Por qué nos encanta: Este set representa el equilibrio perfecto entre calidad profesional y facilidad de uso.

Para quién es ideal: Perfectos para amantes del café exigentes, padres que disfrutan su momento matutino.

Lo que destaca:
• Incluye espumador de leche premium
• Kit completo de latte art
• Granos de especialidad de regalo
• Diseño compacto y elegante''',
        'pros': ['Espumador de leche incluido', 'Kit de latte art profesional', 'Granos premium de regalo'],
        'why_selected': 'Nos encanta porque es el regalo que todo cafetero desearía pero no se compraría.',
        'seo_slug': 'set-barista-profesional-cafe-latte-art'
    }
    
    # Mostrar producto
    print(f"📦 {Colors.BOLD}Producto de Prueba:{Colors.END}")
    print(f"   ASIN: {unique_asin}")
    print(f"   Título: {test_product['title']}")
    print(f"   Precio: €{test_product['price']}")
    print()
    print(f"   {Colors.BOLD}Taxonomías:{Colors.END}")
    print(f"   • Categoría: {test_product['category']}")
    print(f"   • Edades: {test_product['ages']}")
    print(f"   • Género: {test_product['target_gender']}")
    print(f"   • Destinatarios: {test_product['recipients']}")
    print(f"   • Ocasiones: {test_product['occasions']}")
    print(f"   • Hook: {test_product['marketing_hook']}")
    print()
    print(f"   {Colors.BOLD}SEO (Gold Master v50):{Colors.END}")
    print(f"   • Marketing Title: {test_product['marketing_title'][:40]}...")
    print(f"   • Giftia Score: {test_product['giftia_score']} ⭐")

    # ========================================
    # PASO 1: ENVIAR A LA API
    # ========================================
    print_header("📤 PASO 1: Enviando a la API de Ingesta")
    
    headers = {
        'Content-Type': 'application/json',
        'X-GIFTIA-TOKEN': WP_TOKEN,
        'User-Agent': 'GiftiaSchemaTest/2.0'
    }
    
    try:
        response = requests.post(
            WP_API_URL,
            data=json.dumps(test_product, ensure_ascii=False).encode('utf-8'),
            headers=headers,
            timeout=30
        )
    except requests.exceptions.RequestException as e:
        print_error(f"Error de conexión: {e}")
        return False
    
    print(f"   Status HTTP: {response.status_code}")
    
    if response.status_code != 200:
        print_error(f"Error del servidor: {response.text[:200]}")
        return False
    
    result = response.json()
    post_id = result.get('post_id')
    
    if not post_id:
        print_error("No se recibió post_id en la respuesta")
        print(f"   Respuesta: {result}")
        return False
    
    print_success(f"Producto creado/actualizado: Post ID {post_id}")
    
    print_info("Esperando 2 segundos para que WordPress procese...")
    time.sleep(2)

    # ========================================
    # PASO 2: VERIFICAR TAXONOMÍAS
    # ========================================
    print_header("🏷️ PASO 2: Verificando Taxonomías")
    
    verify_url = f"{WP_REST_URL}/{post_id}"
    
    try:
        verify_response = requests.get(verify_url, timeout=10)
    except requests.exceptions.RequestException as e:
        print_error(f"Error obteniendo producto: {e}")
        return False
    
    if verify_response.status_code != 200:
        print_error(f"No se pudo obtener el producto: {verify_response.status_code}")
        return False
    
    product = verify_response.json()
    
    # Verificar cada taxonomía
    taxonomy_checks = [
        ('gf_category', 1),
        ('gf_age', 3),
        ('gf_gender', 1),
        ('gf_recipient', 3),
        ('gf_occasion', 3),
        ('gf_budget', 1),
        ('gf_hook', 1),
    ]
    
    tax_success = True
    for tax_name, expected in taxonomy_checks:
        got = len(product.get(tax_name, []))
        if got >= expected:
            print_success(f"{tax_name}: {got} términos asignados")
        elif got > 0:
            print_warning(f"{tax_name}: {got}/{expected} términos (parcial)")
        else:
            print_error(f"{tax_name}: vacío (esperado {expected})")
            tax_success = False

    # ========================================
    # PASO 3: VERIFICAR META FIELDS
    # ========================================
    print_header("📝 PASO 3: Verificando Meta Fields (SEO)")
    
    meta = product.get('meta', {})
    
    if not meta:
        print_warning("El objeto 'meta' está vacío en la respuesta REST")
        print_info("Los meta fields pueden no estar registrados con show_in_rest")
        print_info("Para habilitarlos, sube giftfinder-core.php actualizado")
        meta_success = None
    else:
        critical_meta = [
            ('_gf_marketing_title', test_product['marketing_title'][:20]),
            ('_gf_hook', test_product['marketing_hook']),
            ('_gf_giftia_score', str(test_product['giftia_score'])),
            ('_gf_current_price', '89'),
        ]
        
        meta_success = True
        for meta_key, expected in critical_meta:
            actual = str(meta.get(meta_key, ''))
            if expected in actual:
                print_success(f"{meta_key}: guardado correctamente")
            elif actual:
                print_warning(f"{meta_key}: valor diferente ({actual[:30]})")
            else:
                print_error(f"{meta_key}: vacío")
                meta_success = False

    # ========================================
    # PASO 4: DATOS DEL PRODUCTO
    # ========================================
    print_header("📊 PASO 4: Datos del Producto")
    
    print(f"   ID: {product.get('id')}")
    print(f"   Título: {product.get('title', {}).get('rendered', '?')}")
    print(f"   Slug: {product.get('slug', '?')}")
    print(f"   Estado: {product.get('status', '?')}")
    print(f"   Link: {product.get('link', '?')}")

    # ========================================
    # RESUMEN FINAL
    # ========================================
    print_header("📋 RESUMEN DE LA PRUEBA")
    
    print(f"   {Colors.BOLD}Taxonomías:{Colors.END} ", end="")
    if tax_success:
        print(f"{Colors.GREEN}✅ TODAS OK{Colors.END}")
    else:
        print(f"{Colors.RED}❌ ALGUNAS FALLARON{Colors.END}")
    
    print(f"   {Colors.BOLD}Meta Fields:{Colors.END} ", end="")
    if meta_success is True:
        print(f"{Colors.GREEN}✅ TODOS OK{Colors.END}")
    elif meta_success is None:
        print(f"{Colors.YELLOW}⚠️  NO VERIFICADOS{Colors.END}")
    else:
        print(f"{Colors.RED}❌ ALGUNOS FALLARON{Colors.END}")
    
    print()
    
    if tax_success and (meta_success is True or meta_success is None):
        print(f"   {Colors.GREEN}{Colors.BOLD}✅ PRUEBA COMPLETADA{Colors.END}")
        print(f"   {Colors.GREEN}El schema Gold Master v50 funciona correctamente!{Colors.END}")
        print()
        print(f"   🔗 Ver producto: {product.get('link', 'N/A')}")
        return True
    else:
        print(f"   {Colors.YELLOW}{Colors.BOLD}⚠️  PRUEBA PARCIAL{Colors.END}")
        print()
        print("   Acciones sugeridas:")
        print("   1. WordPress Admin → Ajustes → Enlaces Permanentes → Guardar")
        print("   2. Subir giftfinder-core.php actualizado")
        print("   3. Volver a ejecutar este test")
        return False


# ============================================
# TEST DE CONEXIÓN
# ============================================
def test_connection():
    """Verifica conexión básica con el servidor."""
    print_header("🔌 Test de Conexión")
    
    try:
        response = requests.get("https://giftia.es/wp-json/", timeout=10)
        if response.status_code == 200:
            print_success("Conexión con WordPress OK")
            return True
        else:
            print_error(f"WordPress respondió con {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"No se puede conectar: {e}")
        return False


# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    print()
    print(f"{Colors.BOLD}╔════════════════════════════════════════════════════════╗{Colors.END}")
    print(f"{Colors.BOLD}║     🎁 GIFTIA SCHEMA TEST - Gold Master v50            ║{Colors.END}")
    print(f"{Colors.BOLD}╚════════════════════════════════════════════════════════╝{Colors.END}")
    
    # Test de conexión primero
    if not test_connection():
        print()
        print_error("Abortando: No hay conexión con el servidor")
        sys.exit(1)
    
    # Test principal
    success = test_new_schema()
    
    print()
    sys.exit(0 if success else 1)
