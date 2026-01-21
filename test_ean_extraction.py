"""
Test EAN Extraction from Amazon
Verifica si podemos extraer el código EAN de productos Amazon
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Configurar Selenium
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

driver = webdriver.Chrome(options=chrome_options)

# URL de test (un producto con EAN conocido)
test_url = "https://www.amazon.es/dp/B08L5YVJRV"  # Ejemplo: Echo Dot

try:
    print(f"Accediendo a: {test_url}")
    driver.get(test_url)
    time.sleep(3)
    
    # Buscar tabla de detalles técnicos
    ean = None
    
    # Método 1: Buscar en tabla de detalles del producto
    try:
        detail_table = driver.find_elements(By.CSS_SELECTOR, "#productDetails_detailBullets_sections1 tr")
        for row in detail_table:
            th_text = row.find_element(By.TAG_NAME, "th").text.strip().lower()
            if any(term in th_text for term in ['ean', 'código de barras', 'gtin']):
                ean = row.find_element(By.TAG_NAME, "td").text.strip()
                print(f"✓ EAN encontrado (detalles): {ean}")
                break
    except Exception as e:
        print(f"No se encontró en detalle: {e}")
    
    # Método 2: Buscar en sección de información adicional
    if not ean:
        try:
            additional_info = driver.find_elements(By.CSS_SELECTOR, "#productDetails_techSpec_section_1 tr")
            for row in additional_info:
                th_text = row.find_element(By.TAG_NAME, "th").text.strip().lower()
                if any(term in th_text for term in ['ean', 'código de barras', 'gtin', 'upc']):
                    ean = row.find_element(By.TAG_NAME, "td").text.strip()
                    print(f"✓ EAN encontrado (tech spec): {ean}")
                    break
        except Exception as e:
            print(f"No se encontró en tech spec: {e}")
    
    # Método 3: Buscar en cualquier tabla con class detailBullets
    if not ean:
        try:
            all_rows = driver.find_elements(By.CSS_SELECTOR, ".detail-bullet-list li, .a-unordered-list li")
            for row in all_rows:
                text = row.text.lower()
                if 'ean' in text or 'código de barras' in text or 'gtin' in text:
                    # Extraer el código (usualmente después de ':')
                    if ':' in row.text:
                        ean = row.text.split(':')[1].strip()
                        print(f"✓ EAN encontrado (bullets): {ean}")
                        break
        except Exception as e:
            print(f"No se encontró en bullets: {e}")
    
    if not ean:
        print("✗ No se pudo encontrar el EAN en esta página")
        print("\n=== HTML de productDetails ===")
        try:
            details_section = driver.find_element(By.ID, "productDetails")
            print(details_section.text[:500])
        except:
            print("No se pudo acceder a productDetails")
    else:
        print(f"\n✓ ÉXITO: EAN extraído correctamente: {ean}")

except Exception as e:
    print(f"✗ ERROR: {e}")

finally:
    driver.quit()
