#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inspect Amazon HTML structure to find correct selectors
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

print("[INFO] Abriendo Chrome...")
options = Options()
# options.add_argument("--headless")  # SIN headless para ver qué pasa
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

try:
    print("[INFO] Navegando a Amazon.es...")
    driver.get("https://www.amazon.es/s?k=smartphone+2024")
    time.sleep(3)
    
    print("[INFO] Buscando elementos...")
    print()
    
    # Intentar cada selector
    selectors = [
        ('div[data-component-type="s-search-result"]', 'CSS - data-component-type'),
        ('div.s-result-item', 'CSS - s-result-item'),
        ('div[data-asin]', 'CSS - data-asin'),
        ('div.s-card-container', 'CSS - s-card-container'),
        ('div[data-csa-c-slot-id]', 'CSS - data-csa-c-slot-id'),
        ('//div[@data-asin and @data-component-type="s-search-result"]', 'XPATH - data-asin + data-component'),
        ('//div[contains(@class, "s-result")]', 'XPATH - contains s-result'),
    ]
    
    for selector, desc in selectors:
        try:
            if selector.startswith('//'):
                elements = driver.find_elements(By.XPATH, selector)
            else:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
            
            print(f"✓ {desc}: encontró {len(elements)} elementos")
            
            if len(elements) > 0:
                # Mostrar el HTML del primer elemento
                first = elements[0]
                html = first.get_attribute('outerHTML')[:200]
                print(f"  HTML: {html}...")
                print()
        except Exception as e:
            print(f"✗ {desc}: error - {str(e)[:50]}")
    
    print("\n[INFO] Inspecciona el HTML en la consola de Chrome Developer Tools")
    print("[INFO] Presiona Enter para cerrar...")
    input()
    
finally:
    driver.quit()
    print("[INFO] Chrome cerrado")
