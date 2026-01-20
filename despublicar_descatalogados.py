#!/usr/bin/env python3
"""
Despublicar productos descatalogados de Amazon
Cambia el status a 'draft' para que no aparezcan en la web
"""

import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php"
TOKEN = os.getenv("WP_API_TOKEN")

def despublicar_productos():
    # Cargar productos no encontrados
    with open("asins_no_encontrados.json", "r", encoding="utf-8") as f:
        productos = json.load(f)
    
    print("=" * 60)
    print("DESPUBLICAR PRODUCTOS DESCATALOGADOS")
    print("=" * 60)
    print(f"Productos a despublicar: {len(productos)}")
    print()
    
    headers = {"X-GIFTIA-TOKEN": TOKEN}
    
    exitos = 0
    fallos = 0
    
    for p in productos:
        post_id = p["post_id"]
        titulo = p["title"][:50]
        
        # Usar endpoint para cambiar status a draft
        payload = {
            "post_id": post_id,
            "status": "draft",
            "reason": "descatalogado_amazon"
        }
        
        try:
            r = requests.post(
                f"{API_URL}?action=update_status",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if r.status_code == 200:
                data = r.json()
                if data.get("success"):
                    print(f"✅ {post_id}: {titulo}...")
                    exitos += 1
                else:
                    print(f"❌ {post_id}: {data.get('error', 'Error desconocido')}")
                    fallos += 1
            else:
                print(f"❌ {post_id}: HTTP {r.status_code}")
                fallos += 1
                
        except Exception as e:
            print(f"❌ {post_id}: {str(e)}")
            fallos += 1
    
    print()
    print("=" * 60)
    print(f"RESUMEN: ✅ {exitos} despublicados | ❌ {fallos} fallos")
    print("=" * 60)

if __name__ == "__main__":
    despublicar_productos()
