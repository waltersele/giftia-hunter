import requests
import json

AWIN_TOKEN = "84554931-d646-45b2-8fcd-a244e1c02f62"

headers = {
    "Authorization": f"Bearer {AWIN_TOKEN}",
    "Content-Type": "application/json"
}

print("🕵️‍♂️ Consultando ID oficial de Giftia...")

try:
    r = requests.get("https://api.awin.com/accounts", headers=headers)
    
    if r.status_code == 200:
        data = r.json()
        accounts = data.get("accounts", [])
        
        print("\n--- RESULTADO ---")
        for acc in accounts:
            print(f"Nombre: {acc.get('accountName')}")
            print(f"Tipo:   {acc.get('accountType')}")
            # AQUÍ ESTÁ LA CLAVE: Imprimimos el accountId
            print(f"👉 ID TÉCNICO: {acc.get('accountId')}") 
            print("-----------------")
            
    else:
        print(f"Error: {r.status_code}")

except Exception as e:
    print(f"Error: {e}")