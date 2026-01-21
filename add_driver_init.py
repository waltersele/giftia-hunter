#!/usr/bin/env python3
"""
Agregar inicialización de driver dentro del main
"""

with open("hunter.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

driver_init = """    
    # Initialize Chrome driver
    print("Setting up Chrome driver...")
    options = Options()
    if not DEBUG:
        options.add_argument("--headless")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager(driver_version="144.0.7559.59").install()), options=options)
        logger.info("[OK] Chrome driver initialized")
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize Chrome: {e}")
        sys.exit(1)

"""

new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    # Agregar driver init después de "Fin previsto:"
    if "Fin previsto:" in line and "logger.info" in line:
        new_lines.append(driver_init)

with open("hunter.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("OK: Driver init agregado en main")
