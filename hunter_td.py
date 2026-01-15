import requests
import json
import time

# --- CONFIGURACIÓN ---
WP_TOKEN = "nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5"
WP_API_URL = "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php"

# --- DATOS TRADEDOUBLER ---
# CUANDO TENGAS EL TOKEN, PÉGALO AQUÍ ABAJO BORRANDO EL TEXTO ACTUAL:
TD_TOKEN = "ESPERANDO_APROBACION" 
REGION = "ES"

BUSQUEDAS = ["xbox series x", "lavadora", "philips hue", "surface pro", "escapada fin de semana", "portatil gaming"]

def enviar_a_giftia(datos):
    print(f"   🚀 Enviando: {datos['title'][:30]}... ({datos['price']}€)")
    try:
        headers = {'Content-Type': 'application/json', 'X-GIFTIA-TOKEN': WP_TOKEN}
        resp = requests.post(WP_API_URL, data=json.dumps(datos), headers=headers)
        if resp.status_code == 200:
            res_json = resp.json()
            if res_json.get('success'):
                print(f"   ✅ {res_json.get('message')}")
            else:
                print(f"   ⚠️ WP: {res_json.get('message')}")
        else:
            print(f"   ❌ Error Server: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Error Conexión: {e}")

print(f"🤖 Iniciando Hunter Tradedoubler...")

# --- SISTEMA DE SEGURIDAD PARA CUENTA PENDIENTE ---
if TD_TOKEN == "ESPERANDO_APROBACION":
    print("⏳ AVISO: La cuenta de Tradedoubler aún no está aprobada.")
    print("   -> El script se saltará este paso hasta que actualices el Token.")
    print("   -> Siguiente paso...")
    exit()
# --------------------------------------------------

for query in BUSQUEDAS:
    print(f"\n🌍 Consultando Tradedoubler para: '{query}'...")
    
    url = f"http://api.tradedoubler.com/1.0/products.json;q={query};token={TD_TOKEN};limit=5"
    
    try:
        r = requests.get(url)
        
        if r.status_code == 200:
            data = r.json()
            productos = data.get("productHeader", {}).get("products", [])
            
            print(f"   📦 TD encontró {len(productos)} productos.")
            
            for prod in productos:
                try:
                    title = prod.get("name", "")
                    offers = prod.get("offers", [])
                    if not offers: continue
                    
                    offer = offers[0]
                    price = "0"
                    if offer.get("priceHistory"):
                        price = offer.get("priceHistory")[0].get("price", "0")
                    
                    affiliate_url = offer.get("productUrl", "")
                    vendor_name = offer.get("programName", "Tradedoubler")
                    
                    image_data = prod.get("productImage", {})
                    image_url = image_data.get("url", "")
                    
                    td_id = prod.get("groupingId", "") or offer.get("id", "")

                    if not title or float(price) == 0: continue

                    payload = {
                        "title": title,
                        "asin": "TD-" + str(td_id),
                        "price": price,
                        "image_url": image_url,
                        "vendor": vendor_name, 
                        "affiliate_url": affiliate_url,
                        "is_active": 1
                    }
                    
                    enviar_a_giftia(payload)
                    time.sleep(0.5)

                except Exception as e:
                    print(f"   ⚠️ Error procesando item: {e}")
        else:
            print(f"   ❌ Error TD API ({r.status_code})")

    except Exception as e:
        print(f"   🔥 Error Fatal: {e}")
    
    time.sleep(1)

print("\n🏁 Caza en Tradedoubler terminada.")