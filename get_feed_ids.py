"""Obtener feed_id de merchants Awin"""
import requests, os, csv
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("AWIN_API_KEY")
pub_id = os.getenv("AWIN_PUBLISHER_ID", "1429881")

merchants = {
    13075: "El Corte Inglés",
    27904: "Sprinter", 
    24562: "Padel Market"
}

print("🔍 Buscando feeds...\n")

for mid, name in merchants.items():
    url = f"https://productdata.awin.com/datafeed/list/apikey/{key}/cid/{pub_id}/mid/{mid}/"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            lines = r.text.strip().split('\n')
            print(f"{name} (ID {mid}):")
            for line in lines[:3]:
                parts = line.split(',')
                if len(parts) >= 3:
                    feed_id, lang, products = parts[0], parts[1], parts[3]
                    print(f"  Feed {feed_id}: {lang} - {products} productos")
            print()
        else:
            print(f"{name}: Error {r.status_code}\n")
    except Exception as e:
        print(f"{name}: {e}\n")
