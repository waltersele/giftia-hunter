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
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

def parse_price(price_str):
    """Parse price string, handling non-breaking spaces and European formats."""
    if not price_str:
        return 0.0
    clean = str(price_str).replace('\xa0', '').replace('€', '').replace(',', '.').strip()
    clean = ''.join(c for c in clean if c.isdigit() or c == '.')
    try:
        return float(clean) if clean else 0.0
    except:
        return 0.0

GEMINI_TIMEOUT_SECONDS = 10
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
# BÚSQUEDAS POR CATEGORÍA - SIMPLIFICADO (6 VIBES + DIGITAL)
# Mapeo directo al frontend: Tech, Gourmet, Bienestar, Aventura, Estilo, Fandom
# ============================================================================

SMART_SEARCHES = {
    # =========================================================================
    # DIGITAL - Productos digitales para entrega inmediata
    # =========================================================================
    "Digital": [
        # Suscripciones
        "tarjeta regalo Netflix",
        "tarjeta regalo Spotify premium",
        "tarjeta regalo Amazon",
        "tarjeta regalo Steam",
        "tarjeta regalo PlayStation Store",
        "tarjeta regalo Xbox Game Pass",
        "tarjeta regalo Nintendo eShop",
        "tarjeta regalo Google Play",
        "tarjeta regalo Apple iTunes",
        "suscripción Audible regalo",
        "suscripción Kindle Unlimited regalo",
        "suscripción Amazon Prime regalo",
        "suscripción Disney Plus regalo",
        "suscripción HBO Max regalo",
        
        # Cursos y Formación
        "curso online Masterclass regalo",
        "curso Udemy regalo",
        "curso Domestika regalo",
        
        # Software & Licencias
        "Microsoft Office 365 código regalo",
        "licencia software regalo",
        
        # eBooks
        "ebook kindle bestseller regalo",
        "kindle ebook regalo",
    ],
    
    # =========================================================================
    # TECH & GAMING - Gadgets, Consolas, Smart Home
    # =========================================================================
    "Tech": [
        # Gadgets originales
        "gadgets tecnologicos regalo original",
        "mini proyector portatil regalo",
        "cargador inalámbrico diseño premium",
        "lámpara LED inteligente RGB WiFi",
        "marco digital fotos WiFi regalo",
        "altavoz bluetooth diseño premium",
        
        # Gaming
        "auriculares gaming inalámbricos premium",
        "teclado mecánico RGB gaming regalo",
        "mando PS5 edición especial regalo",
        "mando Xbox elite controller regalo",
        "consola retro mini regalo",
        "silla gaming ergonómica regalo",
        
        # Smart Home
        "Alexa Echo regalo",
        "Google Nest regalo",
        "bombillas inteligentes Philips Hue",
        "robot aspirador regalo",
        
        # Wearables & Audio
        "smartwatch regalo premium",
        "auriculares AirPods regalo",
        "auriculares Sony WH-1000 regalo",
        "gafas realidad virtual Meta Quest",
        
        # Cámaras & Drones
        "drone DJI Mini regalo",
        "cámara instantánea Polaroid Instax regalo",
        "webcam 4K streaming regalo",
        "gimbal estabilizador smartphone regalo",
        
        # Retro Tech
        "tocadiscos vintage regalo",
        "radio retro bluetooth regalo",
        "Game Boy clásico regalo",
    ],
    
    # =========================================================================
    # GOURMET - Foodie, Cocina, Vinos, Experiencias gastronómicas
    # =========================================================================
    "Gourmet": [
        # Kits experiencias
        "kit cata vinos regalo premium",
        "kit hacer cerveza artesanal regalo",
        "kit gin tonic premium botanicos",
        "kit cocktails regalo mixología",
        "kit sushi regalo",
        "kit especias mundo regalo",
        
        # Café & Té
        "cafetera espresso regalo premium",
        "molinillo café manual regalo",
        "set té japones regalo ceremonial",
        "AeroPress regalo café",
        
        # Vinos & Licores
        "decantador vino cristal regalo",
        "set copas vino Riedel regalo",
        "whisky premium regalo single malt",
        "ginebra premium regalo botánica",
        
        # Utensilios Chef
        "cuchillo chef japonés regalo",
        "set cuchillos damasco regalo",
        "sartén hierro fundido regalo",
        "tabla cortar madera noble regalo",
        
        # Delicatessen
        "aceite oliva premium regalo",
        "jamón ibérico bellota regalo",
        "chocolate belga regalo premium",
        "trufa negra regalo gourmet",
        
        # BBQ
        "kit BBQ regalo premium",
        "termómetro carne bluetooth regalo",
        "ahumador portátil regalo",
    ],
    
    # =========================================================================
    # ZEN - Bienestar, Spa, Meditación, Yoga (BIENESTAR en frontend)
    # =========================================================================
    "Zen": [
        # Aromaterapia
        "difusor aceites esenciales regalo",
        "vela aromática lujo regalo",
        "incienso japonés premium regalo",
        "lámpara sal himalaya regalo",
        
        # Meditación
        "cuenco tibetano regalo",
        "cojín meditación zafu regalo",
        "mala piedras naturales regalo",
        
        # Yoga
        "esterilla yoga premium regalo",
        "bloque yoga corcho regalo",
        "rueda yoga regalo",
        
        # Masaje & Relajación
        "pistola masaje regalo muscular",
        "masajeador cervical regalo",
        "rodillo jade facial regalo",
        "gua sha jade regalo",
        
        # Spa en Casa
        "albornoz algodón egipcio regalo",
        "set spa regalo premium",
        "sales baño regalo lujo",
        "bomba baño regalo set",
        
        # Sueño
        "almohada viscoelástica regalo",
        "antifaz seda dormir regalo",
        "weighted blanket manta pesada",
        "luz despertador amanecer regalo",
    ],
    
    # =========================================================================
    # DEPORTE - Fitness, Running, Outdoor (Se combina con VIAJES = AVENTURA)
    # =========================================================================
    "Deporte": [
        # Fitness
        "mancuernas ajustables regalo",
        "banda resistencia set regalo",
        "foam roller masaje regalo",
        "pistola masaje muscular regalo",
        "TRX entrenamiento suspensión regalo",
        
        # Running
        "reloj GPS running regalo Garmin",
        "auriculares deporte bluetooth regalo",
        "cinturón running hidratación regalo",
        
        # Ciclismo
        "casco ciclismo regalo",
        "luz bicicleta potente regalo",
        "ciclocomputador GPS regalo",
        
        # Outdoor
        "bastones trekking plegables regalo",
        "mochila hidratación trail regalo",
        "prismáticos compactos regalo",
        "navaja suiza victorinox regalo",
        
        # Padel & Tenis
        "raqueta padel regalo",
        "paletero padel regalo",
        
        # Recuperación
        "botas compresión recuperación regalo",
        "electroestimulador muscular regalo",
    ],
    
    # =========================================================================
    # VIAJES - Aventura, Exploradores, Camping (AVENTURA en frontend)
    # =========================================================================
    "Viajes": [
        # Equipaje
        "maleta cabina regalo premium",
        "mochila viaje 40L regalo",
        "mochila antirrobo regalo",
        "neceser viaje organizador regalo",
        
        # Comodidad Viaje
        "almohada viaje memory foam regalo",
        "antifaz viaje seda regalo",
        "adaptador universal viaje regalo",
        "powerbank 20000mah regalo",
        
        # Tech Viajero
        "kindle paperwhite regalo",
        "rastreador maleta AirTag regalo",
        "traductor instantáneo regalo",
        
        # Camping & Outdoor
        "tienda campaña ultraligera regalo",
        "saco dormir compacto regalo",
        "linterna frontal regalo",
        "filtro agua portátil regalo",
        "hamaca camping regalo",
        
        # Accesorios
        "mapa scratch viajes regalo",
        "diario viaje cuero regalo",
        "guía lonely planet regalo",
        
        # Playa
        "altavoz bluetooth impermeable regalo",
        "cámara acuática regalo",
        "gafas snorkel regalo",
    ],
    
    # =========================================================================
    # MODA - Estilo, Accesorios, Joyería (ESTILO en frontend)
    # =========================================================================
    "Moda": [
        # Relojes
        "reloj automatico regalo",
        "reloj minimalista regalo",
        "smartwatch elegante regalo",
        
        # Gafas
        "gafas sol Ray-Ban regalo",
        "gafas sol polarizadas premium regalo",
        
        # Bolsos & Carteras
        "bolso piel regalo",
        "cartera piel regalo",
        "mochila cuero regalo",
        
        # Joyería
        "collar plata 925 regalo",
        "pulsera oro regalo",
        "pendientes diseño regalo",
        "joyero organizador regalo",
        
        # Accesorios
        "cinturón piel italiano regalo",
        "corbata seda regalo",
        "fular cashmere regalo",
        "guantes piel regalo",
        
        # Calzado
        "zapatillas limited edition regalo",
        "sneakers premium regalo",
        
        # Fragancias
        "perfume nicho regalo",
        "colonia premium regalo",
        "set perfume regalo",
        
        # Hogar con estilo
        "cuadro decorativo moderno regalo",
        "lámpara diseño regalo",
        "jarrón diseño regalo",
        "kit bonsai regalo",
    ],
    
    # =========================================================================
    # FRIKI - Fandom, Coleccionismo, Anime, Comics, Juegos Mesa (FANDOM en frontend)
    # =========================================================================
    "Friki": [
        # Funko Pop
        "funko pop edición limitada regalo",
        "funko pop Star Wars regalo",
        "funko pop Marvel regalo",
        "funko pop Harry Potter regalo",
        "funko pop anime regalo",
        
        # LEGO
        "LEGO Star Wars regalo",
        "LEGO Harry Potter regalo",
        "LEGO Technic regalo",
        "LEGO Architecture regalo",
        
        # Star Wars
        "sable luz Star Wars regalo",
        "casco Star Wars réplica regalo",
        "figura Star Wars Black Series",
        
        # Marvel & DC
        "figura Marvel Legends regalo",
        "escudo Capitán América regalo",
        "casco Iron Man regalo",
        
        # Harry Potter
        "varita Harry Potter regalo oficial",
        "libro Harry Potter ilustrado regalo",
        
        # Anime & Manga
        "figura anime premium regalo",
        "figura Dragon Ball regalo",
        "figura One Piece regalo",
        "manga box set regalo",
        
        # Juegos de Mesa
        "Catan edición especial regalo",
        "juego mesa estrategia regalo",
        "Dungeons Dragons starter regalo",
        "cartas Pokemon regalo",
        
        # Gaming Merchandise
        "figura Zelda regalo",
        "figura Pokemon regalo",
        "camiseta gaming premium regalo",
        
        # Para niños (también Fandom)
        "LEGO City regalo niños",
        "LEGO Ninjago regalo",
        "Playmobil regalo",
        "juguete STEM regalo niño",
        "peluche gigante regalo",
    ],
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
    
    # =========================================================================
    # REQUISITOS DE CALIDAD PREMIUM - Solo productos top
    # =========================================================================
    "min_rating": 4.0,          # Mínimo 4.5 estrellas (ESTRICTO)
    "min_reviews": 50,          # Mínimo 50 reseñas (productos mainstream)
    "min_reviews_niche": 20,    # Mínimo 20 para productos nicho/premium
    "niche_price_threshold": 100,  # +100€ = nicho, menor requisito de reviews
    
    # Requisitos de título
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
        price = parse_price(price_str)
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
    
    # Validación de precio (using parse_price for   handling)
    price = parse_price(price_str)
    if price <= 0 or price < BLACKLIST["min_price_eur"] or price > BLACKLIST["max_price_eur"]:
        return True
    
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
    FILTRO PREMIUM: Solo productos con 4.5+ estrellas y suficientes reseñas.
    """
    # Validaciones previas
    if not datos.get("asin") or not datos.get("title"):
        logger.warning("Datos incompletos, ignorando")
        return False
    
    # =========================================================================
    # FILTRO DE CALIDAD PREMIUM - Solo productos top de Amazon
    # =========================================================================
    rating_value = datos.get("rating_value", 0.0)
    review_count = datos.get("review_count", 0)
    
    # Determinar mínimo de reviews según precio (nicho vs mainstream)
    try:
        price_float = float(datos.get("price", "0").replace(",", ".").replace("€", ""))
        min_reviews = BLACKLIST["min_reviews_niche"] if price_float >= BLACKLIST["niche_price_threshold"] else BLACKLIST["min_reviews"]
    except:
        min_reviews = BLACKLIST["min_reviews"]
    
    # FILTRO 1: Rating mínimo 4.5 estrellas
    if rating_value < BLACKLIST["min_rating"]:
        logger.debug(f"⭐ RATING BAJO ({rating_value}): {datos['title'][:40]}...")
        return False
    
    # FILTRO 2: Mínimo de reseñas
    if review_count < min_reviews:
        logger.debug(f"📊 POCAS REVIEWS ({review_count}/{min_reviews}): {datos['title'][:40]}...")
        return False
    
    logger.info(f"✅ CALIDAD OK: {rating_value}⭐ con {review_count} reviews")
    
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

# Seleccionar más vibes para máxima variedad (ahora tenemos 10 categorías)
selected_vibes = random.sample(list(SMART_SEARCHES.keys()), k=min(6, len(SMART_SEARCHES)))
logger.info(f"[VIBES] Selected: {selected_vibes}")

total_sent = 0
total_discarded = 0

try:
    for vibe in selected_vibes:
        searches = SMART_SEARCHES[vibe]
        # Seleccionar 4-5 búsquedas por vibe (antes eran 2-3)
        selected_searches = random.sample(searches, k=min(5, len(searches)))
        
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
                        
                        # Título - Múltiples selectores por si Amazon cambia
                        title = None
                        title_selectors = [
                            "h2 a span",
                            "h2 span",
                            ".a-size-medium.a-color-base.a-text-normal",
                            ".a-size-base-plus.a-color-base.a-text-normal",
                            "[data-cy='title-recipe'] h2 span",
                            ".s-title-instructions-style span",
                            "h2.a-size-mini span.a-text-normal",
                            ".a-link-normal .a-text-normal"
                        ]
                        
                        for selector in title_selectors:
                            try:
                                title_elem = item.find_element(By.CSS_SELECTOR, selector)
                                if title_elem and title_elem.text.strip():
                                    title = title_elem.text.strip()
                                    break
                            except:
                                continue
                        
                        if not title:
                            # Último recurso: usar JavaScript
                            try:
                                title = driver.execute_script("""
                                    var el = arguments[0];
                                    var h2 = el.querySelector('h2');
                                    if (h2) return h2.textContent.trim();
                                    var span = el.querySelector('.a-text-normal');
                                    if (span) return span.textContent.trim();
                                    return null;
                                """, item)
                            except:
                                pass
                        
                        if not title or len(title) < BLACKLIST["min_title_length"]:
                            continue
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
                        
                        # Rating (OBLIGATORIO para calidad)
                        rating = ""
                        rating_value = 0.0
                        try:
                            rating_el = item.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
                            rating_text = rating_el.get_attribute("innerHTML") or rating_el.text
                            rating = rating_text
                            # Extraer número: "4,7 de 5 estrellas" → 4.7
                            match = re.search(r'([0-9]+[,.]?[0-9]*)', rating_text.replace(',', '.'))
                            if match:
                                rating_value = float(match.group(1))
                        except:
                            pass
                        
                        # Número de reviews (OBLIGATORIO para calidad)
                        review_count = 0
                        try:
                            reviews_el = item.find_element(By.CSS_SELECTOR, "span.a-size-base.s-underline-text")
                            reviews_text = reviews_el.text.replace(".", "").replace(",", "")
                            review_count = int(re.sub(r'[^0-9]', '', reviews_text) or 0)
                        except:
                            try:
                                # Selector alternativo
                                reviews_el = item.find_element(By.CSS_SELECTOR, "a.a-link-normal span.a-size-base")
                                reviews_text = reviews_el.text.replace(".", "").replace(",", "")
                                review_count = int(re.sub(r'[^0-9]', '', reviews_text) or 0)
                            except:
                                pass
                        
                        # Descripción/subtítulo (optativo)
                        try:
                            description = item.find_element(By.CSS_SELECTOR, ".a-color-base.a-text-normal").text
                        except:
                            description = ""
                        
                        # Construir payload
                        if parse_price(price) > 0:
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
                                "rating_value": rating_value,
                                "review_count": review_count,
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