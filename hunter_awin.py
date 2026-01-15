import requests
import json

# --- TUS DATOS ---
AWIN_TOKEN = "84554931-d646-45b2-8fcd-a244e1c02f62"

print("🩺 INICIANDO DIAGNÓSTICO AWIN...")

headers = {
    "Authorization": f"Bearer {AWIN_TOKEN}",
    "Content-Type": "application/json"
}

# 1. PREGUNTAR A LA API QUÉ CUENTAS TIENE ESTE TOKEN
print("\n1. Consultando tus cuentas (Endpoint /accounts)...")
url_accounts = "https://api.awin.com/accounts"

try:
    r = requests.get(url_accounts, headers=headers)
    
    if r.status_code == 200:
        data = r.json()
        print("✅ CONEXIÓN ÉXITOSA. Datos recibidos:")
        # print(json.dumps(data, indent=2)) # Descomentar para ver todo el json crudo
        
        accounts = data.get("accounts", [])
        if not accounts:
            print("⚠️ El Token es válido pero no devuelve ninguna cuenta asociada.")
        
        for acc in accounts:
            print(f"   👤 CUENTA ENCONTRADA: {acc.get('accountName')} (Type: {acc.get('accountType')})")
            
            # Buscamos los usuarios/publishers dentro de la cuenta
            # Dependiendo de la estructura, a veces el publisherId está visible aquí
            # Pero lo más seguro es listar los 'publishers' del usuario.
            
    else:
        print(f"❌ Error conectando ({r.status_code}): {r.text}")
        print("   -> Revisa si el TOKEN es correcto.")

except Exception as e:
    print(f"🔥 Error Fatal: {e}")


# 2. INTENTO DIRECTO DE LISTAR TUS IDS DE PUBLISHER
print("\n2. Buscando tu 'Publisher ID' Real...")
# A veces el endpoint /publishers devuelve la lista de todos los que tienes acceso
url_pubs = "https://api.awin.com/publishers"

try:
    r = requests.get(url_pubs, headers=headers)
    if r.status_code == 200:
        data = r.json()
        # AWIN a veces devuelve una lista directa o paginada
        print("✅ LISTA DE PUBLISHERS RECUPERADA:")
        for pub in data:
            # Intentamos sacar el ID y el Nombre
            pid = pub.get('id')
            name = pub.get('name')
            status = pub.get('status')
            print(f"   👉 ID REAL: {pid} | Nombre: {name} | Estado: {status}")
            
            if str(pid) == "2729530":
                print("      (Este coincide con el que usábamos. El ID parece correcto).")
            else:
                print("      (¡OJO! Este ID es diferente al que usábamos).")
                
    elif r.status_code == 404:
        print("⚠️ El endpoint /publishers dio 404. Es posible que tu cuenta sea nueva y no esté propagada.")
    else:
        print(f"❌ Error ({r.status_code}): {r.text}")

except Exception as e:
    print(f"🔥 Error: {e}")

print("\n🏁 Diagnóstico terminado.")