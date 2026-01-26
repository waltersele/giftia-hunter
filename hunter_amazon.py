#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GIFTIA HUNTER v11.0 - THE GIFTIA STANDARD
Curador IA: Ingeniero + Explorador + Hedonista

- 4 Filtros de Excelencia: Utilidad Elevada, Auto-Boicot, Originalidad, Orgullo
- Cláusula "Cheap & Chic" para <20€
- Busca GEMAS que hagan sentir inteligente y generoso a quien regala
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
from dotenv import load_dotenv

# Fix encoding para Windows (evitar crash con emojis en cp1252)
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Cargar .env
load_dotenv()

def parse_price(price_str):
    """Parse price string, handling non-breaking spaces and European formats."""
    if not price_str:
        return 0.0
    clean = str(price_str).replace('\xa0', '').replace('Ã¢â€šÂ¬', '').replace(',', '.').strip()
    clean = ''.join(c for c in clean if c.isdigit() or c == '.')
    try:
        return float(clean) if clean else 0.0
    except:
        return 0.0

GEMINI_TIMEOUT_SECONDS = 8
# Ã°Å¸â€â€˜ API KEY - Leer desde .env (NUNCA hardcodear)
GEMINI_API_KEYS = [os.getenv("GEMINI_API_KEY", "")]
_current_key_index = 0  # ÃƒÂndice de la key actual
GEMINI_MODEL = "gemini-2.0-flash"  # Modelo mÃƒÂ¡s reciente y rÃƒÂ¡pido
GEMINI_RETRY_WAIT = 60  # Segundos a esperar cuando quota excedida
GEMINI_MAX_RETRIES = 3  # MÃƒÂ¡ximo intentos antes de fallback
GEMINI_PACING_SECONDS = 10  # Ã°Å¸ÂÂ¢ PACING SEGURO: 10s entre llamadas (6 RPM, muy bajo del lÃƒÂ­mite 15 RPM)

# Ã°Å¸â€œÂ¦ COLA LOCAL - Productos pendientes de anÃƒÂ¡lisis AI
PENDING_QUEUE_FILE = "pending_products.json"
PROCESSED_LOG_FILE = "processed_products.json"

# Variable global para controlar el pacing de Gemini
_last_gemini_call = 0
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ============================================================================
# CONFIGURACIÃƒâ€œN CENTRALIZADA
# ============================================================================

# Environment-based configuration
WP_TOKEN = os.getenv("WP_API_TOKEN", "nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5")  # Fallback para desarrollo
WP_API_URL = os.getenv("WP_API_URL", "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php")
AMAZON_TAG = os.getenv("AMAZON_TAG", "GIFTIA-21")
DEBUG = os.getenv("DEBUG", "0") == "1"

# ============================================================================
# CARGAR SCHEMA CENTRALIZADO (giftia_schema.json)
# ============================================================================
# Este schema es la FUENTE ÃƒÅ¡NICA DE VERDAD para categorÃƒÂ­as, edades, gÃƒÂ©neros, etc.
# Debe coincidir con giftfinder-core/config/giftia-schema.php

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'giftia_schema.json')
GIFTIA_SCHEMA = {}

try:
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        GIFTIA_SCHEMA = json.load(f)
    print(f"Ã¢Å“â€¦ Schema cargado: {len(GIFTIA_SCHEMA.get('categories', {}))} categorÃƒÂ­as")
except FileNotFoundError:
    print(f"Ã¢Å¡Â Ã¯Â¸Â Schema no encontrado en {SCHEMA_PATH}, usando valores por defecto")
except json.JSONDecodeError as e:
    print(f"Ã¢Å¡Â Ã¯Â¸Â Error parseando schema: {e}")

# ============================================================================
# CATEGORÃƒÂAS v2.0 - Sistema de 4 Dimensiones del Avatar
# ============================================================================
# El nuevo sistema usa:
# - gf_vibe (personalidad): techie, foodie, zen, friki, aventurero, estiloso, practico
# - gf_etapa (etapa vital): bebe, peques, teen, genz, adulto, senior
# - gf_category (inventario): Tech, Gourmet, Bienestar, Gamer, etc.
# - gf_occasion (ocasiones): cumple, navidad, aniversario, etc.

if GIFTIA_SCHEMA:
    VALID_CATEGORIES = list(GIFTIA_SCHEMA.get('categories', {}).keys())
    VALID_VIBES = list(GIFTIA_SCHEMA.get('vibes', {}).keys())
    VALID_ETAPAS = list(GIFTIA_SCHEMA.get('etapas', {}).keys())
    VALID_GENDERS = list(GIFTIA_SCHEMA.get('genders', {}).keys())
else:
    # Fallback si no hay schema
    VALID_CATEGORIES = [
        "Tech", "Gourmet", "Bienestar", "Deporte", "Outdoor", "Moda", 
        "Gamer", "Hogar", "Libros", "Mascotas", "Bebidas", "Joyeria",
        "Experiencias", "Bebes", "Ninos", "Cocina", "Belleza", "Otros"
    ]
    VALID_VIBES = ["techie", "foodie", "zen", "friki", "aventurero", "estiloso", "practico"]
    VALID_ETAPAS = ["bebe", "peques", "teen", "genz", "adulto", "senior"]
    VALID_GENDERS = ["any", "male", "female"]

# Mapeo de categorÃƒÂ­as antiguas/errÃƒÂ³neas a las correctas
CATEGORY_MAPPING = {
    "Arte": "Hogar",
    "Bebe": "Bebes",
    "Juguetes": "Ninos",
    "BebÃƒÂ©": "Friki",
    "Gaming": "Gamer",
    "Wellness": "Zen",
    "Bienestar": "Zen",
    "Hogar": "DecoraciÃƒÂ³n",
    "Lectura": "Lector",
    "Libros": "Lector",
    "Cocina": "Gourmet",
    "GastronomÃƒÂ­a": "Gourmet",
    "Relax": "Zen",
    "Sport": "Deporte",
    "Aventura": "Outdoor",
    "Camping": "Outdoor",
    "Fashion": "Moda",
    "Pets": "Mascotas",
    "Photo": "FotografÃƒÂ­a",
    "Audio": "MÃƒÂºsica",
    "Fitness": "Deporte",  # Fusionar Fitness en Deporte
    "Geek": "Friki",       # Fusionar Geek en Friki
}

def validate_category(category):
    """
    Valida y normaliza una categorÃƒÂ­a.
    Si no es vÃƒÂ¡lida, intenta mapearla o retorna 'Friki' como fallback.
    """
    if not category:
        return "Friki"
    
    # Si ya es vÃƒÂ¡lida, retornar
    if category in VALID_CATEGORIES:
        return category
    
    # Intentar mapear categorÃƒÂ­a antigua/errÃƒÂ³nea
    if category in CATEGORY_MAPPING:
        return CATEGORY_MAPPING[category]
    
    # Buscar coincidencia case-insensitive
    for valid in VALID_CATEGORIES:
        if valid.lower() == category.lower():
            return valid
    
    # Fallback
    print(f"Ã¢Å¡Â Ã¯Â¸Â CategorÃƒÂ­a desconocida '{category}', usando 'Friki'")
    return "Friki"

def validate_gender(gender):
    """Valida que el gÃƒÂ©nero sea vÃƒÂ¡lido."""
    if gender in VALID_GENDERS:
        return gender
    return "unisex"

def get_category_keywords(category):
    """Obtiene las keywords de una categorÃƒÂ­a desde el schema."""
    if GIFTIA_SCHEMA and category in GIFTIA_SCHEMA.get('categories', {}):
        return GIFTIA_SCHEMA['categories'][category].get('keywords', [])
    return []

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

logger.info("[HUNTER] Ã°Å¸â€™Å½ INICIANDO v11.0 - THE GIFTIA STANDARD")
logger.info(f"[HUNTER] API Endpoint: {WP_API_URL}")
logger.info(f"[HUNTER] Gemini API: {len(GEMINI_API_KEYS)} keys configuradas (rotaciÃƒÂ³n automÃƒÂ¡tica)")
logger.info(f"[HUNTER] Ã°Å¸ÂÂ¢ Pacing: {GEMINI_PACING_SECONDS}s entre llamadas (6 RPM seguro)")
logger.info(f"[HUNTER] Debug Mode: {'ENABLED' if DEBUG else 'DISABLED'}")

# ============================================================================
# Ã°Å¸â€œÂ¦ SISTEMA DE COLA LOCAL - Productos pendientes de anÃƒÂ¡lisis AI
# ============================================================================

def load_pending_queue():
    """Carga productos pendientes de anÃƒÂ¡lisis."""
    try:
        if os.path.exists(PENDING_QUEUE_FILE):
            with open(PENDING_QUEUE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Error cargando cola: {e}")
    return []

def save_pending_queue(queue):
    """Guarda la cola de productos pendientes."""
    try:
        with open(PENDING_QUEUE_FILE, 'w', encoding='utf-8') as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error guardando cola: {e}")

def add_to_pending_queue(product):
    """AÃƒÂ±ade un producto a la cola de pendientes."""
    queue = load_pending_queue()
    # Evitar duplicados por ASIN
    if not any(p.get('asin') == product.get('asin') for p in queue):
        product['queued_at'] = datetime.now().isoformat()
        queue.append(product)
        save_pending_queue(queue)
        logger.info(f"Ã°Å¸â€œÂ¦ EN COLA [{len(queue)}]: {product.get('title', '')[:40]}...")
        return True
    return False

def get_pending_count():
    """Retorna cuÃƒÂ¡ntos productos hay en cola."""
    return len(load_pending_queue())

def log_processed_product(product, result):
    """Registra producto procesado (para anÃƒÂ¡lisis posterior)."""
    try:
        processed = []
        if os.path.exists(PROCESSED_LOG_FILE):
            with open(PROCESSED_LOG_FILE, 'r', encoding='utf-8') as f:
                processed = json.load(f)
        
        product['processed_at'] = datetime.now().isoformat()
        product['ai_result'] = result
        processed.append(product)
        
        # Mantener solo ÃƒÂºltimos 500 para no crecer infinito
        if len(processed) > 500:
            processed = processed[-500:]
        
        with open(PROCESSED_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(processed, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Error logging processed: {e}")

def get_next_from_queue():
    """Obtiene el siguiente producto de la cola (FIFO)."""
    queue = load_pending_queue()
    if queue:
        product = queue.pop(0)
        save_pending_queue(queue)
        return product
    return None

def remove_from_queue(asin):
    """Elimina un producto de la cola por ASIN."""
    queue = load_pending_queue()
    queue = [p for p in queue if p.get('asin') != asin]
    save_pending_queue(queue)

# Variable global para modo cola
QUEUE_MODE = os.getenv("QUEUE_MODE", "queue").lower()  # 'queue', 'direct', 'hybrid'
# hybrid = scrapea y aÃƒÂ±ade a cola, procesa cola al final
# queue = solo procesa cola existente
# direct = comportamiento anterior (Gemini inline)

# ============================================================================
# BÃƒÅ¡SQUEDAS POR CATEGORÃƒÂA - SIMPLIFICADO (6 VIBES + DIGITAL)
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
        "suscripciÃƒÂ³n Audible regalo",
        "suscripciÃƒÂ³n Kindle Unlimited regalo",
        "suscripciÃƒÂ³n Amazon Prime regalo",
        "suscripciÃƒÂ³n Disney Plus regalo",
        "suscripciÃƒÂ³n HBO Max regalo",
        
        # Cursos y FormaciÃƒÂ³n
        "curso online Masterclass regalo",
        "curso Udemy regalo",
        "curso Domestika regalo",
        
        # Software & Licencias
        "Microsoft Office 365 cÃƒÂ³digo regalo",
        "licencia software regalo",
        
        # eBooks
        "ebook kindle bestseller regalo",
        "kindle ebook regalo",
    ],
    
    # =========================================================================
    # EXPERIENCIAS - Viajes, Entradas, Smartbox (entrega instantÃƒÂ¡nea/voucher)
    # =========================================================================
    "Experiencias": [
        # Smartbox & Cajas Experiencia
        "Smartbox escapada romÃƒÂ¡ntica regalo",
        "Smartbox spa bienestar regalo",
        "Smartbox aventura regalo",
        "Smartbox cena gourmet regalo",
        "Wonderbox escapada regalo",
        "Wonderbox spa masaje regalo",
        "caja experiencia regalo",
        "Cofre Dakotabox regalo",
        
        # Entradas EspectÃƒÂ¡culos
        "entrada musical regalo",
        "entrada teatro regalo",
        "entrada concierto regalo",
        "entrada ÃƒÂ³pera regalo",
        "entrada circo del sol regalo",
        
        # Experiencias Aventura
        "salto paracaÃƒÂ­das experiencia regalo",
        "vuelo globo aerostÃƒÂ¡tico regalo",
        "conducir Ferrari experiencia regalo",
        "conducir Lamborghini experiencia regalo",
        "experiencia karting regalo",
        "vuelo helicÃƒÂ³ptero experiencia regalo",
        "bautismo buceo experiencia regalo",
        "experiencia surf regalo",
        
        # Experiencias GastronÃƒÂ³micas
        "cena ciegas experiencia regalo",
        "cata vinos experiencia regalo",
        "curso cocina experiencia regalo",
        "experiencia escape room regalo",
        
        # Spa & Bienestar
        "circuito spa regalo",
        "masaje relajante experiencia regalo",
        "dÃƒÂ­a spa pareja regalo",
        
        # Viajes Experiencia
        "escapada rural regalo",
        "noche hotel regalo",
        "viaje sorpresa regalo",
    ],
    
    # =========================================================================
    # TECH & GAMING - Gadgets, Consolas, Smart Home
    # =========================================================================
    "Tech": [
        # Gadgets originales
        "gadgets tecnologicos regalo original",
        "mini proyector portatil regalo",
        "cargador inalÃƒÂ¡mbrico diseÃƒÂ±o premium",
        "lÃƒÂ¡mpara LED inteligente RGB WiFi",
        "marco digital fotos WiFi regalo",
        "altavoz bluetooth diseÃƒÂ±o premium",
        
        # Gaming
        "auriculares gaming inalÃƒÂ¡mbricos premium",
        "teclado mecÃƒÂ¡nico RGB gaming regalo",
        "mando PS5 ediciÃƒÂ³n especial regalo",
        "mando Xbox elite controller regalo",
        "consola retro mini regalo",
        "silla gaming ergonÃƒÂ³mica regalo",
        
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
        
        # CÃƒÂ¡maras & Drones
        "drone DJI Mini regalo",
        "cÃƒÂ¡mara instantÃƒÂ¡nea Polaroid Instax regalo",
        "webcam 4K streaming regalo",
        "gimbal estabilizador smartphone regalo",
        
        # Retro Tech
        "tocadiscos vintage regalo",
        "radio retro bluetooth regalo",
        "Game Boy clÃƒÂ¡sico regalo",
    ],
    
    # =========================================================================
    # GOURMET - Foodie, Cocina, Vinos, Experiencias gastronÃƒÂ³micas
    # =========================================================================
    "Gourmet": [
        # Kits experiencias
        "kit cata vinos regalo premium",
        "kit hacer cerveza artesanal regalo",
        "kit gin tonic premium botanicos",
        "kit cocktails regalo mixologÃƒÂ­a",
        "kit sushi regalo",
        "kit especias mundo regalo",
        
        # CafÃƒÂ© & TÃƒÂ©
        "cafetera espresso regalo premium",
        "molinillo cafÃƒÂ© manual regalo",
        "set tÃƒÂ© japones regalo ceremonial",
        "AeroPress regalo cafÃƒÂ©",
        
        # Vinos & Licores
        "decantador vino cristal regalo",
        "set copas vino Riedel regalo",
        "whisky premium regalo single malt",
        "ginebra premium regalo botÃƒÂ¡nica",
        
        # Utensilios Chef
        "cuchillo chef japonÃƒÂ©s regalo",
        "set cuchillos damasco regalo",
        "sartÃƒÂ©n hierro fundido regalo",
        "tabla cortar madera noble regalo",
        
        # Delicatessen
        "aceite oliva premium regalo",
        "jamÃƒÂ³n ibÃƒÂ©rico bellota regalo",
        "chocolate belga regalo premium",
        "trufa negra regalo gourmet",
        
        # BBQ
        "kit BBQ regalo premium",
        "termÃƒÂ³metro carne bluetooth regalo",
        "ahumador portÃƒÂ¡til regalo",
    ],
    
    # =========================================================================
    # ZEN - Bienestar, Spa, MeditaciÃƒÂ³n, Yoga (BIENESTAR en frontend)
    # =========================================================================
    "Zen": [
        # Aromaterapia
        "difusor aceites esenciales regalo",
        "vela aromÃƒÂ¡tica lujo regalo",
        "incienso japonÃƒÂ©s premium regalo",
        "lÃƒÂ¡mpara sal himalaya regalo",
        
        # MeditaciÃƒÂ³n
        "cuenco tibetano regalo",
        "cojÃƒÂ­n meditaciÃƒÂ³n zafu regalo",
        "mala piedras naturales regalo",
        
        # Yoga
        "esterilla yoga premium regalo",
        "bloque yoga corcho regalo",
        "rueda yoga regalo",
        
        # Masaje & RelajaciÃƒÂ³n
        "pistola masaje regalo muscular",
        "masajeador cervical regalo",
        "rodillo jade facial regalo",
        "gua sha jade regalo",
        
        # Spa en Casa
        "albornoz algodÃƒÂ³n egipcio regalo",
        "set spa regalo premium",
        "sales baÃƒÂ±o regalo lujo",
        "bomba baÃƒÂ±o regalo set",
        
        # SueÃƒÂ±o
        "almohada viscoelÃƒÂ¡stica regalo",
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
        "TRX entrenamiento suspensiÃƒÂ³n regalo",
        
        # Running
        "reloj GPS running regalo Garmin",
        "auriculares deporte bluetooth regalo",
        "cinturÃƒÂ³n running hidrataciÃƒÂ³n regalo",
        
        # Ciclismo
        "casco ciclismo regalo",
        "luz bicicleta potente regalo",
        "ciclocomputador GPS regalo",
        
        # Outdoor
        "bastones trekking plegables regalo",
        "mochila hidrataciÃƒÂ³n trail regalo",
        "prismÃƒÂ¡ticos compactos regalo",
        "navaja suiza victorinox regalo",
        
        # Padel & Tenis
        "raqueta padel regalo",
        "paletero padel regalo",
        
        # RecuperaciÃƒÂ³n
        "botas compresiÃƒÂ³n recuperaciÃƒÂ³n regalo",
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
        "traductor instantÃƒÂ¡neo regalo",
        
        # Camping & Outdoor
        "tienda campaÃƒÂ±a ultraligera regalo",
        "saco dormir compacto regalo",
        "linterna frontal regalo",
        "filtro agua portÃƒÂ¡til regalo",
        "hamaca camping regalo",
        
        # Accesorios
        "mapa scratch viajes regalo",
        "diario viaje cuero regalo",
        "guÃƒÂ­a lonely planet regalo",
        
        # Playa
        "altavoz bluetooth impermeable regalo",
        "cÃƒÂ¡mara acuÃƒÂ¡tica regalo",
        "gafas snorkel regalo",
    ],
    
    # =========================================================================
    # MODA - Estilo, Accesorios, JoyerÃƒÂ­a (ESTILO en frontend)
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
        
        # JoyerÃƒÂ­a
        "collar plata 925 regalo",
        "pulsera oro regalo",
        "pendientes diseÃƒÂ±o regalo",
        "joyero organizador regalo",
        
        # Accesorios
        "cinturÃƒÂ³n piel italiano regalo",
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
        "lÃƒÂ¡mpara diseÃƒÂ±o regalo",
        "jarrÃƒÂ³n diseÃƒÂ±o regalo",
        "kit bonsai regalo",
    ],
    
    # =========================================================================
    # FRIKI - Fandom, Coleccionismo, Anime, Comics, Juegos Mesa (FANDOM en frontend)
    # =========================================================================
    "Friki": [
        # Funko Pop
        "funko pop ediciÃƒÂ³n limitada regalo",
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
        "casco Star Wars rÃƒÂ©plica regalo",
        "figura Star Wars Black Series",
        
        # Marvel & DC
        "figura Marvel Legends regalo",
        "escudo CapitÃƒÂ¡n AmÃƒÂ©rica regalo",
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
        "Catan ediciÃƒÂ³n especial regalo",
        "juego mesa estrategia regalo",
        "Dungeons Dragons starter regalo",
        "cartas Pokemon regalo",
        
        # Gaming Merchandise
        "figura Zelda regalo",
        "figura Pokemon regalo",
        "camiseta gaming premium regalo",
        
        # Para niÃƒÂ±os (tambiÃƒÂ©n Fandom)
        "LEGO City regalo niÃƒÂ±os",
        "LEGO Ninjago regalo",
        "Playmobil regalo",
        "juguete STEM regalo niÃƒÂ±o",
        "peluche gigante regalo",
    ],
    
    # =========================================================================
    # BEBÃƒâ€° - Productos para reciÃƒÂ©n nacidos y bebÃƒÂ©s (0-2 aÃƒÂ±os)
    # Sets regalo de marcas premium que Gemini deberÃƒÂ­a ACEPTAR
    # =========================================================================
    "Bebe": [
        # MARCAS PREMIUM - Sets regalo (Gemini deberÃƒÂ­a aceptar estos)
        "Philips Avent set regalo",
        "Suavinex set regalo bebe",
        "Chicco set regalo",
        "NUK set regalo bebe",
        "Tommee Tippee set regalo",
        "Mustela set regalo bebe",
        "set bienvenida bebe premium",
        
        # Carricoches y transporte
        "cochecito bebe regalo",
        "silla paseo bebe regalo",
        "mochila portabebÃƒÂ©s ergonÃƒÂ³mica regalo",
        "capazo bebe regalo",
        "silla coche bebe grupo 0 regalo",
        
        # Cestas y sets regalo
        "canastilla bebe regalo",
        "cesta regalo reciÃƒÂ©n nacido",
        "set regalo bebe",
        "caja regalo nacimiento",
        "kit bienvenida bebe regalo",
        
        # Ropa bebÃƒÂ©
        "ropa bebe regalo set",
        "bodies bebe pack regalo",
        "pijama bebe regalo",
        "conjunto bebe regalo",
        "vestido bebe regalo",
        "pelele bebe regalo",
        "gorro bebe regalo",
        "patucos bebe regalo",
        
        # BaÃƒÂ±o bebÃƒÂ©
        "baÃƒÂ±era bebe regalo",
        "set baÃƒÂ±o bebe regalo",
        "toalla bebe capucha regalo",
        "capa baÃƒÂ±o bebe regalo",
        "termÃƒÂ³metro baÃƒÂ±o bebe regalo",
        "patitos baÃƒÂ±o bebe regalo",
        
        # AlimentaciÃƒÂ³n
        "set biberones regalo",
        "robot cocina bebe regalo",
        "trona bebe regalo",
        "baberos regalo set",
        "vajilla bebe regalo",
        "cuchara silicona bebe set",
        
        # SueÃƒÂ±o y descanso
        "cuna bebe regalo",
        "minicuna regalo",
        "mÃƒÂ³vil cuna musical regalo",
        "proyector estrellas bebe regalo",
        "luz nocturna bebe regalo",
        "saco dormir bebe regalo",
        "doudou bebe regalo",
        "mantita bebe regalo",
        
        # Juguetes bebÃƒÂ© (0-2 aÃƒÂ±os)
        "sonajero bebe regalo",
        "mordedor bebe regalo",
        "gimnasio bebe regalo",
        "alfombra actividades bebe regalo",
        "juguete sensorial bebe regalo",
        "peluche bebe regalo",
        "libro tela bebe regalo",
        "cubos apilables bebe regalo",
        
        # Recuerdos y especiales
        "huella bebe regalo",
        "marco foto bebe regalo",
        "ÃƒÂ¡lbum bebe regalo",
        "caja recuerdos bebe regalo",
        "joyero primer diente regalo",
        
        # Seguridad y cuidado
        "vigilabebÃƒÂ©s cÃƒÂ¡mara regalo",
        "esterilizador biberones regalo",
        "cambiador bebe regalo",
        "bolsa paÃƒÂ±ales regalo",
        "neceser bebe regalo",
    ],
    
    # =========================================================================
    # ARTE - Materiales artÃƒÂ­sticos, manualidades, creatividad (NUEVO)
    # =========================================================================
    "Arte": [
        # Pintura & Dibujo
        "set acuarelas profesional regalo",
        "set ÃƒÂ³leos artista regalo",
        "set lÃƒÂ¡pices colores profesional regalo Faber Castell",
        "set rotuladores lettering regalo",
        "caballete pintura regalo",
        "lienzos artista set regalo",
        "paleta pintura madera regalo",
        "set pinceles profesional regalo",
        
        # Dibujo TÃƒÂ©cnico & DiseÃƒÂ±o
        "tableta grÃƒÂ¡fica dibujo regalo",
        "Wacom regalo artista",
        "set copic markers regalo",
        "set prismacolor regalo",
        "cuaderno sketch premium regalo",
        "bloc dibujo artista regalo",
        
        # Manualidades & Craft
        "kit scrapbooking regalo",
        "set arcilla polimerica regalo",
        "kit costura creativa regalo",
        "mÃƒÂ¡quina coser regalo principiante",
        "kit bordado regalo",
        "kit macramÃƒÂ© regalo",
        "kit punch needle regalo",
        "kit resina epoxi regalo",
        
        # NiÃƒÂ±os creativos
        "set arte niÃƒÂ±os regalo premium",
        "maletÃƒÂ­n pintura niÃƒÂ±os regalo",
        "kit manualidades niÃƒÂ±os regalo",
        "set plastilina Play-Doh regalo",
        "caballete niÃƒÂ±os regalo",
        "set acuarelas niÃƒÂ±os regalo",
        "kit origami niÃƒÂ±os regalo",
        "ceras Manley set regalo",
        
        # CaligrafÃƒÂ­a & Lettering
        "set caligrafÃƒÂ­a regalo",
        "plumas caligrafÃƒÂ­a regalo",
        "kit lettering principiante regalo",
        "brush pens tombow regalo",
        
        # Escultura & 3D
        "kit escultura regalo",
        "set herramientas modelado regalo",
        "impresora 3D regalo",
        "kit modelismo regalo",
    ],
}

# ============================================================================
# Ã°Å¸Â§Â  CEREBRO SEMÃƒÂNTICO v9.0 - Filtrado Contextual Inteligente
# ============================================================================

# REGLAS DE CONTEXTO: Palabras "peligrosas" que dependen del contexto
# Si "baterÃƒÂ­a" + "coche" = BASURA, pero "baterÃƒÂ­a" + "musical" = JOYITA
CONTEXT_RULES = {
    "bateria": {
        "bad_context": ["coche", "moto", "12v", "24v", "recambio", "repuesto", "arranque", "cr2032", "aa", "aaa", "lr44"],
        "good_context": ["externa", "musical", "portatil", "powerbank", "instrumento", "ebike", "patinete", "magsafe", "electronica"]
    },
    "filtro": {
        "bad_context": ["aire", "aceite", "coche", "motor", "aspiradora", "campana", "agua", "recambio", "hepa"],
        "good_context": ["instagram", "lente", "fotografia", "camara", "privacidad", "nd", "polarizador"]
    },
    "papel": {
        "bad_context": ["higienico", "cocina", "aluminio", "horno", "film", "wc", "limpieza", "lijadora", "lija"],
        "good_context": ["regalo", "fotografico", "polaroid", "instax", "pintar", "acuarela", "scrapbooking", "origami"]
    },
    "cable": {
        "bad_context": ["red", "bobina", "electrico", "instalacion", "tierra", "antena", "metros", "rollo"],
        "good_context": ["organizador", "luminoso", "rgb", "diseÃƒÂ±o", "gaming", "trenzado", "premium"]
    },
    "funda": {
        "bad_context": ["almohada", "sofa", "silla", "coche", "asiento", "tabla", "planchar", "nordica", "colchon"],
        "good_context": ["nintendo", "switch", "steam deck", "kindle", "diseÃƒÂ±o", "cuero", "airpods", "premium"]
    },
    "cargador": {
        "bad_context": ["pilas", "recambio", "coche", "bateria coche", "arrancador"],
        "good_context": ["inalambrico", "magsafe", "rapido", "diseÃƒÂ±o", "premium", "qi", "wireless"]
    },
    "soporte": {
        "bad_context": ["tv", "pared", "bicicleta", "herramientas", "estanteria", "monitor"],
        "good_context": ["gaming", "rgb", "auriculares", "diseÃƒÂ±o", "madera", "premium"]
    }
}

# PALABRAS DE ORO - Aumentan drÃƒÂ¡sticamente el Gift Score
GOLDEN_KEYWORDS = [
    "edicion limitada", "coleccionista", "oficial", "premium", "deluxe",
    "caja regalo", "kit regalo", "set regalo", "madera noble", "cuero autentico",
    "hecho a mano", "artesanal", "diseÃƒÂ±o original", "gadget", "novedad",
    "bestseller", "viral", "tiktok", "juego mesa", "lego", "funko",
    "ediciÃƒÂ³n especial", "exclusivo", "handmade", "luxury", "signature"
]

# KILLER KEYWORDS - Muerte sÃƒÂºbita, nadie quiere esto como regalo
KILLER_KEYWORDS = [
    # Consumibles/Repuestos
    "recambio", "repuesto", "pack de 10", "pack de 20", "pack de 50",
    "pack de 100", "100 unidades", "50 unidades", "tornillos", "tuercas",
    "recarga", "refill", "cartucho recambio",
    
    # GRANEL - TamaÃƒÂ±os gigantes no regalo
    "garrafa", "5 litros", "5l", "10 litros", "10l", "20 litros", "25 litros",
    "5kg", "10kg", "25kg", "bulk", "industrial", "hosteleria", "profesional 5l",
    
    # Limpieza/Hogar aburrido
    "fregona", "lejia", "detergente", "suavizante", "pastillas lavavajillas",
    "insecticida", "raticida", "abono", "tierra maceta", "cemento", "masilla",
    "silicona sellador", "junta fontaneria", "desatascador", "estropajo",
    "bayeta", "cubo fregona", "escoba", "recogedor",
    
    # Industrial/FontanerÃƒÂ­a
    "fontaneria", "tuberia", "pvc", "manguera", "grifo", "valvula",
    "junta torica", "arandela", "codo pvc",
    
    # BebÃƒÂ© CONSUMIBLES (solo los claramente utilitarios)
    "paÃƒÂ±ales", "paÃƒÂ±al", "toallitas humedas", 
    "leche formula", "leche infantil", "potito", "papilla",
    "tetina recambio",
    
    # AlimentaciÃƒÂ³n bÃƒÂ¡sica
    "arroz 5kg", "arroz 10kg", "aceite girasol", "aceite oliva 5l",
    "sal 1kg", "azucar 1kg", "harina 5kg",
    
    # Tarjetas Amazon (genÃƒÂ©ricas)
    "tarjeta regalo amazon", "tarjeta regalo electronica", "tarjeta de felicitacion",
    
    # Ropa interior bÃƒÂ¡sica
    "pack calzoncillos", "pack bragas", "pack calcetines basicos",
    "slip hombre pack", "boxer pack 10",
    
    # Oficina/Escolar aburrido
    "pack folios", "folios 500", "grapadora industrial", "archivador",
    "carpeta", "post-it", "clips", "chinchetas"
]

# ============================================================================
# Ã°Å¸Å½Â¯ SISTEMA DE GÃƒâ€°NERO/DEMOGRAFÃƒÂA - DetecciÃƒÂ³n inteligente de target
# ============================================================================

# Indicadores de producto FEMENINO
FEMALE_INDICATORS = {
    # Colores tÃƒÂ­picamente femeninos
    "colors": ["rosa", "pink", "fucsia", "lavanda", "lila", "coral", "malva", "violeta"],
    # Palabras clave femeninas
    "keywords": [
        "mujer", "woman", "women", "girl", "chica", "dama", "femenino", "feminine",
        "ella", "her", "ladies", "seÃƒÂ±ora", "mamÃƒÂ¡", "madre", "novia", "esposa",
        "manicura", "pedicura", "maquillaje", "makeup", "labial", "rimel", "mascara",
        "bolso mujer", "vestido", "falda", "sujetador", "braga", "lenceria",
        "depiladora", "plancha pelo", "secador pelo", "rizador",
        "bomba baÃƒÂ±o", "sales baÃƒÂ±o rosa", "spa mujer", "beauty", "belleza",
        "joyeria mujer", "pendientes", "pulsera mujer", "collar mujer"
    ],
    # Productos tÃƒÂ­picamente femeninos (aunque no digan "mujer")
    "products": [
        "bombas de baÃƒÂ±o", "bath bomb", "set maquillaje", "paleta sombras",
        "neceser maquillaje", "espejo maquillaje", "brochas maquillaje",
        "set manicura", "esmalte uÃƒÂ±as", "gel uÃƒÂ±as", "lampara uÃƒÂ±as"
    ]
}

# Indicadores de producto MASCULINO
MALE_INDICATORS = {
    # Colores tÃƒÂ­picamente masculinos (solos no determinan, pero ayudan)
    "colors": [],  # Los colores masculinos son mÃƒÂ¡s neutros
    # Palabras clave masculinas
    "keywords": [
        "hombre", "man", "men", "boy", "chico", "caballero", "masculino", "masculine",
        "ÃƒÂ©l", "him", "his", "papÃƒÂ¡", "padre", "novio", "esposo", "marido",
        "barba", "beard", "afeitado", "shaving", "afeitadora", "maquinilla",
        "corbata", "gemelos", "tirantes hombre", "cinturon hombre",
        "locion after shave", "colonia hombre", "perfume hombre"
    ],
    # Productos tÃƒÂ­picamente masculinos
    "products": [
        "set afeitado", "brocha afeitar", "navaja afeitar", "aceite barba",
        "recortadora barba", "kit barba", "cera bigote", "peine barba"
    ]
}

# Indicadores de producto INFANTIL
KIDS_INDICATORS = {
    "keywords": [
        "niÃƒÂ±o", "niÃƒÂ±a", "kids", "children", "infantil", "child", "baby", "bebÃƒÂ©",
        "junior", "peque", "pequeÃƒÂ±o", "pequeÃƒÂ±a", "escolar", "colegio",
        "juguete", "toy", "toys", "peluche", "muÃƒÂ±eco", "muÃƒÂ±eca",
        "reciÃƒÂ©n nacido", "recien nacido", "newborn", "bebe", "lactante"
    ],
    "products": [
        "juego educativo", "puzzle niÃƒÂ±os", "lego duplo", "playmobil",
        "cuentos infantiles", "libro colorear", "plastilina", "crayones",
        "cochecito", "carricoche", "canastilla", "biberÃƒÂ³n", "chupete",
        "sonajero", "mordedor", "cuna", "minicuna", "trona", "portabebÃƒÂ©s"
    ]
}

# Productos SOLO para adultos - NUNCA mostrar a niÃƒÂ±os/bebÃƒÂ©s
ADULT_ONLY_PRODUCTS = [
    "antifaz", "antifaz seda", "antifaz dormir",
    "vino", "whisky", "ginebra", "cerveza", "licor", "champagne",
    "cuchillo", "navaja", "machete",
    "perfume", "colonia", "eau de parfum",
    "cafetera", "espresso", "nespresso",
    "sacacorchos", "decantador",
    "rasuradora", "afeitadora", "depiladora",
    "pistola masaje", "masajeador",
    "manta elÃƒÂ©ctrica", "almohadilla elÃƒÂ©ctrica",
    "plancha pelo", "secador pelo", "rizador",
]

# ============================================================================
# Ã°Å¸â€â€ž SISTEMA DE DEDUPLICACIÃƒâ€œN - Evitar productos repetidos/similares
# ============================================================================

# Cache de productos enviados en esta sesiÃƒÂ³n (para evitar duplicados)
SENT_PRODUCTS_CACHE = set()  # ASINs enviados
SENT_CATEGORIES_CACHE = {}   # {"auriculares traductores": 1, "smartwatch": 2, ...}
MAX_PER_CATEGORY = 5         # MÃƒÂ¡ximo 5 productos por categorÃƒÂ­a similar

# Palabras clave para categorizar productos (detectar similares)
PRODUCT_CATEGORIES = [
    # Tech
    "auriculares", "cascos", "headphones", "earbuds", "airpods",
    "smartwatch", "reloj inteligente", "fitness tracker",
    "altavoz", "speaker", "bluetooth speaker",
    "cargador inalambrico", "wireless charger",
    "powerbank", "bateria externa",
    "traductor", "translator",
    "drone", "dron",
    "camara instantanea", "polaroid", "instax",
    "proyector", "projector",
    "teclado", "keyboard",
    "raton", "mouse",
    "webcam",
    
    # Gaming
    "mando ps5", "mando xbox", "controller",
    "silla gaming",
    "funko pop",
    "figura coleccion",
    
    # Gourmet
    "cafetera", "coffee maker",
    "molinillo cafe",
    "set cuchillos", "cuchillo chef",
    "decantador",
    "whisky", "ginebra", "gin",
    
    # Deporte
    "mancuernas", "pesas",
    "esterilla yoga", "yoga mat",
    "pistola masaje",
    "reloj gps", "garmin",
    "raqueta padel",
    
    # Moda
    "gafas sol", "sunglasses",
    "cartera", "billetera", "wallet",
    "bolso", "bag",
    "perfume", "colonia", "fragancia",
    "reloj automatico", "reloj mecanico",
    
    # Zen
    "difusor", "humidificador",
    "vela aromatica",
    "cuenco tibetano",
    "lampara sal",
]

def get_product_category(title):
    """
    Detecta la categorÃƒÂ­a del producto para evitar duplicados.
    Retorna la categorÃƒÂ­a o None si no encuentra match.
    """
    title_lower = title.lower()
    for category in PRODUCT_CATEGORIES:
        if category in title_lower:
            return category
    return None

def is_duplicate_category(title):
    """
    Verifica si ya enviamos demasiados productos de esta categorÃƒÂ­a.
    """
    category = get_product_category(title)
    if not category:
        return False  # Sin categorÃƒÂ­a = permitir
    
    current_count = SENT_CATEGORIES_CACHE.get(category, 0)
    return current_count >= MAX_PER_CATEGORY

def register_sent_product(asin, title):
    """
    Registra un producto enviado para evitar duplicados futuros.
    """
    SENT_PRODUCTS_CACHE.add(asin)
    category = get_product_category(title)
    if category:
        SENT_CATEGORIES_CACHE[category] = SENT_CATEGORIES_CACHE.get(category, 0) + 1
        logger.debug(f"Ã°Å¸â€œÂ¦ CategorÃƒÂ­a '{category}': {SENT_CATEGORIES_CACHE[category]}/{MAX_PER_CATEGORY}")

def detect_target_gender(title, description=""):
    """
    Detecta el gÃƒÂ©nero/demografÃƒÂ­a objetivo del producto.
    Retorna: 'female', 'male', 'kids', o 'unisex'
    """
    text = (title + " " + description).lower()
    
    female_score = 0
    male_score = 0
    kids_score = 0
    
    # Detectar FEMENINO
    for color in FEMALE_INDICATORS["colors"]:
        if color in text:
            female_score += 2
    for kw in FEMALE_INDICATORS["keywords"]:
        if kw in text:
            female_score += 3
    for prod in FEMALE_INDICATORS["products"]:
        if prod in text:
            female_score += 5
    
    # Detectar MASCULINO
    for kw in MALE_INDICATORS["keywords"]:
        if kw in text:
            male_score += 3
    for prod in MALE_INDICATORS["products"]:
        if prod in text:
            male_score += 5
    
    # Detectar INFANTIL
    for kw in KIDS_INDICATORS["keywords"]:
        if kw in text:
            kids_score += 3
    for prod in KIDS_INDICATORS["products"]:
        if prod in text:
            kids_score += 5
    
    # Ã¢Å¡Â Ã¯Â¸Â PenalizaciÃƒÂ³n: Productos de adultos NUNCA son para niÃƒÂ±os
    for adult_product in ADULT_ONLY_PRODUCTS:
        if adult_product in text:
            kids_score = 0  # Reset - no es para niÃƒÂ±os
            break
    
    # Determinar ganador
    if kids_score >= 3:
        return "kids"
    if female_score >= 3 and female_score > male_score:
        return "female"
    if male_score >= 3 and male_score > female_score:
        return "male"
    
    return "unisex"

# ============================================================================
# Ã°Å¸Â§Â  GEMINI JUDGE - El Juez AI para clasificaciÃƒÂ³n inteligente
# ============================================================================

def ask_gemini_judge(title, price, category_hint="", already_sent_categories=None):
    """
    Consulta a Gemini para clasificar el producto de forma inteligente.
    Con retry automÃƒÂ¡tico cuando se excede la quota (429).
    
    Retorna un dict con:
    - is_good_gift: bool
    - target_gender: 'male', 'female', 'any'
    - category: categorÃƒÂ­a de gf_category (inventario WordPress)
    - vibes: lista de vibes de personalidad (gf_vibe)
    - reasoning: explicaciÃƒÂ³n breve
    - is_duplicate: bool (si ya tenemos algo muy similar)
    """
    if not GEMINI_API_KEYS or len(GEMINI_API_KEYS) == 0:
        # Sin API keys, usar fallback al sistema anterior
        logger.debug("Ã¢Å¡Â Ã¯Â¸Â Gemini no configurado, usando fallback regex")
        return None
    
    # Construir contexto de productos ya enviados
    sent_context = ""
    if already_sent_categories:
        sent_items = [f"{cat}: {count}" for cat, count in already_sent_categories.items() if count > 0]
        if sent_items:
            sent_context = f"Ya tengo en mi lista: {', '.join(sent_items[:10])}."
    
    # Usar la constante global VALID_CATEGORIES
    # Edades y ocasiones del schema (fuente ÃƒÂºnica de verdad)
    valid_ages = list(GIFTIA_SCHEMA.get('ages', {}).keys()) if GIFTIA_SCHEMA else ["nino", "teen", "joven", "adulto", "senior", "mayor"]
    valid_occasions = list(GIFTIA_SCHEMA.get('occasions', {}).keys()) if GIFTIA_SCHEMA else ["cumple", "navidad", "amigoinvisible", "sanvalentin", "aniversario", "diaMadre", "graduacion", "boda", "gracias", "random"]
    valid_genders = list(GIFTIA_SCHEMA.get('genders', {}).keys()) if GIFTIA_SCHEMA else ["unisex", "male", "female", "kids"]
    
    prompt = f"""Eres el CURADOR PRINCIPAL de "Giftia". Tu criterio combina:
Ã°Å¸â€Â§ INGENIERO (utilidad y calidad) + Ã°Å¸Â§Â­ EXPLORADOR (originalidad) + Ã°Å¸ÂÂ· HEDONISTA (placer)

Tu misiÃƒÂ³n: Filtrar la basura del e-commerce para encontrar "GEMAS" que hagan sentir INTELIGENTE y GENEROSO a quien regala.

PRODUCTO: {title}
PRECIO: {price} EUR
{sent_context}

Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
Ã°Å¸â€™Å½ THE GIFTIA STANDARD - MATRIZ DE DECISIÃƒâ€œN
Para APROBAR, debe superar AL MENOS UNO de estos 4 filtros.
Si es "del montÃƒÂ³n" o "hacer la compra" Ã¢â€ â€™ RECHAZAR sin piedad.
Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

Ã°Å¸â€Â§ FILTRO 1: UTILIDAD ELEVADA (Best in Class)
"Ã‚Â¿Es la MEJOR versiÃƒÂ³n posible de esa utilidad?"
Ã¢ÂÅ’ Tupper plÃƒÂ¡stico supermercado, paraguas endeble, bolÃƒÂ­grafo publicidad, cable genÃƒÂ©rico
Ã¢Å“â€¦ Bento Box hermÃƒÂ©tico diseÃƒÂ±o (Monbento), Paraguas fibra vidrio, BolÃƒÂ­grafo latÃƒÂ³n, Cable trenzado premium
CRITERIO: "Ã‚Â¿Es consumible que se tira o herramienta que se cuida?"

Ã°Å¸Å½Â FILTRO 2: AUTO-BOICOT (The Indulgence Gap)
"Ã‚Â¿Es algo que QUIEREN pero les da 'dolor' comprarse?"
Ã¢ÂÅ’ Calcetines bÃƒÂ¡sicos, tinta impresora, bombillas, gel ducha familiar
Ã¢Å“â€¦ Calcetines Lana Merino/Happy Socks, Vela AromÃƒÂ¡tica Premium, Aceite Trufa, JabÃƒÂ³n Aesop/Rituals
CRITERIO: "Ã‚Â¿Lo comprarÃƒÂ­a un martes cualquiera? SÃƒÂÃ¢â€ â€™Rechazar. Es 'capricho'Ã¢â€ â€™Aprobar"

Ã°Å¸Â§Â­ FILTRO 3: ORIGINALIDAD INTELIGENTE (The Discovery)
"Ã‚Â¿Resuelve algo de forma ingeniosa o cuenta una historia?"
Ã¢ÂÅ’ Delantales frases graciosas, tazas forma vÃƒÂ¡ter, plÃƒÂ¡sticos inÃƒÂºtiles, bromas cutres
Ã¢Å“â€¦ Kit Cultivo Setas/Pizza, Mapamundi Corcho/Rascable, CarbonKlean, Cuaderno Reutilizable
CRITERIO: "Ã‚Â¿SorprenderÃƒÂ¡ gratamente o terminarÃƒÂ¡ en un cajÃƒÂ³n?"

Ã°Å¸â€˜â€˜ FILTRO 4: ORGULLO (The Pride Factor)
"Ã‚Â¿Da orgullo regalarlo o parece comprado en gasolinera?"
Ã¢ÂÅ’ Aspecto barato, genÃƒÂ©rico, sin marca, plÃƒÂ¡stico cutre
Ã¢Å“â€¦ Marca reconocida (Lego, Moleskine, Stanley, Le Creuset), Materiales nobles (madera, metal, vidrio)
CRITERIO: "Ã‚Â¿Me sentirÃƒÂ­a bien entregando esto?"

Ã°Å¸â€™Â° CLÃƒÂUSULA "CHEAP & CHIC" (productos <20Ã¢â€šÂ¬ para Amigo Invisible):
NO rechazar por precio bajo, pero aplicar LEY DEL LUJO ACCESIBLE:
Ã¢Å“â€¦ VersiÃƒÂ³n Premium de algo barato (Chocolate Autor vs supermercado)
Ã¢Å“â€¦ Stocking Filler con diseÃƒÂ±o (Llavero Funko, Baraja cartas diseÃƒÂ±o)
Ã¢ÂÅ’ Basura plÃƒÂ¡stica sin gracia

Ã°Å¸â€œÂ¦ EJEMPLOS GIFTIA STANDARD:
"Tupper Ikea" Ã¢â€ â€™ Ã¢ÂÅ’ (ordinario, se tira)
"Monbento Bento Box" Ã¢â€ â€™ Ã¢Å“â€¦ FILTRO 1 (best in class, se cuida)
"Gel ducha familiar" Ã¢â€ â€™ Ã¢ÂÅ’ (necesidad bÃƒÂ¡sica)
"Set jabones Rituals" Ã¢â€ â€™ Ã¢Å“â€¦ FILTRO 2 (capricho que no te compras)
"Taza con chiste malo" Ã¢â€ â€™ Ã¢ÂÅ’ (kitsch, terminarÃƒÂ¡ olvidada)
"Kit cultivo setas gourmet" Ã¢â€ â€™ Ã¢Å“â€¦ FILTRO 3 (ingenioso, experiencia)
"Auriculares chinos" Ã¢â€ â€™ Ã¢ÂÅ’ (vergÃƒÂ¼enza regalar)
"Marshall Stanmore" Ã¢â€ â€™ Ã¢Å“â€¦ FILTRO 4 (orgullo, marca icÃƒÂ³nica)
"Chocolate Milka" Ã¢â€ â€™ Ã¢ÂÅ’ (supermercado)
"Chocolate Lindt Excellence 85%" Ã¢â€ â€™ Ã¢Å“â€¦ CHEAP&CHIC (lujo accesible)

CATEGORIAS (exactamente una): {', '.join(VALID_CATEGORIES)}
EDADES (1-3): {', '.join(valid_ages)}
OCASIONES (1-3): {', '.join(valid_occasions)}
GENEROS: {', '.join(valid_genders)}

Responde SOLO JSON vÃƒÂ¡lido:
{{
    "is_good_gift": true/false,
    "reject_reason": "si false: quÃƒÂ© filtro falla y por quÃƒÂ©",
    "approved_filter": "si true: cual de los 4 filtros supera (utilidad/indulgencia/originalidad/orgullo)",
    "target_gender": "uno de la lista",
    "category": "UNA de la lista",
    "gift_quality": 1-10,
    "is_duplicate": true/false,
    "etapas": ["edad1", "edad2"],
    "ocasiones": ["ocasion1", "ocasion2"],
    "delivery": "express" | "standard",
    "seo_title": "Titulo viral max 60 chars",
    "gift_headline": "Frase gancho 10-15 palabras que haga DESEAR este regalo",
    "gift_pros": ["Pro 1 corto", "Pro 2 corto", "Pro 3 corto"]
}}

CRITERIOS CLASIFICACIÃƒâ€œN:
- gift_quality: 1-4 meh, 5-6 ok, 7-8 bueno, 9-10 GEMA
- target_gender: "kids" SOLO juguetes 3-12. Alcohol/cafÃƒÂ© = adultos
- gift_headline: persuasiva, ej "El capricho gourmet que nadie se compra pero todos desean"

Solo JSON."""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,  # Muy determinista
            "maxOutputTokens": 500  # Aumentado para campos enriquecidos
        }
    }
    
    # Ã°Å¸ÂÂ¢ PACING: Esperar para no exceder 15 RPM del Free Tier
    global _last_gemini_call, _current_key_index
    time_since_last = time.time() - _last_gemini_call
    if time_since_last < GEMINI_PACING_SECONDS:
        wait_time = GEMINI_PACING_SECONDS - time_since_last
        logger.debug(f"Ã°Å¸ÂÂ¢ Pacing: esperando {wait_time:.1f}s antes de llamar a Gemini...")
        time.sleep(wait_time)
    _last_gemini_call = time.time()
    
    # Ã°Å¸â€â€˜ ROTACIÃƒâ€œN DE KEYS: Intentar con cada key disponible
    keys_tried = 0
    while keys_tried < len(GEMINI_API_KEYS):
        current_key = GEMINI_API_KEYS[_current_key_index]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={current_key}"
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=GEMINI_TIMEOUT_SECONDS
            )
            
            # Quota exceeded - rotar a siguiente key
            if response.status_code == 429:
                old_index = _current_key_index
                _current_key_index = (_current_key_index + 1) % len(GEMINI_API_KEYS)
                keys_tried += 1
                logger.info(f"Ã°Å¸â€â€˜ Key {old_index + 1} quota excedida Ã¢â€ â€™ Rotando a Key {_current_key_index + 1}")
                
                if keys_tried < len(GEMINI_API_KEYS):
                    time.sleep(1)  # Breve pausa antes de intentar con otra key
                    continue
                else:
                    # Todas las keys agotadas, esperar y reintentar
                    logger.warning(f"Ã¢Å¡Â Ã¯Â¸Â Todas las {len(GEMINI_API_KEYS)} keys agotadas. Esperando {GEMINI_RETRY_WAIT}s...")
                    time.sleep(GEMINI_RETRY_WAIT)
                    keys_tried = 0  # Reiniciar contador para otro ciclo
                    continue
            
            if response.status_code != 200:
                logger.warning(f"Ã¢Å¡Â Ã¯Â¸Â Gemini error {response.status_code}: {response.text[:100]}")
                return None
            
            data = response.json()
            text_response = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            # Limpiar respuesta (a veces Gemini aÃƒÂ±ade markdown)
            text_response = text_response.strip()
            if text_response.startswith("```"):
                text_response = re.sub(r'^```json?\s*', '', text_response)
                text_response = re.sub(r'\s*```$', '', text_response)
            
            result = json.loads(text_response)
            logger.debug(f"Ã°Å¸Â§Â  Gemini: {result}")
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Ã¢Å¡Â Ã¯Â¸Â Gemini JSON invÃƒÂ¡lido: {text_response[:100]}")
            return None
        except requests.exceptions.Timeout:
            logger.warning("Ã¢Å¡Â Ã¯Â¸Â Gemini timeout")
            return None
        except Exception as e:
            logger.warning(f"Ã¢Å¡Â Ã¯Â¸Â Gemini error: {e}")
            return None
    
    return None


def classify_with_gemini_or_fallback(title, price, description=""):
    """
    Intenta clasificar con Gemini. Si falla, usa el sistema regex como fallback.
    """
    # Intentar con Gemini
    gemini_result = ask_gemini_judge(
        title=title,
        price=price,
        already_sent_categories=SENT_CATEGORIES_CACHE
    )
    
    if gemini_result:
        return {
            "source": "gemini",
            "is_good_gift": gemini_result.get("is_good_gift", True),
            "reject_reason": gemini_result.get("reject_reason"),
            "target_gender": gemini_result.get("target_gender", "unisex"),
            "category": gemini_result.get("category", "Friki"),
            "gift_quality": gemini_result.get("gift_quality", 5),
            "is_duplicate": gemini_result.get("is_duplicate", False),
            # Nuevos campos enriquecidos (usar slugs SEO-friendly)
            "etapas": gemini_result.get("etapas", ["adultos"]),
            "ocasiones": gemini_result.get("ocasiones", ["cumpleanos", "sin-motivo"]),
            "delivery": gemini_result.get("delivery", "standard"),
            "seo_title": gemini_result.get("seo_title", ""),
            "gift_headline": gemini_result.get("gift_headline", ""),
            "gift_pros": gemini_result.get("gift_pros", [])
        }
    
    # Fallback al sistema regex
    return {
        "source": "fallback",
        "is_good_gift": True,  # El filtro regex ya pasÃƒÂ³
        "reject_reason": None,
        "target_gender": detect_target_gender(title, description),
        "category": classify_product_vibes(title, description, str(price))[0] if classify_product_vibes(title, description, str(price)) else "Friki",
        "gift_quality": 6,
        "is_duplicate": is_duplicate_category(title),
        # Fallback con slugs SEO-friendly
        "etapas": ["adultos"],
        "ocasiones": ["cumpleanos", "sin-motivo"],
        "delivery": "standard",
        "seo_title": "",
        "gift_headline": "",
        "gift_pros": []
    }

# ============================================================================
# CONFIGURACIÃƒâ€œN DE CALIDAD
# ============================================================================

BLACKLIST = {
    # Palabras sospechosas que disminuyen score (no matan)
    "suspicious_keywords": [
        "fake", "rÃƒÂ©plica", "genÃƒÂ©rico", "pack ahorro", "lote",
        "outlet", "defectuoso", "reparado", "reacondicionado",
        "imitaciÃƒÂ³n", "copia"
    ],
    
    # Precios sospechosos
    "min_price_eur": 12.0,      # Nada por debajo de 12Ã¢â€šÂ¬
    "max_price_eur": 9999.0,    # Nada absurdamente caro
    "preferred_price_range": (20, 500),  # Rango ideal para regalos
    
    # =========================================================================
    # REQUISITOS DE CALIDAD PREMIUM - Solo productos top
    # =========================================================================
    "min_rating": 4.0,          # MÃƒÂ­nimo 4.5 estrellas (ESTRICTO)
    "min_reviews": 50,          # MÃƒÂ­nimo 50 reseÃƒÂ±as (productos mainstream)
    "min_reviews_niche": 20,    # MÃƒÂ­nimo 20 para productos nicho/premium
    "niche_price_threshold": 100,  # +100Ã¢â€šÂ¬ = nicho, menor requisito de reviews
    
    # Requisitos de tÃƒÂ­tulo
    "min_title_length": 15,     # TÃƒÂ­tulos demasiado cortos = basura
    "max_title_length": 200,    # TÃƒÂ­tulos demasiado largos = spam
}

# ============================================================================
# PALABRAS CLAVE DE RELEVANCIA - Scoring de regalos
# ============================================================================

GIFT_KEYWORDS = {
    "premium": 10,
    "exclusivo": 10,
    "limitado": 9,
    "ediciÃƒÂ³n especial": 9,
    "oficial": 8,
    "autÃƒÂ©ntico": 8,
    "licenciado": 8,
    "original": 7,
    "handmade": 9,
    "artesanal": 8,
    "ecolÃƒÂ³gico": 7,
    "orgÃƒÂ¡nico": 7,
    "sostenible": 6,
    "premium quality": 8,
    "pro": 5,
    "profesional": 6,
    "expert": 6,
    "master": 5,
}


# ============================================================================
# Ã°Å¸Â§Â  MOTOR DE ANÃƒÂLISIS CONTEXTUAL
# ============================================================================

def analyze_context(text, keyword):
    """
    Analiza si una palabra 'peligrosa' estÃƒÂ¡ en contexto bueno o malo.
    Retorna: 'good', 'bad', o 'neutral'
    """
    rules = CONTEXT_RULES.get(keyword)
    if not rules:
        return "neutral"
    
    text_lower = text.lower()
    
    # Primero checar contexto malo (mÃƒÂ¡s restrictivo)
    for bad in rules["bad_context"]:
        if bad in text_lower:
            return "bad"
    
    # Luego checar contexto bueno (salvavidas)
    for good in rules["good_context"]:
        if good in text_lower:
            return "good"
    
    return "neutral"  # Ambiguo - penalizar ligeramente


# ============================================================================
# MOTOR DE SCORING SEMÃƒÂNTICO
# ============================================================================

def calculate_gift_score(title, price_str, description=""):
    """
    Calcula puntuaciÃƒÂ³n de 0-100 para determinar si es un regalo perfecto.
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
    
    # PenalizaciÃƒÂ³n por precio fuera de rango
    if price < BLACKLIST["min_price_eur"]:
        return 0
    if price > BLACKLIST["max_price_eur"]:
        return 0
    
    # Bonus por rango ideal de regalo (20-500Ã¢â€šÂ¬)
    if BLACKLIST["preferred_price_range"][0] <= price <= BLACKLIST["preferred_price_range"][1]:
        score += 20
    elif price > 500:
        score -= 5
    
    # BÃƒÂºsqueda de palabras clave premium (GIFT_KEYWORDS originales)
    for keyword, points in GIFT_KEYWORDS.items():
        if keyword in full_text:
            score += min(points, 15)
    
    # Ã°Å¸Â§Â  BONUS por GOLDEN KEYWORDS (v9.0)
    for gold in GOLDEN_KEYWORDS:
        if gold in full_text:
            score += 12
    
    # Penalizar palabras sospechosas
    for keyword in BLACKLIST["suspicious_keywords"]:
        if keyword in full_text:
            score -= 10
    
    # Ã°Å¸Â§Â  PenalizaciÃƒÂ³n por palabras peligrosas en contexto neutral
    for dangerous_word in CONTEXT_RULES.keys():
        if dangerous_word in full_text:
            context = analyze_context(full_text, dangerous_word)
            if context == "neutral":
                score -= 8  # Ambiguo = sospechoso
            elif context == "good":
                score += 10  # Contexto positivo = bonus
    
    # ValidaciÃƒÂ³n de longitud de tÃƒÂ­tulo
    if len(title) < BLACKLIST["min_title_length"]:
        score -= 20
    if len(title) > BLACKLIST["max_title_length"]:
        score -= 15
    
    # Bonus por signos de calidad
    if "Ã¢Ëœâ€¦" in title or "Ã¢Â­Â" in title:
        score += 5
    if "official" in title_lower or "oficial" in title_lower:
        score += 10
    
    return max(0, min(100, score))  # Clamp a 0-100


def is_garbage(title, price_str, description=""):
    """
    Ã°Å¸Â§Â  FILTRADO CONTEXTUAL SEMÃƒÂNTICO v9.0
    Ya no bloquea palabras "tontas". Analiza el CONTEXTO.
    """
    title_lower = title.lower()
    full_text = (title_lower + " " + description.lower()).strip()
    
    # 1. KILLER KEYWORDS - Muerte sÃƒÂºbita
    for killer in KILLER_KEYWORDS:
        if killer in title_lower:
            logger.info(f"Ã°Å¸â€™â‚¬ KILLER: '{killer}' en {title[:50]}")
            return True
    
    # 2. ANÃƒÂLISIS CONTEXTUAL - La magia del v9.0
    for dangerous_word in CONTEXT_RULES.keys():
        if dangerous_word in title_lower:
            context = analyze_context(full_text, dangerous_word)
            if context == "bad":
                logger.info(f"Ã¢â€ºâ€ CONTEXTO MALO: '{dangerous_word}' en {title[:50]}")
                return True
            elif context == "good":
                logger.info(f"Ã¢Å“Â¨ CONTEXTO BUENO: '{dangerous_word}' salvado")
    
    # 3. CONSUMIBLES (cantidades grandes) - EXCEPTO productos que son regalos vÃƒÂ¡lidos
    consumable_match = re.search(r'\b\d{2,}\s*(piezas|unidades|pcs|ud|uds)\b', title_lower)
    if consumable_match:
        # Excepciones: productos donde "X piezas" es caracterÃƒÂ­stica, no consumible
        gift_with_pieces = [
            "lego", "playmobil", "puzzle", "rompecabezas", "maqueta", "kit de",
            "set de", "pack regalo", "caja de", "colecciÃƒÂ³n", "pintura", "acuarela",
            "rotulador", "lapiz", "crayon", "herramienta", "construcciÃƒÂ³n",
            "bloques", "mecano", "k'nex", "magnetiles", "juego de mesa"
        ]
        if not any(x in title_lower for x in gift_with_pieces):
            logger.info(f"Ã°Å¸â€Â§ CONSUMIBLE: {title[:50]}")
            return True
    
    # 4. PRECIO
    price = parse_price(price_str)
    if price <= 0:
        logger.info(f"Ã°Å¸â€™Â° PRECIO INVÃƒÂLIDO ({price}Ã¢â€šÂ¬): {title[:40]}...")
        return True
    if price < BLACKLIST["min_price_eur"]:
        logger.info(f"Ã°Å¸â€™Â° PRECIO BAJO ({price}Ã¢â€šÂ¬ < {BLACKLIST['min_price_eur']}Ã¢â€šÂ¬): {title[:40]}...")
        return True
    if price > BLACKLIST["max_price_eur"]:
        logger.info(f"Ã°Å¸â€™Â° PRECIO ALTO ({price}Ã¢â€šÂ¬ > {BLACKLIST['max_price_eur']}Ã¢â€šÂ¬): {title[:40]}...")
        return True
    
    return False


def classify_product_vibes(title, description="", price_str=""):
    """
    Clasifica automÃƒÂ¡ticamente el producto en categorÃƒÂ­as de Giftia (gf_category).
    Retorna array de categorÃƒÂ­as que coinciden: ['Tech', 'Gamer', etc]
    NOTA: Este es un fallback regex. El sistema principal usa process_queue.py
    con Gemini para clasificaciÃƒÂ³n avanzada (vibes, etapas, ocasiones).
    """
    text = (title + " " + description).lower()
    matched_vibes = []
    
    # Construir vibe_keywords desde el schema si estÃƒÂ¡ disponible
    if GIFTIA_SCHEMA and 'categories' in GIFTIA_SCHEMA:
        vibe_keywords = {}
        for cat_name, cat_data in GIFTIA_SCHEMA['categories'].items():
            # Los keywords vienen del schema
            keywords = cat_data.get('keywords', [])
            if keywords:
                # Convertir a lowercase para comparaciÃƒÂ³n
                vibe_keywords[cat_name] = [kw.lower() for kw in keywords]
    else:
        # Fallback con keywords hardcodeados si no hay schema
        vibe_keywords = {
            "Tech": ["gadget", "tech", "electrÃƒÂ³nic", "usb", "inalÃƒÂ¡mbric", "inteligent", "smart", "auricular", "smartwatch", "bluetooth", "wifi", "led"],
            "Gourmet": ["cafÃƒÂ©", "tea", "vino", "queso", "aceite", "gourmet", "cocinero", "chef", "especias", "chocolate", "jamÃƒÂ³n", "whisky", "gin", "cafetera", "cuchillo"],
            "Friki": ["funko", "pop", "star wars", "harry potter", "marvel", "anime", "manga", "coleccion", "geek", "nerd", "estatua", "figura", "pokemon", "disney"],
            "Gamer": ["playstation", "xbox", "nintendo", "gaming", "mando", "consola", "ps5", "videojuego", "esport"],
            "Zen": ["meditaci", "yoga", "spa", "aromaterapia", "difusor", "vela", "cristal", "chakra", "mindfulness", "relajaci", "bienestar"],
            "Viajes": ["mochila", "maleta", "viajero", "viaje", "portÃƒÂ¡til", "backpack", "adaptador", "equipaje"],
            "Outdoor": ["camping", "trekking", "acampad", "senderismo", "montaÃƒÂ±a", "aventura", "linterna", "navaja"],
            "Deporte": ["deporte", "runner", "ejercicio", "gym", "bicicleta", "running", "entrenamiento", "sport", "pesas", "mancuerna", "fitness", "yoga mat", "esterilla"],
            "Moda": ["ropa", "zapatos", "bolso", "reloj", "gafas", "cinturÃƒÂ³n", "cartera", "sombrero", "bufanda", "joya", "moda", "perfume"],
            "Belleza": ["maquillaje", "skincare", "cosmÃƒÂ©tica", "crema", "sÃƒÂ©rum", "beauty", "tratamiento facial", "mascarilla"],
            "DecoraciÃƒÂ³n": ["decoraciÃƒÂ³n", "hogar", "lÃƒÂ¡mpara", "cojÃƒÂ­n", "cuadro", "jarrÃƒÂ³n", "vela decorativa", "estanterÃƒÂ­a"],
            "Artista": ["acuarela", "ÃƒÂ³leo", "pintura", "pincel", "lienzo", "caballete", "dibujo", "sketch", "rotulador", "lettering", "manualidad", "craft", "arcilla", "escultura", "copic", "wacom", "tableta grÃƒÂ¡fica", "scrapbook", "bordado"],
            "Lector": ["libro", "lectura", "kindle", "e-reader", "literatura", "novela", "marcapÃƒÂ¡ginas", "estanterÃƒÂ­a libros"],
            "MÃƒÂºsica": ["guitarra", "piano", "ukelele", "instrumento", "vinilo", "tocadiscos", "auriculares mÃƒÂºsica", "altavoz"],
            "FotografÃƒÂ­a": ["cÃƒÂ¡mara", "fotografÃƒÂ­a", "polaroid", "instax", "ÃƒÂ¡lbum foto", "trÃƒÂ­pode", "objetivo", "impresora foto"],
            "Mascotas": ["perro", "gato", "mascota", "pet", "collar mascota", "comedero", "cama perro", "juguete mascota"],
            "Lujo": ["premium", "lujo", "luxury", "oro", "plata", "exclusivo", "ediciÃƒÂ³n limitada"],
            "Digital": ["tarjeta regalo", "cÃƒÂ³digo", "suscripciÃƒÂ³n", "netflix", "spotify", "steam", "playstation store", "xbox game pass", "nintendo eshop", "amazon prime", "disney plus", "curso online", "ebook", "kindle unlimited"],
            "Experiencias": ["smartbox", "wonderbox", "escapada", "entrada", "concierto", "experiencia", "spa", "vuelo", "paracaÃƒÂ­das", "globo", "ferrari", "cata", "escape room", "hotel", "viaje sorpresa"],
        }
    
    for vibe, keywords in vibe_keywords.items():
        for keyword in keywords:
            if keyword in text:
                matched_vibes.append(vibe)
                break  # Una vez encontrado, pasar al siguiente vibe
    
    return matched_vibes if matched_vibes else ["Friki"]  # Default


def classify_product_recipients(title, description=""):
    """
    Clasifica automÃƒÂ¡ticamente para quÃƒÂ© tipos de personas es ideal.
    Retorna array de recipients: ['Tech Lover', 'Foodie', etc]
    """
    text = (title + " " + description).lower()
    recipients = []
    
    recipient_keywords = {
        "Tech Lover": ["gadget", "tech", "smart", "digital", "electrÃƒÂ³nic", "usb", "app", "software"],
        "Foodie": ["food", "comida", "cafÃƒÂ©", "vino", "queso", "gourmet", "chef", "cocinero"],
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
# ============================================================================
# SELENIUM DRIVER SETUP - initialized in main()
# ============================================================================
driver = None  # Global driver variable

def send_to_giftia(datos):
    """
    EnvÃƒÂ­a producto validado a la API de Giftia con metadata de clasificaciÃƒÂ³n.
    FILTRO PREMIUM: Solo productos con 4.5+ estrellas y suficientes reseÃƒÂ±as.
    DEDUPLICACIÃƒâ€œN: No enviar productos duplicados o de categorÃƒÂ­as saturadas.
    DEMOGRAFÃƒÂA: Detecta gÃƒÂ©nero/target del producto.
    """
    # Validaciones previas
    if not datos.get("asin") or not datos.get("title"):
        logger.warning("Datos incompletos, ignorando")
        return False
    
    # =========================================================================
    # DEDUPLICACIÃƒâ€œN - Evitar productos repetidos
    # =========================================================================
    asin = datos["asin"]
    title = datos["title"]
    
    # Ya enviamos este ASIN exacto?
    if asin in SENT_PRODUCTS_CACHE:
        logger.info(f"Ã°Å¸â€â€ž DUPLICADO (ASIN): {title[:40]}...")
        return False
    
    # Ya tenemos demasiados de esta categorÃƒÂ­a?
    if is_duplicate_category(title):
        category = get_product_category(title)
        logger.info(f"Ã°Å¸â€â€ž DUPLICADO (categorÃƒÂ­a '{category}'): {title[:40]}...")
        return False
    
    # =========================================================================
    # FILTRO DE CALIDAD PREMIUM - Solo productos top de Amazon
    # =========================================================================
    # SISTEMA DE CALIDAD DINÃƒÂMICO
    # 1000+ reviews Ã¢â€ â€™ 4.2Ã¢Â­Â mÃƒÂ­nimo
    # 500-999 reviews Ã¢â€ â€™ 4.3Ã¢Â­Â mÃƒÂ­nimo
    # 100-499 reviews Ã¢â€ â€™ 4.5Ã¢Â­Â mÃƒÂ­nimo
    # 50-99 reviews Ã¢â€ â€™ 4.7Ã¢Â­Â mÃƒÂ­nimo
    # <50 reviews Ã¢â€ â€™ DESCARTAR
    # =========================================================================
    rating_value = datos.get("rating_value", 0.0)
    review_count = datos.get("review_count", 0)
    
    # MÃƒÂ­nimo absoluto: 50 reviews
    if review_count < 50:
        logger.info(f"Ã°Å¸â€œÅ  POCAS REVIEWS ({review_count}<50): {datos['title'][:40]}...")
        return False
    
    # Rating dinÃƒÂ¡mico segÃƒÂºn cantidad de reviews
    if review_count >= 1000:
        min_rating = 4.2
    elif review_count >= 500:
        min_rating = 4.3
    elif review_count >= 100:
        min_rating = 4.5
    else:  # 50-99 reviews - productos nicho
        min_rating = 4.7
    
    if rating_value < min_rating:
        logger.info(f"Ã¢Â­Â RATING BAJO ({rating_value}<{min_rating} para {review_count} reviews): {datos['title'][:40]}...")
        return False
    
    logger.info(f"Ã¢Å“â€¦ CALIDAD OK: {rating_value}Ã¢Â­Â con {review_count} reviews (min: {min_rating})")
    
    # Check garbage (pre-filtro rÃƒÂ¡pido Python)
    if is_garbage(datos["title"], datos.get("price", "0"), datos.get("description", "")):
        logger.info(f"Ã°Å¸â€”â€˜Ã¯Â¸Â BASURA: {datos['title'][:50]}...")
        return False
    
    # =========================================================================
    # Ã°Å¸Â§Â  JUEZ GEMINI - ClasificaciÃƒÂ³n inteligente con IA
    # =========================================================================
    price_value = float(re.sub(r"[^0-9.,]", "", datos.get("price", "0")).replace(",", ".").strip() or "0")
    classification = classify_with_gemini_or_fallback(
        title=datos["title"],
        price=price_value,
        description=datos.get("description", "")
    )
    
    # Si Gemini dice que NO es buen regalo, rechazar
    if not classification["is_good_gift"]:
        reason = classification.get("reject_reason", "no es buen regalo")
        source_emoji = "Ã°Å¸Â§Â " if classification["source"] == "gemini" else "Ã°Å¸â€Â§"
        logger.info(f"{source_emoji} RECHAZADO: {reason} - {datos['title'][:40]}...")
        return False
    
    # Si Gemini detecta duplicado
    if classification["is_duplicate"]:
        logger.info(f"Ã°Å¸Â§Â  DUPLICADO (Gemini): {datos['title'][:40]}...")
        return False
    
    # Usar clasificaciÃƒÂ³n de Gemini (o fallback)
    target_gender = classification["target_gender"]
    gemini_category = validate_category(classification["category"])  # VALIDAR categorÃƒÂ­a
    gift_quality = classification["gift_quality"]
    source = classification["source"]
    
    # Si gift_quality < 5, descartar (solo con Gemini)
    if source == "gemini" and gift_quality < 5:
        logger.info(f"Ã°Å¸Â§Â  CALIDAD BAJA ({gift_quality}/10): {datos['title'][:40]}...")
        return False
    
    # Calcular score (combinamos Gemini + regex)
    score = calculate_gift_score(
        datos["title"], 
        datos.get("price", "0"),
        datos.get("description", "")
    )
    
    # Ajustar score con gift_quality de Gemini
    if source == "gemini":
        score = int(score * 0.5 + gift_quality * 5)  # Blend 50-50
    
    if score < 30:
        logger.info(f"Ã°Å¸â€œâ€° Score bajo ({score}): {datos['title'][:40]}...")
        return False
    
    # ClasificaciÃƒÂ³n automÃƒÂ¡tica (vibes y recipients del sistema regex)
    vibes = classify_product_vibes(datos["title"], datos.get("description", ""), datos.get("price", ""))
    # Validar cada vibe tambiÃƒÂ©n
    vibes = [validate_category(v) for v in vibes]
    vibes = list(set(vibes))  # Eliminar duplicados
    recipients = classify_product_recipients(datos["title"], datos.get("description", ""))
    
    # Enriquecer datos con clasificaciÃƒÂ³n hÃƒÂ­brida
    datos["vibes"] = vibes
    datos["recipients"] = recipients
    datos["gift_score"] = score
    datos["target_gender"] = target_gender  # De Gemini o fallback
    datos["gemini_category"] = gemini_category  # CategorÃƒÂ­a inteligente (VALIDADA)
    datos["classification_source"] = source  # 'gemini' o 'fallback'
    datos["gift_quality"] = gift_quality if source == "gemini" else None
    datos["discovered_at"] = datetime.now().isoformat()
    
    # Datos enriquecidos de Gemini (nuevos campos v11)
    datos["etapas"] = classification.get("etapas", ["adultos"])
    datos["ocasiones"] = classification.get("ocasiones", ["cumpleanos", "sin-motivo"])
    datos["delivery"] = classification.get("delivery", "standard")
    datos["seo_title"] = classification.get("seo_title", "")
    datos["gift_headline"] = classification.get("gift_headline", "")
    datos["gift_pros"] = classification.get("gift_pros", [])
    
    # EnvÃƒÂ­o
    source_emoji = "Ã°Å¸Â§Â " if source == "gemini" else "Ã°Å¸â€Â§"
    gender_emoji = {"male": "Ã°Å¸â€˜Â¨", "female": "Ã°Å¸â€˜Â©", "kids": "Ã°Å¸â€˜Â¶", "unisex": "Ã°Å¸â€˜Â¥"}.get(target_gender, "Ã°Å¸â€˜Â¥")
    logger.info(f"{source_emoji} ENVIANDO [Score:{score}|Q:{gift_quality}] {gender_emoji} [{gemini_category}] {datos['title'][:40]}...")
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'X-GIFTIA-TOKEN': WP_TOKEN,
            'User-Agent': 'GiftiaHunter/10.0'
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
            # Registrar para evitar duplicados
            register_sent_product(datos["asin"], datos["title"])
            return True
        else:
            logger.error(f"Error API {response.status_code}: {response.text[:100]}")
            return False
            
    except Exception as e:
        logger.error(f"Excepcion al enviar: {str(e)}")
        return False


# ============================================================================
# Ã°Å¸â€œÂ¦ SISTEMA DE COLA - AÃƒÂ±adir producto para anÃƒÂ¡lisis posterior
# ============================================================================

def queue_for_ai_analysis(datos):
    """
    FASE 1: Filtros bÃƒÂ¡sicos + aÃƒÂ±adir a cola.
    NO llama a Gemini, solo filtra basura obvia y aÃƒÂ±ade a cola.
    """
    # Validaciones previas
    if not datos.get("asin") or not datos.get("title"):
        logger.warning("Datos incompletos, ignorando")
        return False
    
    asin = datos["asin"]
    title = datos["title"]
    
    # Ya enviamos este ASIN exacto?
    if asin in SENT_PRODUCTS_CACHE:
        logger.debug(f"Ã°Å¸â€â€ž DUPLICADO (ASIN ya enviado): {title[:40]}...")
        return False
    
    # Ya estÃƒÂ¡ en cola?
    queue = load_pending_queue()
    if any(p.get('asin') == asin for p in queue):
        logger.debug(f"Ã°Å¸â€â€ž YA EN COLA: {title[:40]}...")
        return False
    
    # Demasiados de esta categorÃƒÂ­a?
    if is_duplicate_category(title):
        category = get_product_category(title)
        logger.debug(f"Ã°Å¸â€â€ž DUPLICADO (categorÃƒÂ­a '{category}'): {title[:40]}...")
        return False
    
    # Filtro de calidad: reviews y rating
    rating_value = datos.get("rating_value", 0.0)
    review_count = datos.get("review_count", 0)
    
    if review_count < 50:
        logger.debug(f"Ã°Å¸â€œÅ  POCAS REVIEWS ({review_count}<50): {title[:40]}...")
        return False
    
    # Rating dinÃƒÂ¡mico segÃƒÂºn cantidad de reviews
    if review_count >= 1000:
        min_rating = 4.2
    elif review_count >= 500:
        min_rating = 4.3
    elif review_count >= 100:
        min_rating = 4.5
    else:
        min_rating = 4.7
    
    if rating_value < min_rating:
        logger.debug(f"Ã¢Â­Â RATING BAJO ({rating_value}<{min_rating}): {title[:40]}...")
        return False
    
    # Pre-filtro rÃƒÂ¡pido Python (sin Gemini)
    if is_garbage(title, datos.get("price", "0"), datos.get("description", "")):
        logger.debug(f"Ã°Å¸â€”â€˜Ã¯Â¸Â BASURA: {title[:50]}...")
        return False
    
    # Ã‚Â¡Producto vÃƒÂ¡lido! AÃƒÂ±adir a cola
    logger.info(f"Ã¢Å“â€¦ CANDIDATO [Rating:{rating_value}Ã¢Â­Â|Reviews:{review_count}]: {title[:50]}...")
    return add_to_pending_queue(datos)


def process_queued_product(product):
    """
    FASE 2: Procesar producto de cola con Gemini y enviar a WordPress.
    """
    title = product.get("title", "")
    asin = product.get("asin", "")
    
    # Verificar que no se haya enviado mientras estaba en cola
    if asin in SENT_PRODUCTS_CACHE:
        logger.info(f"Ã¢ÂÂ­Ã¯Â¸Â Ya enviado: {title[:40]}...")
        return False
    
    # Calcular precio
    price_value = float(re.sub(r"[^0-9.,]", "", product.get("price", "0")).replace(",", ".").strip() or "0")
    
    # Ã°Å¸Â§Â  LLAMAR A GEMINI (aquÃƒÂ­ sÃƒÂ­, con pacing)
    classification = classify_with_gemini_or_fallback(
        title=title,
        price=price_value,
        description=product.get("description", "")
    )
    
    # Si Gemini dice NO
    if not classification["is_good_gift"]:
        reason = classification.get("reject_reason", "no es buen regalo")
        source_emoji = "Ã°Å¸Â§Â " if classification["source"] == "gemini" else "Ã°Å¸â€Â§"
        logger.info(f"{source_emoji} RECHAZADO: {reason} - {title[:40]}...")
        log_processed_product(product, {"status": "rejected", "reason": reason})
        return False
    
    if classification["is_duplicate"]:
        logger.info(f"Ã°Å¸Â§Â  DUPLICADO (Gemini): {title[:40]}...")
        log_processed_product(product, {"status": "rejected", "reason": "duplicado"})
        return False
    
    # Extraer clasificaciÃƒÂ³n
    target_gender = classification["target_gender"]
    gemini_category = validate_category(classification["category"])
    gift_quality = classification["gift_quality"]
    source = classification["source"]
    
    # Calidad mÃƒÂ­nima
    if source == "gemini" and gift_quality < 5:
        logger.info(f"Ã°Å¸Â§Â  CALIDAD BAJA ({gift_quality}/10): {title[:40]}...")
        log_processed_product(product, {"status": "rejected", "reason": f"calidad {gift_quality}/10"})
        return False
    
    # Calcular score
    score = calculate_gift_score(title, product.get("price", "0"), product.get("description", ""))
    if source == "gemini":
        score = int(score * 0.5 + gift_quality * 5)
    
    if score < 30:
        logger.info(f"Ã°Å¸â€œâ€° Score bajo ({score}): {title[:40]}...")
        log_processed_product(product, {"status": "rejected", "reason": f"score {score}"})
        return False
    
    # Enriquecer producto
    vibes = classify_product_vibes(title, product.get("description", ""), product.get("price", ""))
    vibes = list(set([validate_category(v) for v in vibes]))
    recipients = classify_product_recipients(title, product.get("description", ""))
    
    product["vibes"] = vibes
    product["recipients"] = recipients
    product["gift_score"] = score
    product["target_gender"] = target_gender
    product["gemini_category"] = gemini_category
    product["classification_source"] = source
    product["gift_quality"] = gift_quality if source == "gemini" else None
    product["discovered_at"] = product.get("queued_at", datetime.now().isoformat())
    product["processed_at"] = datetime.now().isoformat()
    
    # === AÃƒâ€˜ADIR CAMPOS DE GEMINI AL PRODUCTO ===
    # Estos campos son cruciales para el schema de taxonomÃƒÂ­as
    product["etapas"] = classification.get("etapas", ["adultos"])
    product["ocasiones"] = classification.get("ocasiones", ["cumpleanos", "sin-motivo"])
    product["delivery"] = classification.get("delivery", "standard")
    product["seo_title"] = classification.get("seo_title", "")
    product["gift_headline"] = classification.get("gift_headline", "")
    product["gift_pros"] = classification.get("gift_pros", [])
    
    # ENVIAR A WORDPRESS
    source_emoji = "Ã°Å¸Â§Â " if source == "gemini" else "Ã°Å¸â€Â§"
    gender_emoji = {"male": "Ã°Å¸â€˜Â¨", "female": "Ã°Å¸â€˜Â©", "kids": "Ã°Å¸â€˜Â¶", "unisex": "Ã°Å¸â€˜Â¥"}.get(target_gender, "Ã°Å¸â€˜Â¥")
    logger.info(f"{source_emoji} ENVIANDO [Score:{score}|Q:{gift_quality}] {gender_emoji} [{gemini_category}] {title[:40]}...")
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'X-GIFTIA-TOKEN': WP_TOKEN,
            'User-Agent': 'GiftiaHunter/10.0'
        }
        
        response = requests.post(
            WP_API_URL,
            data=json.dumps(product, ensure_ascii=False).encode('utf-8'),
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Ã¢Å“â€¦ WordPress OK: {title[:40]}")
            register_sent_product(asin, title)
            log_processed_product(product, {"status": "published", "score": score, "quality": gift_quality})
            return True
        else:
            logger.error(f"Ã¢ÂÅ’ Error API {response.status_code}: {response.text[:100]}")
            log_processed_product(product, {"status": "error", "http_code": response.status_code})
            return False
            
    except Exception as e:
        logger.error(f"Ã¢ÂÅ’ ExcepciÃƒÂ³n: {str(e)}")
        log_processed_product(product, {"status": "error", "exception": str(e)})
        return False


def run_queue_processor(max_products=None, pacing_seconds=None):
    """
    Procesa la cola de productos con Gemini.
    Respeta el pacing para no exceder lÃƒÂ­mites de API.
    """
    if pacing_seconds is None:
        pacing_seconds = GEMINI_PACING_SECONDS
    
    queue_size = get_pending_count()
    if queue_size == 0:
        logger.info("Ã°Å¸â€œÂ­ Cola vacÃƒÂ­a, nada que procesar")
        return 0
    
    logger.info(f"Ã°Å¸Å¡â‚¬ PROCESANDO COLA: {queue_size} productos pendientes")
    logger.info(f"Ã¢ÂÂ±Ã¯Â¸Â Pacing: {pacing_seconds}s entre productos ({60/pacing_seconds:.1f} RPM)")
    
    if max_products:
        logger.info(f"Ã°Å¸â€œÅ  LÃƒÂ­mite: {max_products} productos mÃƒÂ¡ximo")
    
    processed = 0
    published = 0
    
    while True:
        product = get_next_from_queue()
        if not product:
            break
        
        if max_products and processed >= max_products:
            # Devolver a cola si excedemos lÃƒÂ­mite
            add_to_pending_queue(product)
            logger.info(f"Ã¢ÂÂ¸Ã¯Â¸Â LÃƒÂ­mite alcanzado ({max_products}), parando")
            break
        
        processed += 1
        remaining = get_pending_count()
        logger.info(f"Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬")
        logger.info(f"Ã°Å¸â€œÂ¦ [{processed}] Procesando... (quedan {remaining} en cola)")
        
        try:
            if process_queued_product(product):
                published += 1
        except Exception as e:
            logger.error(f"Ã¢ÂÅ’ Error procesando: {e}")
            # No devolver a cola para evitar bucle infinito
        
        # Pacing - esperar antes del siguiente
        if get_pending_count() > 0:
            logger.debug(f"Ã¢ÂÂ³ Esperando {pacing_seconds}s...")
            time.sleep(pacing_seconds)
    
    logger.info(f"Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â")
    logger.info(f"Ã°Å¸â€œÅ  RESUMEN COLA: {processed} procesados, {published} publicados")
    logger.info(f"Ã°Å¸â€œÂ­ Quedan {get_pending_count()} en cola")
    return published


# ============================================================================
# BUCLE PRINCIPAL DE SCRAPING
# ============================================================================

# Ã¢ÂÂ° CONFIGURACIÃƒâ€œN DE DURACIÃƒâ€œN
DEFAULT_RUN_HOURS = 6  # Horas de ejecucion por defecto

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Giftia Hunter')
    parser.add_argument('--hours', type=float, default=DEFAULT_RUN_HOURS, help='Horas')
    parser.add_argument('--test', action='store_true', help='Modo test: 5 min')
    args = parser.parse_args()

    RUN_HOURS = 5/60 if args.test else args.hours
    RUN_DURATION_SECONDS = int(RUN_HOURS * 60 * 60)

    start_time = time.time()
    end_time = start_time + RUN_DURATION_SECONDS
    cycle = 0

    mode_text = "MODO TEST (5 min)" if args.test else f"MODO MARATON - {RUN_HOURS}h"
    logger.info(f"HUNTER {mode_text}")
    logger.info(f"Ã¢ÂÂ° Inicio: {datetime.now().strftime('%H:%M:%S')}")
    logger.info(f"Ã¢ÂÂ° Fin previsto: {datetime.fromtimestamp(end_time).strftime('%H:%M:%S')}")
    
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
        # Usar gestor automático de drivers
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        logger.info("[OK] Chrome driver initialized")
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize Chrome: {e}")
        # Intentar fallback sin especificar versión (a veces ayuda si hay conflicto)
        try:
             logger.info("Attempting fallback driver init...")
             driver = webdriver.Chrome(service=Service(), options=options)
        except:
             sys.exit(1)

    
    while time.time() < end_time:
        cycle += 1
        remaining_hours = (end_time - time.time()) / 3600
        logger.info(f"")
        logger.info(f"Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â")
        logger.info(f"Ã°Å¸â€â€ž CICLO {cycle} - Quedan {remaining_hours:.1f}h")
        logger.info(f"Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â")

        # Seleccionar mÃƒÂ¡s vibes para mÃƒÂ¡xima variedad (ahora tenemos 10 categorÃƒÂ­as)
        selected_vibes = random.sample(list(SMART_SEARCHES.keys()), k=min(6, len(SMART_SEARCHES)))
        logger.info(f"[VIBES] Selected: {selected_vibes}")

        total_sent = 0
        total_discarded = 0

        try:
            for vibe in selected_vibes:
                # Verificar tiempo restante
                if time.time() >= end_time:
                    logger.info(f"Ã¢ÂÂ° Tiempo agotado, terminando ciclo...")
                    break
                    
                searches = SMART_SEARCHES[vibe]
                # Seleccionar 4-5 bÃƒÂºsquedas por vibe (antes eran 2-3)
                selected_searches = random.sample(searches, k=min(5, len(searches)))
                
                for query in selected_searches:
                    # Agregar variaciÃƒÂ³n temporal DINÃƒÂMICA
                    current_year = datetime.now().year
                    modifiers = [
                        "",                              # Sin modificador
                        f" {current_year}",              # AÃƒÂ±o actual (2026)
                        f" {current_year - 1}",          # AÃƒÂ±o anterior (2025)
                        " novedades",                    # Novedades
                        " bestseller",                   # MÃƒÂ¡s vendidos
                        " viral",                        # Productos virales
                        " trending",                     # Tendencias
                        " nuevo lanzamiento",            # Lanzamientos recientes
                        " top ventas",                   # Top ventas
                        " mas vendido",                  # MÃƒÂ¡s vendidos espaÃƒÂ±ol
                        " mejor valorado",               # Mejor valorados
                        " idea regalo",                  # Ideas regalo
                        " regalo original",              # Regalo original
                        " regalo perfecto",              # Regalo perfecto
                        " recomendado",                  # Recomendados
                        " premium",                      # Premium
                        " calidad",                      # Calidad
                        " oferta",                       # Ofertas
                        " chollos",                      # Chollos
                        " black friday",                 # Black Friday deals
                        " navidad",                      # Navidad
                        " cumpleaÃƒÂ±os",                   # CumpleaÃƒÂ±os
                        " san valentin",                 # San ValentÃƒÂ­n
                        " dia del padre",                # DÃƒÂ­a del padre
                        " dia de la madre",              # DÃƒÂ­a de la madre
                        " aniversario",                  # Aniversario
                        " exclusivo",                    # Exclusivo
                        " edicion limitada",             # EdiciÃƒÂ³n limitada
                        " profesional",                  # Profesional
                    ]
                    final_query = query + random.choice(modifiers)
                    
                    logger.info(f"[SEARCH] [{vibe}] {final_query}")
                
                # URL con ordenamiento aleatorio para variedad
                sort_options = [
                    "date-desc-rank",                # Por novedad
                    "review-rank",                   # Mejor valorados
                    "popularity-rank",               # MÃƒÂ¡s populares
                    "",                              # Relevancia Amazon
                ]
                sort_param = random.choice(sort_options)
                if sort_param:
                    amazon_url = f"https://www.amazon.es/s?k={final_query.replace(' ', '+')}&s={sort_param}"
                else:
                    amazon_url = f"https://www.amazon.es/s?k={final_query.replace(' ', '+')}"
                
                try:
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
                        logger.debug(f"   WebDriverWait fallÃƒÂ³, usando JavaScript...")
                        # Usar JavaScript para ejecutar scroll y esperar
                        time.sleep(2)
                        driver.execute_script("window.scrollTo(0, 1000);")
                        time.sleep(2)
                        
                        # Encontrar items usando JavaScript
                        items_count = driver.execute_script("""
                            return document.querySelectorAll('[data-component-type="s-search-result"]').length;
                        """)
                        logger.debug(f"   JavaScript encontrÃƒÂ³ {items_count} elementos")
                        
                        # Ahora buscar con Selenium
                        items = driver.find_elements(By.CSS_SELECTOR, 'div[data-component-type="s-search-result"]')
                        
                        # Si aÃƒÂºn no encuentra, intentar selector alternativo
                        if len(items) == 0:
                            logger.debug(f"   Intentando selector alternativo...")
                            items = driver.find_elements(By.CSS_SELECTOR, 'div.s-result-item[data-asin]')
                    
                    logger.debug(f"   Found {len(items)} search results")
                    
                    captured_in_query = 0
                    for item in items:
                        if captured_in_query >= 5:  # MÃƒÂ¡x 5 por bÃƒÂºsqueda
                            break
                        
                        try:
                            # ASIN (identificador ÃƒÂºnico)
                            asin = item.get_attribute("data-asin")
                            if not asin or len(asin) < 10:
                                continue
                            
                            # TÃƒÂ­tulo - MÃƒÂºltiples selectores por si Amazon cambia
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
                                # ÃƒÅ¡ltimo recurso: usar JavaScript
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
                            
                            # Precio
                            try:
                                price_elements = item.find_elements(By.CSS_SELECTOR, ".a-price .a-offscreen")
                                if price_elements:
                                    price_txt = price_elements[0].get_attribute("textContent")
                                    price = price_txt.replace("Ã¢â€šÂ¬", "").replace(".", "").replace(",", ".").strip()
                                else:
                                    price = "0"
                            except:
                                price = "0"
                            
                            # Imagen - LIMPIEZA HD
                            try:
                                raw_img = item.find_element(By.CSS_SELECTOR, "img.s-image").get_attribute("src")
                                # TRUCO HD: Quitar parámetros de calidad baja como ._AC_UL320_
                                # Transforma "...image._AC_UL320_.jpg" en "...image.jpg"
                                image_url = re.sub(r'\._[A-Z]{2}[^.]*_', '', raw_img) if raw_img else ""
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
                                # Extraer nÃƒÂºmero: "4,7 de 5 estrellas" Ã¢â€ â€™ 4.7
                                match = re.search(r'([0-9]+[,.]?[0-9]*)', rating_text.replace(',', '.'))
                                if match:
                                    rating_value = float(match.group(1))
                            except:
                                pass
                            
                            # NÃƒÂºmero de reviews (OBLIGATORIO para calidad)
                            review_count = 0
                            try:
                                # Selector principal - nÃƒÂºmero de reviews junto a las estrellas
                                reviews_el = item.find_element(By.CSS_SELECTOR, "span.a-size-base.s-underline-text")
                                reviews_text = reviews_el.text.replace(".", "").replace(",", "")
                                review_count = int(re.sub(r'[^0-9]', '', reviews_text) or 0)
                            except:
                                try:
                                    # Alternativo 1: dentro del link de reviews
                                    reviews_el = item.find_element(By.CSS_SELECTOR, "a[href*='customerReviews'] span")
                                    reviews_text = reviews_el.text.replace(".", "").replace(",", "")
                                    review_count = int(re.sub(r'[^0-9]', '', reviews_text) or 0)
                                except:
                                    try:
                                        # Alternativo 2: aria-label del rating
                                        rating_link = item.find_element(By.CSS_SELECTOR, "a.a-link-normal[href*='product-reviews']")
                                        aria = rating_link.get_attribute("aria-label") or ""
                                        # "4.5 de 5 estrellas, 1.234 valoraciones"
                                        match = re.search(r'([\d.]+)\s*valoraciones', aria.replace(".", ""))
                                        if match:
                                            review_count = int(match.group(1))
                                    except:
                                        try:
                                            # Alternativo 3: cualquier span con nÃƒÂºmero despuÃƒÂ©s del rating
                                            all_spans = item.find_elements(By.CSS_SELECTOR, "span.a-size-base")
                                            for span in all_spans:
                                                text = span.text.strip()
                                                if text and text.replace(".", "").replace(",", "").isdigit():
                                                    review_count = int(text.replace(".", "").replace(",", ""))
                                                    if review_count > 5:  # Evitar confundir con rating
                                                        break
                                        except:
                                            pass
                            
                            # DescripciÃƒÂ³n/subtÃƒÂ­tulo (optativo)
                            try:
                                description = item.find_element(By.CSS_SELECTOR, ".a-color-base.a-text-normal").text
                            except:
                                description = ""
                            

                            # Prime y envÃƒÂ­o gratis
                            is_prime = False
                            free_shipping = False
                            try:
                                # Detectar Prime badge
                                prime_elements = item.find_elements(By.CSS_SELECTOR, "i.a-icon-prime, .a-icon-prime, span[aria-label*='Prime']")
                                is_prime = len(prime_elements) > 0
                            except:
                                pass
                            
                            # Detectar tiempo de envÃƒÂ­o y envÃƒÂ­o gratis
                            delivery_time = ""
                            try:
                                # Buscar texto de envÃƒÂ­o en mÃƒÂºltiples selectores
                                delivery_selectors = [
                                    "span[data-component-type='s-shipping-label-block']",
                                    "div[data-cy='delivery-recipe']",
                                    "span.a-text-bold[aria-label*='Entrega']",
                                    "span.a-color-base.a-text-bold",
                                    "div.s-align-children-center span"
                                ]
                                for selector in delivery_selectors:
                                    try:
                                        els = item.find_elements(By.CSS_SELECTOR, selector)
                                        for el in els:
                                            text = el.text.strip()
                                            # Buscar patrones de entrega
                                            if any(kw in text.lower() for kw in ['entrega', 'envÃƒÂ­o', 'llega', 'recÃƒÂ­belo', 'maÃƒÂ±ana', 'lunes', 'martes', 'miÃƒÂ©rcoles', 'jueves', 'viernes', 'sÃƒÂ¡bado', 'domingo', 'dÃƒÂ­as']):
                                                if len(text) > len(delivery_time):
                                                    delivery_time = text
                                    except:
                                        continue
                            except:
                                pass
                            
                            # Determinar si es envÃƒÂ­o gratis basado en texto o Prime
                            delivery_lower = delivery_time.lower()
                            free_shipping = is_prime or "gratis" in delivery_lower or "envÃƒÂ­o gratis" in delivery_lower

                            # Extraer EAN (multi-vendor matching)
                            ean = ""
                            try:
                                # Ir a la página del producto para extraer EAN
                                product_url = f"https://www.amazon.es/dp/{asin}"
                                driver.execute_script(f"window.open('{product_url}', '_blank');")
                                driver.switch_to.window(driver.window_handles[-1])
                                time.sleep(2)
                                
                                # Buscar en tabla de detalles técnicos
                                try:
                                    detail_rows = driver.find_elements(By.CSS_SELECTOR, "#detailBullets_feature_div li, #productDetails_detailBullets_sections1 tr, .prodDetTable tr")
                                    logger.info(f"[EAN] Filas detectadas: {len(detail_rows)}")
                                    for row in detail_rows:
                                        try:
                                            text = row.text.lower()
                                            if any(term in text for term in ['ean', 'código de barras', 'gtin', 'ean-13']):
                                                # Extraer código (generalmente después de ':')
                                                ean_match = re.search(r'[\d\s]{13,17}', row.text)
                                                if ean_match:
                                                    ean = ean_match.group(0).replace(' ', '').strip()
                                                    logger.info(f"[EAN] ✓ Encontrado: {ean}")
                                                    break
                                        except:
                                            continue
                                    if not ean:
                                        logger.info(f"[EAN] ✗ No encontrado en {len(detail_rows)} filas")
                                except Exception as e:
                                    logger.warning(f"[EAN] Error búsqueda: {e}")
                                
                                # Cerrar pestaña y volver
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                            except Exception as e:
                                logger.debug(f"No se pudo extraer EAN: {e}")
                                try:
                                    # Asegurar que volvemos a la ventana principal
                                    if len(driver.window_handles) > 1:
                                        driver.close()
                                    driver.switch_to.window(driver.window_handles[0])
                                except:
                                    pass

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
                                    "has_reviews": True,  # Amazon siempre tiene reviews verificadas
                                    "source_vibe": vibe,
                                    "is_prime": is_prime,
                                    "free_shipping": free_shipping,
                                    "delivery_time": delivery_time,
                                    "ean": ean  # Multi-vendor matching
                                }
                                
                                # MODO HÃƒÂBRIDO: aÃƒÂ±adir a cola (no llama a Gemini aÃƒÂºn)
                                if queue_for_ai_analysis(payload):
                                    total_sent += 1
                                    captured_in_query += 1
                                else:
                                    total_discarded += 1
                                time.sleep(random.uniform(0.3, 0.8))
                        
                        except Exception as e:
                            logger.debug(f"Error processing item: {e}")
                            continue
                    
                    time.sleep(random.uniform(2, 5))  # Pause between searches
                
                except Exception as e:
                    logger.error(f"Error searching '{final_query}': {e}")
                    continue
        
            logger.info(f"[SCRAPING DONE] Ã‚Â¡Scraping completado!")
            logger.info(f"   En cola: {total_sent}")
            logger.info(f"   Descartados: {total_discarded}")
            logger.info(f"   Tasa de ÃƒÂ©xito pre-filtro: {(total_sent / max(1, total_sent + total_discarded) * 100):.1f}%")
            
            # =========================================================================
            # Ã°Å¸Â§Â  FASE 2: PROCESAR COLA CON GEMINI
            # =========================================================================
            queue_size = get_pending_count()
            if queue_size > 0:
                logger.info(f"")
                logger.info(f"Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â")
                logger.info(f"Ã°Å¸Â§Â  INICIANDO PROCESAMIENTO IA")
                logger.info(f"Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â")
                logger.info(f"Ã°Å¸â€œÂ¦ Productos en cola: {queue_size}")
                logger.info(f"Ã¢ÂÂ±Ã¯Â¸Â Tiempo estimado: {queue_size * GEMINI_PACING_SECONDS / 60:.1f} minutos")
                logger.info(f"")
                
                # En modo queue, NO procesamos - usar process_queue.py
                if QUEUE_MODE == 'queue':
                    logger.info('Modo QUEUE: productos guardados. Ejecuta process_queue.py')
                    published = 0
                else:
                    published = run_queue_processor()
                
                logger.info(f"")
                logger.info(f"Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â")
                logger.info(f"Ã°Å¸Ââ€  RESUMEN FINAL")
                logger.info(f"Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â")
                logger.info(f"   Scrapeados: {total_sent + total_discarded}")
                logger.info(f"   Pre-filtrados: {total_sent}")
                logger.info(f"   Publicados: {published}")
                logger.info(f"   Tasa conversiÃƒÂ³n: {(published / max(1, total_sent) * 100):.1f}%")
            else:
                logger.info(f"Ã°Å¸â€œÂ­ No hay productos en cola para procesar")

        except KeyboardInterrupt:
            logger.info("Ã°Å¸â€ºâ€˜ Interrumpido por usuario")
            logger.info(f"Ã°Å¸â€œÂ¦ Quedan {get_pending_count()} productos en cola para prÃƒÂ³xima ejecuciÃƒÂ³n")
            break
        except Exception as e:
            logger.error(f"Error en ciclo {cycle}: {e}")
            logger.info(f"Ã°Å¸â€œÂ¦ Quedan {get_pending_count()} productos en cola")
            time.sleep(30)  # Esperar 30s antes del siguiente ciclo si hay error
            continue
    
    # Fin del while - limpieza
    driver.quit()
    logger.info("Ã°Å¸ÂÂ Driver cerrado, sesiÃƒÂ³n de 6 horas terminada")