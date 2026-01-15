#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GIFTIA HUNTER v8.0 - Advanced Gift Discovery Engine
Scrapes Amazon with intelligent filtering, relevance scoring, and multi-vibe targeting
Automatically sends discovered gifts to Giftia API with classification metadata
"""

import time
import json
import random
import requests
import logging
import os
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ============================================================================
# CONFIGURACIÓN CENTRALIZADA
# ============================================================================

# Environment-based configuration
WP_TOKEN = os.getenv("WP_API_TOKEN", "nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5")  # Fallback para desarrollo
WP_API_URL = os.getenv("WP_API_URL", "https://giftia.es/wp-json/giftia/v1/ingest")  # NUEVA RUTA REST API
AMAZON_TAG = os.getenv("AMAZON_TAG", "GIFTIA-21")
DEBUG = os.getenv("DEBUG", "0") == "1"

# Logging setup with UTF-8 encoding for Windows compatibility
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('hunter.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  # Explicit stdout
    ]
)
logger = logging.getLogger(__name__)

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logger.info("[HUNTER] INICIANDO v8.0 - Advanced Gift Discovery Engine")
logger.info(f"[HUNTER] API Endpoint: {WP_API_URL}")
logger.info(f"[HUNTER] Debug Mode: {'ENABLED' if DEBUG else 'DISABLED'}")

# ============================================================================
# BÚSQUEDAS INTELIGENTES POR CATEGORÍA (Mapeo a Vibes/Recipients)
# ============================================================================

SMART_SEARCHES = {
    # TECH VIBE (Tecnofilo, Gamer, Early adopter)
    "Tech": [
        "gadgets tecnologicos innovadores 2024",
        "accesorios gaming pc última generación",
        "drones DJI profesionales 4K",
        "smartwatch fitness deportivo premium",
        "auriculares inalámbricos gaming",
        "teclados mecánicos RGB programables",
        "powerbank solar carga rápida",
        "lámparas LED RGB inteligentes",
        "mouse gaming inalámbrico profesional",
        "webcam 4K streaming profesional"
    ],
    
    # GOURMET (Foodie, Cocinero, Sommelier)
    "Gourmet": [
        "kit cata vinos premium españa",
        "aceite oliva virgen extra denominación origen",
        "chocolatería artesanal gourmet",
        "set especias premium chef",
        "cortador jamón serrano profesional",
        "tabla quesos madera noble",
        "set cuchillos cocina damasco",
        "coffee maker specialty profesional",
        "copas vino cristal bohemia",
        "infusiones premium té gourmet"
    ],
    
    # FRIKI (Fanático, Coleccionista, Geek)
    "Friki": [
        "funkos pop edición limitada coleccionista",
        "replica espada Lord of the Rings oficial",
        "póster metal Batman vintage retro",
        "figura estatua Dragon Ball Super",
        "manga colección completa bestsellers",
        "camiseta gaming streetwear",
        "gorro beanie Harry Potter oficial",
        "lego architecture monumentos famosos",
        "poster star wars hologramas",
        "peluche animé oficial licenciado"
    ],
    
    # ZEN (Meditación, Wellness, Spa)
    "Zen": [
        "vela aromática soya natural perfumada",
        "difusor ultrasónico aromas aceites",
        "colchoneta yoga antideslizante premium",
        "cojín meditación espelta ecológico",
        "masajeador cervical vibración calor",
        "sal cristal himalaya auténtica",
        "pulsera chakra piedras naturales",
        "incienso japonés kyoto premium",
        "almohada memory foam cervical",
        "lámpara sal cristal himalaya"
    ],
    
    # VIAJES (Viajero, Mochilero, Aventurero)
    "Viajes": [
        "mochila trekking 50L impermeable técnica",
        "maleta cabina expandible TSA aprob",
        "almohada viaje cuello gel memory",
        "portadocumentos RFID organizador",
        "tarjeta eSIM datos internacionales",
        "adaptador universal viajero 250W",
        "filtro agua portátil acampada",
        "brújula digital GPS profesional",
        "botella agua inteligente acero inox",
        "linterna LED recargable USB camping"
    ],
    
    # DEPORTE (Deportista, Fitness, Aventurero)
    "Deporte": [
        "banda elástica resistencia entrenamiento",
        "smartwatch deportivo GPS running",
        "botellas hidratación BPA free 1L",
        "rodillo foam massage recovery",
        "protecciones rodilla tobillo neopreno",
        "mochila correr hidratación integrada",
        "cuerda saltar velocidad profesional",
        "mat yoga antideslizante grosor",
        "guantes ciclismo acolchados profesional",
        "tubo masaje vibración muscular recovery"
    ],
    
    # MODA (Fashionista, Diseño, Estilo)
    "Moda": [
        "reloj minimalista diseño nórdico",
        "gafas de sol aviador UV protection",
        "cinturón cuero genuino italiano",
        "bolso cuero vintage piel natural",
        "zapatillas sneaker diseño limitado",
        "bufanda pashmina lana merino",
        "cartera piel RFID seguridad",
        "corbata seda italiano nudo mágico",
        "sombrero fedora fieltro lana",
        "joyería plata 925 diseño exclusivo"
    ]
}

# ============================================================================
# FILTRADO AVANZADO - Anti-basura profesional
# ============================================================================

BLACKLIST = {
    # Palabras completamente prohibidas
    "banned_keywords": [
        "calentador agua", "tendedero", "grifo", "recambio", "batería", "pila", "aceite motor", 
        "fregona", "detergente", "papel higienico", "filtro aire", "bombilla", "cable usb",
        "adaptador", "tornillo", "destornillador", "funda teléfono", "protector pantalla",
        "enchufe", "regleta", "soporte monitor", "cristal templado", "bolsa plástico",
        "alfombrilla mouse", "molde horno", "descalcificador", "pastillas", "repuesto",
        "tinta cartucho", "papel aluminio", "spray", "limpiador", "cepillo dientes",
        "rasuradora", "secador pelo", "plancha ropa", "mop", "escoba", "pala",
        "tubo pvc", "clavos", "tornillos", "herramientas", "taladro", "sierra",
        "bombona", "tanque", "tubo", "válvula", "manguera", "conector",
    ],
    
    # Palabras sospechosas que disminuyen score
    "suspicious_keywords": [
        "fake", "réplica", "genérico", "aroma relleno", "pack ahorro", "lote",
        "sobrante", "outlet", "defectuoso", "reparado", "reacondicionado",
        "imitación", "copia", "genérico", "compatible con"
    ],
    
    # Precios sospechosos
    "min_price_eur": 12.0,      # Nada por debajo de 12€
    "max_price_eur": 9999.0,    # Nada absurdamente caro
    "preferred_price_range": (20, 500),  # Rango ideal para regalos
    
    # Requisitos de calidad
    "min_title_length": 15,     # Títulos demasiado cortos = basura
    "max_title_length": 200,    # Títulos demasiado largos = spam
}

# ============================================================================
# PALABRAS CLAVE DE RELEVANCIA - Scoring de regalos
# ============================================================================

GIFT_KEYWORDS = {
    "premium": 10,
    "exclusivo": 10,
    "limitado": 9,
    "edición especial": 9,
    "oficial": 8,
    "auténtico": 8,
    "licenciado": 8,
    "original": 7,
    "handmade": 9,
    "artesanal": 8,
    "ecológico": 7,
    "orgánico": 7,
    "sostenible": 6,
    "premium quality": 8,
    "pro": 5,
    "profesional": 6,
    "expert": 6,
    "master": 5,
}


# ============================================================================
# MOTOR DE SCORING Y FILTRADO
# ============================================================================

def calculate_gift_score(title, price_str, description=""):
    """
    Calcula puntuación de 0-100 para determinar si es un regalo perfecto.
    Basado en: palabras clave premium, rango de precio, relevancia.
    """
    score = 50  # Base score
    
    title_lower = title.lower()
    desc_lower = description.lower()
    full_text = (title_lower + " " + desc_lower).lower()
    
    try:
        price = float(price_str.replace(",", ".").replace("€", ""))
    except:
        return 0  # No price = not a gift
    
    # Penalización por precio fuera de rango
    if price < BLACKLIST["min_price_eur"]:
        return 0
    if price > BLACKLIST["max_price_eur"]:
        return 0
    
    # Bonus por rango ideal de regalo (20-500€)
    if BLACKLIST["preferred_price_range"][0] <= price <= BLACKLIST["preferred_price_range"][1]:
        score += 20
    elif price > 500:
        score -= 5
    
    # Búsqueda de palabras clave premium
    for keyword, points in GIFT_KEYWORDS.items():
        if keyword in full_text:
            score += min(points, 15)  # Cap a 15 puntos por keyword
    
    # Penalizar palabras sospechosas
    for keyword in BLACKLIST["suspicious_keywords"]:
        if keyword in full_text:
            score -= 10
    
    # Validación de longitud de título
    if len(title) < BLACKLIST["min_title_length"]:
        score -= 20
    if len(title) > BLACKLIST["max_title_length"]:
        score -= 15
    
    # Bonus por signos de calidad
    if "★" in title or "⭐" in title:
        score += 5
    if "official" in title_lower or "oficial" in title_lower:
        score += 10
    
    return max(0, min(100, score))  # Clamp a 0-100


def is_garbage(title, price_str, description=""):
    """
    Descarta basura definitiva.
    Retorna True si es basura que no queremos enviar.
    """
    title_lower = title.lower()
    price_lower = price_str.lower()
    
    # Palabras prohibidas absolutas
    for banned in BLACKLIST["banned_keywords"]:
        if banned in title_lower:
            logger.debug(f"❌ Bannword detected: {banned} in {title[:40]}")
            return True
    
    # Validación de precio
    try:
        price = float(price_str.replace(",", ".").replace("€", ""))
        if price < BLACKLIST["min_price_eur"] or price > BLACKLIST["max_price_eur"]:
            return True
    except:
        return True  # Si no tiene precio válido = basura
    
    # Excluir packs/lotes genéricos
    if title_lower.count(" ") > 12:  # Títulos muy largos suelen ser maleza
        return True
    
    return False


def classify_product_vibes(title, description="", price_str=""):
    """
    Clasifica automáticamente el producto en vibes de Giftia.
    Retorna array de vibes que coinciden: ['Tech', 'Friki', etc]
    """
    text = (title + " " + description).lower()
    matched_vibes = []
    
    vibe_keywords = {
        "Tech": ["gadget", "tech", "electrónic", "usb", "inalámbric", "inteligent", "smart", "game", "gamer", "pc", "usb-c", "inalamb"],
        "Gourmet": ["café", "tea", "vino", "queso", "aceite", "gourmet", "cocinero", "chef", "especias", "chocolate", "jamón"],
        "Friki": ["funk", "pop", "star wars", "harry potter", "marvel", "anime", "manga", "coleccion", "geek", "nerd", "estatua", "figura"],
        "Zen": ["meditaci", "yoga", "spa", "aromaterapia", "difusor", "vela", "cristal", "chakra", "mindfulness", "relajaci"],
        "Viajes": ["mochila", "maleta", "viajero", "camping", "trekking", "acampad", "viaje", "portátil", "backpack"],
        "Deporte": ["deporte", "fitness", "runner", "yoga", "ejercicio", "gym", "bicicleta", "running", "entrenamiento", "sport"],
        "Moda": ["ropa", "zapatos", "bolso", "reloj", "gafas", "cinturón", "cartera", "sombrero", "bufanda", "joya", "moda"],
    }
    
    for vibe, keywords in vibe_keywords.items():
        for keyword in keywords:
            if keyword in text:
                matched_vibes.append(vibe)
                break  # Una vez encontrado, pasar al siguiente vibe
    
    return matched_vibes if matched_vibes else ["Friki"]  # Default


def classify_product_recipients(title, description=""):
    """
    Clasifica automáticamente para qué tipos de personas es ideal.
    Retorna array de recipients: ['Tech Lover', 'Foodie', etc]
    """
    text = (title + " " + description).lower()
    recipients = []
    
    recipient_keywords = {
        "Tech Lover": ["gadget", "tech", "smart", "digital", "electrónic", "usb", "app", "software"],
        "Foodie": ["food", "comida", "café", "vino", "queso", "gourmet", "chef", "cocinero"],
        "Geek": ["star wars", "harry potter", "marvel", "anime", "manga", "pop", "coleccion"],
        "Wellness Enthusiast": ["yoga", "meditaci", "spa", "aromaterapia", "relax", "zen"],
        "Adventurer": ["viaje", "mochila", "trekking", "camping", "aventura", "outdoor"],
        "Fitness Junkie": ["fitness", "deporte", "running", "gym", "entrenamiento", "sport"],
        "Fashion Icon": ["ropa", "moda", "zapatos", "bolso", "reloj", "estilo", "cartera"],
    }
    
    for recipient, keywords in recipient_keywords.items():
        for keyword in keywords:
            if keyword in text:
                recipients.append(recipient)
                break
    
    return recipients if recipients else ["Everyone"]


# ============================================================================
# SELENIUM DRIVER SETUP
# ============================================================================

print("🏹 Setting up Chrome driver...")
options = Options()
if not DEBUG:
    options.add_argument("--headless")
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    logger.info("[OK] Chrome driver initialized")
except Exception as e:
    logger.error(f"[ERROR] Failed to initialize Chrome: {e}")
    sys.exit(1)

# ============================================================================
# FUNCIÓN DE ENVÍO A GIFTIA
# ============================================================================

def send_to_giftia(datos):
    """
    Envía producto validado a la API de Giftia con metadata de clasificación.
    """
    # Validaciones previas
    if not datos.get("asin") or not datos.get("title"):
        logger.warning("Datos incompletos, ignorando")
        return False
    
    # Check garbage
    if is_garbage(datos["title"], datos.get("price", "0"), datos.get("description", "")):
        logger.debug(f"BASURA descartada: {datos['title'][:40]}...")
        return False
    
    # Calcular score
    score = calculate_gift_score(
        datos["title"], 
        datos.get("price", "0"),
        datos.get("description", "")
    )
    
    if score < 45:  # Threshold mínimo para enviar
        logger.debug(f"Score bajo ({score}): {datos['title'][:40]}...")
        return False
    
    # Clasificación automática
    vibes = classify_product_vibes(datos["title"], datos.get("description", ""), datos.get("price", ""))
    recipients = classify_product_recipients(datos["title"], datos.get("description", ""))
    
    # Enriquecer datos
    datos["vibes"] = vibes
    datos["recipients"] = recipients
    datos["gift_score"] = score
    datos["discovered_at"] = datetime.now().isoformat()
    
    # Envío
    logger.info(f"ENVIANDO [Score:{score}] {datos['title'][:50]}... vibes={vibes}")
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'X-GIFTIA-TOKEN': WP_TOKEN,
            'User-Agent': 'GiftiaHunter/8.0'
        }
        
        logger.debug(f"POST a {WP_API_URL}")
        logger.debug(f"Token: {WP_TOKEN[:10]}...")
        logger.debug(f"Datos: {json.dumps(datos, ensure_ascii=False)[:200]}...")
        
        response = requests.post(
            WP_API_URL,
            data=json.dumps(datos, ensure_ascii=False).encode('utf-8'),
            headers=headers,
            timeout=10
        )
        
        logger.debug(f"Respuesta status: {response.status_code}")
        logger.debug(f"Respuesta body: {response.text[:200]}")
        
        if response.status_code == 200:
            logger.info(f"OK: {datos['title'][:40]} guardado en WordPress")
            return True
        else:
            logger.error(f"Error API {response.status_code}: {response.text[:100]}")
            return False
            
    except Exception as e:
        logger.error(f"Excepcion al enviar: {str(e)}")
        return False


# ============================================================================
# BUCLE PRINCIPAL DE SCRAPING
# ============================================================================

logger.info(f"Starting main scraping loop at {datetime.now()}")

# Seleccionar vibes aleatorias para máxima variedad
selected_vibes = random.sample(list(SMART_SEARCHES.keys()), k=min(4, len(SMART_SEARCHES)))
logger.info(f"[VIBES] Selected: {selected_vibes}")

total_sent = 0
total_discarded = 0

try:
    for vibe in selected_vibes:
        searches = SMART_SEARCHES[vibe]
        # Seleccionar 2-3 búsquedas por vibe
        selected_searches = random.sample(searches, k=min(3, len(searches)))
        
        for query in selected_searches:
            # Agregar variación
            modifiers = ["", " 2024", " novedades", " bestseller"]
            final_query = query + random.choice(modifiers)
            
            logger.info(f"[SEARCH] [{vibe}] {final_query}")
            
            try:
                # URL con ordenamiento por novedad + rating
                amazon_url = f"https://www.amazon.es/s?k={final_query.replace(' ', '+')}&s=date-desc-rank&ref=sr_st_date-desc-rank"
                driver.get(amazon_url)
                
                # ESPERAR A QUE CARGUEN LOS PRODUCTOS CON JAVASCRIPT
                try:
                    # Esperar hasta 10 segundos a que aparezcan productos
                    wait = WebDriverWait(driver, 10)
                    items = wait.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-component-type="s-search-result"]'))
                    )
                    logger.debug(f"   Cargaron {len(items)} productos con WebDriverWait")
                except:
                    logger.debug(f"   WebDriverWait falló, usando JavaScript...")
                    # Usar JavaScript para ejecutar scroll y esperar
                    time.sleep(2)
                    driver.execute_script("window.scrollTo(0, 1000);")
                    time.sleep(2)
                    
                    # Encontrar items usando JavaScript
                    items_count = driver.execute_script("""
                        return document.querySelectorAll('[data-component-type="s-search-result"]').length;
                    """)
                    logger.debug(f"   JavaScript encontró {items_count} elementos")
                    
                    # Ahora buscar con Selenium
                    items = driver.find_elements(By.CSS_SELECTOR, 'div[data-component-type="s-search-result"]')
                    
                    # Si aún no encuentra, intentar selector alternativo
                    if len(items) == 0:
                        logger.debug(f"   Intentando selector alternativo...")
                        items = driver.find_elements(By.CSS_SELECTOR, 'div.s-result-item[data-asin]')
                
                logger.debug(f"   Found {len(items)} search results")
                
                captured_in_query = 0
                for item in items:
                    if captured_in_query >= 5:  # Máx 5 por búsqueda
                        break
                    
                    try:
                        # ASIN (identificador único)
                        asin = item.get_attribute("data-asin")
                        if not asin or len(asin) < 10:
                            continue
                        
                        # Título
                        try:
                            title = item.find_element(By.CSS_SELECTOR, "h2 a span").text.strip()
                        except:
                            continue
                        
                        if not title or len(title) < BLACKLIST["min_title_length"]:
                            continue
                        
                        # Precio
                        try:
                            price_elements = item.find_elements(By.CSS_SELECTOR, ".a-price .a-offscreen")
                            if price_elements:
                                price_txt = price_elements[0].get_attribute("textContent")
                                price = price_txt.replace("€", "").replace(".", "").replace(",", ".").strip()
                            else:
                                price = "0"
                        except:
                            price = "0"
                        
                        # Imagen
                        try:
                            image_url = item.find_element(By.CSS_SELECTOR, "img.s-image").get_attribute("src")
                            # Ensure HTTPS
                            if image_url and image_url.startswith("http://"):
                                image_url = image_url.replace("http://", "https://", 1)
                        except:
                            image_url = ""
                        
                        # Rating (optativo pero mejora score)
                        try:
                            rating = item.find_element(By.CSS_SELECTOR, ".a-star-small span").text
                        except:
                            rating = ""
                        
                        # Descripción/subtítulo (optativo)
                        try:
                            description = item.find_element(By.CSS_SELECTOR, ".a-color-base.a-text-normal").text
                        except:
                            description = ""
                        
                        # Construir payload
                        if float(price.replace(",", ".") or 0) > 0:
                            affiliate_url = f"https://www.amazon.es/dp/{asin}?tag={AMAZON_TAG}"
                            
                            payload = {
                                "title": title,
                                "asin": asin,
                                "price": price,
                                "image_url": image_url,
                                "vendor": "Amazon",
                                "affiliate_url": affiliate_url,
                                "description": description,
                                "rating": rating,
                                "source_vibe": vibe
                            }
                            
                            if send_to_giftia(payload):
                                total_sent += 1
                                captured_in_query += 1
                                time.sleep(random.uniform(0.3, 0.8))
                            else:
                                total_discarded += 1
                    
                    except Exception as e:
                        logger.debug(f"Error processing item: {e}")
                        continue
                
                time.sleep(random.uniform(2, 5))  # Pause between searches
                
            except Exception as e:
                logger.error(f"Error searching '{final_query}': {e}")
                continue
    
    logger.info(f"[DONE] Session completed!")
    logger.info(f"   Sent: {total_sent}")
    logger.info(f"   Discarded: {total_discarded}")
    logger.info(f"   Success rate: {(total_sent / max(1, total_sent + total_discarded) * 100):.1f}%")

except KeyboardInterrupt:
    logger.info("🛑 Interrupted by user")
except Exception as e:
    logger.error(f"Fatal error: {e}")
finally:
    driver.quit()
    logger.info("🏁 Driver closed, session ended")