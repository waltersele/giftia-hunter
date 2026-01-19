#!/usr/bin/env python3
"""
Test de reparación SEO - SOLO 1 producto
"""

import sys
import os
sys.path.append('.')

from fix_massive_seo import *

def test_single_product():
    print("🔧 TEST: Procesar 1 producto con SEO v51")
    print("="*50)
    
    # Obtener productos
    products = get_products_without_seo()
    if not products:
        print("❌ No hay productos sin SEO")
        return
    
    # Tomar solo el primero
    product = products[0]
    product_id = product['id']
    title = product['title']
    asin = product['asin']
    price = product.get('price', 49.99)  # Precio por defecto si es 0
    
    print(f"📦 Producto: ID {product_id}")
    print(f"   Título: {title}")
    print(f"   ASIN: {asin}")
    print(f"   Precio: {price}€")
    
    # Generar SEO con Gemini
    print(f"\n🧠 Generando SEO con Gemini...")
    try:
        seo_data = generate_seo_with_gemini(title, price, asin)
    except Exception as e:
        print(f"❌ Error en Gemini: {e}")
        return
    
    if not seo_data:
        print("❌ Error generando SEO")
        return
    
    if not seo_data.get('is_good_gift', False):
        print("❌ Gemini rechazó el producto")
        return
        
    print(f"✅ SEO generado:")
    print(f"   SEO Title: {seo_data.get('seo_title', '')}")
    print(f"   H1 Title: {seo_data.get('h1_title', '')}")
    print(f"   Meta Desc: {seo_data.get('meta_description', '')[:60]}...")
    
    # Actualizar en WordPress
    print(f"\n💾 Actualizando en WordPress...")
    
    success = update_product_with_seo(product_id, asin, price, seo_data)
    
    if success:
        print(f"✅ Producto actualizado correctamente!")
    else:
        print(f"❌ Error actualizando producto")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    test_single_product()