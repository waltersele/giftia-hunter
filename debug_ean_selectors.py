#!/usr/bin/env python3
"""
Debug script to extract technical details from Amazon product pages
and find where EAN/GTIN is displayed
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Test ASIN - producto conocido con EAN
TEST_ASIN = "B079HJ3N96"  # RIEDEL Extreme Pinot Noir (visto en queue)

# Setup Chrome
chrome_options = Options()
# chrome_options.add_argument("--headless")  # COMENTADO para ver la página
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

try:
    url = f"https://www.amazon.es/dp/{TEST_ASIN}"
    print(f"Abriendo: {url}")
    driver.get(url)
    time.sleep(3)
    
    print("\n" + "="*80)
    print("BÚSQUEDA 1: #detailBullets_feature_div li")
    print("="*80)
    try:
        detail_bullets = driver.find_elements(By.CSS_SELECTOR, "#detailBullets_feature_div li")
        print(f"OK Encontradas {len(detail_bullets)} filas")
        for i, row in enumerate(detail_bullets):
            text = row.text.strip()
            if text:
                print(f"  [{i}] {text[:150]}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*80)
    print("BÚSQUEDA 2: #productDetails_detailBullets_sections1 tr")
    print("="*80)
    try:
        detail_sections1 = driver.find_elements(By.CSS_SELECTOR, "#productDetails_detailBullets_sections1 tr")
        print(f"✓ Encontradas {len(detail_sections1)} filas")
        for i, row in enumerate(detail_sections1):
            text = row.text.strip()
            if text:
                print(f"  [{i}] {text[:150]}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*80)
    print("BÚSQUEDA 3: .prodDetTable tr")
    print("="*80)
    try:
        prod_det_table = driver.find_elements(By.CSS_SELECTOR, ".prodDetTable tr")
        print(f"✓ Encontradas {len(prod_det_table)} filas")
        for i, row in enumerate(prod_det_table):
            text = row.text.strip()
            if text:
                print(f"  [{i}] {text[:150]}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*80)
    print("BÚSQUEDA 4: #prodDetails tr (alternativa)")
    print("="*80)
    try:
        prod_details = driver.find_elements(By.CSS_SELECTOR, "#prodDetails tr")
        print(f"✓ Encontradas {len(prod_details)} filas")
        for i, row in enumerate(prod_details):
            text = row.text.strip()
            if text:
                print(f"  [{i}] {text[:150]}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*80)
    print("BÚSQUEDA 5: Búsqueda genérica con texto 'EAN' o 'GTIN'")
    print("="*80)
    try:
        # Buscar todos los elementos que contengan "EAN" o "GTIN" en el texto
        all_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ean') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'gtin')]")
        print(f"✓ Elementos con EAN/GTIN: {len(all_elements)}")
        for i, el in enumerate(all_elements[:10]):  # Primeros 10
            text = el.text.strip() if el.text else ""
            parent_html = el.get_attribute('outerHTML')[:300] if el.get_attribute('outerHTML') else ""
            print(f"\n  [{i}] Tag={el.tag_name}")
            print(f"      ID={el.get_attribute('id')}")
            print(f"      Class={el.get_attribute('class')}")
            print(f"      Text={text[:200] if text else '(sin texto)'}")
            print(f"      HTML={parent_html}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*80)
    print("OK Analisis completo. Presiona Ctrl+C para cerrar el navegador.")
    print("="*80)
    
    # NO WAIT - cerrar inmediatamente para capturar output

finally:
    driver.quit()
