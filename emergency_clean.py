import json
import os

QUEUE_FILE = 'pending_products.json'
BACKUP_FILE = 'pending_products.json.bak'

# Palabras prohibidas explícitas (Music & Media)
KILLER_KEYWORDS = [
    " cd", "(cd)", "dvd", "vinilo", "lp-vinilo", "banda sonora", "soundtrack",
    "partitura", "blu-ray", "single cd", "disco compact", "álbum musical", 
    "music", "música", "canciones"
]

BAD_CATEGORIES = [
    "música", "music", "cine", "movies", "libros", "books", "papelería", 
    "revistas", "películas"
]

def clean_queue():
    if not os.path.exists(QUEUE_FILE):
        print("No hay cola para limpiar.")
        return

    print(f"🧹 Iniciando limpieza profunda de {QUEUE_FILE}...")
    
    with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
        queue = json.load(f)
    
    initial_count = len(queue)
    clean_items = []
    removed_count = 0
    
    for item in queue:
        title_lower = item.get('title', '').lower()
        desc_lower = item.get('description', '').lower()
        # Algunos items traen category del CSV, otros no
        cat_lower = item.get('category', '').lower() if 'category' in item else ""

        is_bad = False

        # 1. Filtro por Categoría
        for bad_cat in BAD_CATEGORIES:
            if bad_cat in cat_lower:
                is_bad = True
                break
        
        if is_bad:
            removed_count += 1
            continue

        # 2. Filtro por Keywords en Título
        for kw in KILLER_KEYWORDS:
            if kw in title_lower:
                is_bad = True
                break
        
        if is_bad:
            removed_count += 1
            continue
            
        # 3. Filtro Precio (Safety Check)
        if item.get('price', 0) < 12:
             removed_count += 1
             continue

        clean_items.append(item)

    # Crear backup
    if os.path.exists(QUEUE_FILE):
        os.rename(QUEUE_FILE, BACKUP_FILE)

    # Guardar cola limpia
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(clean_items, f, indent=2, ensure_ascii=False)

    print(f"✅ Limpieza completada.")
    print(f"   Inicales: {initial_count}")
    print(f"   Eliminados (Música/Basura): {removed_count}")
    print(f"   Restantes (Válidos): {len(clean_items)}")

if __name__ == "__main__":
    clean_queue()
