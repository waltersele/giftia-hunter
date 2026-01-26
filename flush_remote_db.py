#!/usr/bin/env python3
import os
import requests
import sys
from dotenv import load_dotenv

# Cargar entorno
load_dotenv()

WP_API_URL = os.getenv("WP_API_URL", "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php")
WP_TOKEN = os.getenv("WP_API_TOKEN")

if not WP_TOKEN:
    print("❌ Error: No se encontró WP_API_TOKEN en .env")
    sys.exit(1)

print(f"🔥 INICIANDO FLUSH TOTAL DE BASE DE DATOS REMOTA")
print(f"🎯 Target: {WP_API_URL}")
print("⚠️ ESTO BORRARÁ TODOS LOS PRODUCTOS 'gf_gift'. Tienes 5 segundos para cancelar (Ctrl+C).")

import time
try:
    for i in range(5, 0, -1):
        print(f"{i}...")
        time.sleep(1)
except KeyboardInterrupt:
    print("\n🛑 Cancelado.")
    sys.exit(0)

try:
    # URL de acción directa al script flush-v52.php
    # Asumimos que el usuario lo sube a la carpeta del plugin
    base_url = WP_API_URL.replace("api-ingest.php", "flush-v52.php")
    url = f"{base_url}?key=force_flush_v52"
    
    print(f"🚀 Enviando orden de purga a: {url}")
    # Usamos GET para el script standalone
    response = requests.get(url, timeout=30)
    
    print(f"📡 Status Code: {response.status_code}")
    print(f"📄 Respuesta: {response.text}")
    
    if response.status_code == 200 and "success" in response.text:
        print("\n✅ BASE DE DATOS LIMPIA. FLUSH EXITOSO.")
    else:
        print("\n❌ Error. Asegúrate de subir 'flush-v52.php' al servidor.")


except Exception as e:
    print(f"❌ Excepción: {e}")
