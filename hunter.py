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
# BÚSQUEDAS INTELIGENTES POR CATEGORÍA - MEGA EXPANSIÓN REGALOS
# ============================================================================

SMART_SEARCHES = {
    # =========================================================================
    # TECH VIBE - Gadgets, Gaming, Tecnología
    # =========================================================================
    "Tech": [
        # Gadgets únicos y originales
        "gadgets tecnologicos regalo original",
        "gadgets curiosos innovadores",
        "mini proyector portatil regalo",
        "cargador inalámbrico diseño premium",
        "estación carga múltiple dispositivos",
        "hub USB-C premium aluminio",
        "lámpara LED inteligente RGB WiFi",
        "despertador digital proyector techo",
        "marco digital fotos WiFi",
        "altavoz bluetooth diseño premium",
        
        # Gaming & eSports
        "auriculares gaming inalámbricos premium",
        "teclado mecánico RGB gaming",
        "ratón gaming profesional inalámbrico",
        "alfombrilla gaming XXL RGB",
        "silla gaming ergonómica premium",
        "mando PS5 edición especial",
        "mando Xbox elite controller",
        "soporte auriculares RGB gaming",
        "capturadora video streaming",
        "micrófono USB streaming podcast",
        
        # Drones & Cámaras
        "drone DJI Mini regalo",
        "cámara acción 4K regalo",
        "gimbal estabilizador smartphone",
        "webcam 4K streaming",
        "anillo luz selfie profesional",
        "trípode smartphone profesional",
        
        # Smart Home
        "Alexa Echo regalo",
        "Google Nest regalo",
        "bombillas inteligentes Philips Hue",
        "enchufe inteligente WiFi",
        "sensor temperatura humedad smart",
        "cerradura inteligente WiFi",
        "timbre video inteligente",
        "robot aspirador regalo",
        
        # Wearables
        "smartwatch regalo premium",
        "Apple Watch correa regalo",
        "Garmin reloj deportivo",
        "Fitbit regalo fitness",
        "gafas realidad virtual Meta Quest",
        "auriculares AirPods regalo",
        "auriculares Sony WH-1000",
        
        # Retro & Nostalgia Tech
        "consola retro mini regalo",
        "Game Boy clásico regalo",
        "tocadiscos vintage regalo",
        "radio retro bluetooth",
        "cámara instantánea Polaroid Instax",
        "máquina escribir bluetooth",
    ],
    
    # =========================================================================
    # GOURMET - Foodies, Cocina, Vinos
    # =========================================================================
    "Gourmet": [
        # Kits y experiencias gastronómicas
        "kit cata vinos regalo premium",
        "kit hacer cerveza artesanal",
        "kit hacer queso casero",
        "kit sushi regalo",
        "kit gin tonic premium botanicos",
        "kit cocktails regalo mixología",
        "kit especias mundo regalo",
        "kit chocolatería artesanal",
        "kit hacer pasta fresca",
        "kit fermentación kombucha",
        
        # Café & Té premium
        "cafetera espresso regalo premium",
        "molinillo café manual regalo",
        "café especialidad regalo gourmet",
        "set té japones regalo",
        "tetera hierro fundido japonesa",
        "matcha kit ceremonial regalo",
        "prensa francesa premium regalo",
        "chemex cafetera regalo",
        "AeroPress regalo café",
        
        # Vinos & Licores
        "decantador vino cristal regalo",
        "set copas vino Riedel regalo",
        "sacacorchos eléctrico premium",
        "enfriador vino regalo",
        "caja vinos reserva regalo",
        "whisky premium regalo single malt",
        "set whisky cristal regalo",
        "ginebra premium regalo botánica",
        "vermut artesanal regalo",
        
        # Utensilios Chef
        "cuchillo chef japonés regalo",
        "set cuchillos damasco regalo",
        "tabla cortar madera noble regalo",
        "mortero mármol regalo",
        "sartén hierro fundido Lodge regalo",
        "olla holandesa Le Creuset regalo",
        "thermomix accesorios regalo",
        "mandolina cocina profesional",
        "báscula cocina precisión",
        
        # Delicatessen
        "aceite oliva premium regalo",
        "jamón ibérico bellota regalo",
        "queso manchego curado regalo",
        "chocolate belga regalo premium",
        "trufa negra regalo gourmet",
        "caviar regalo premium",
        "foie gras regalo gourmet",
        "sal escamas gourmet regalo",
        "vinagre balsámico Módena regalo",
        "miel cruda premium regalo",
        
        # BBQ & Parrilla  
        "kit BBQ regalo premium",
        "termómetro carne bluetooth",
        "ahumador portátil regalo",
        "plancha hierro fundido",
        "carbón binchotan japonés",
        "guantes BBQ resistentes calor",
    ],
    
    # =========================================================================
    # FRIKI / FANDOM - Coleccionismo, Series, Anime, Comics
    # =========================================================================
    "Friki": [
        # Funko Pop & Figuras
        "funko pop edición limitada",
        "funko pop exclusivo chase",
        "funko pop Star Wars regalo",
        "funko pop Marvel Avengers",
        "funko pop Harry Potter",
        "funko pop anime exclusivo",
        "funko pop Disney villanos",
        "funko pop The Office",
        "funko pop Stranger Things",
        "funko pop Game of Thrones",
        
        # LEGO sets coleccionistas
        "LEGO Star Wars UCS regalo",
        "LEGO Technic regalo",
        "LEGO Architecture regalo",
        "LEGO Harry Potter castillo",
        "LEGO Ideas regalo",
        "LEGO Creator Expert regalo",
        "LEGO Marvel regalo",
        "LEGO Nintendo regalo",
        
        # Star Wars
        "sable luz Star Wars regalo",
        "casco Star Wars regalo réplica",
        "figura Star Wars Black Series",
        "maqueta Star Wars regalo",
        "libro arte Star Wars",
        "disfraz Mandalorian premium",
        
        # Marvel & DC
        "figura Marvel Legends regalo",
        "escudo Capitán América regalo",
        "casco Iron Man regalo",
        "guante infinito Thanos regalo",
        "cómic Marvel omnibus regalo",
        "figura Batman premium regalo",
        "Batarang réplica regalo",
        
        # Harry Potter
        "varita Harry Potter regalo oficial",
        "túnica Hogwarts regalo oficial",
        "libro Harry Potter ilustrado regalo",
        "ajedrez mago Harry Potter",
        "mapa merodeador regalo",
        "giratiempo Hermione regalo",
        
        # Anime & Manga
        "figura anime premium regalo",
        "figura Dragon Ball Super",
        "figura One Piece regalo",
        "figura Naruto Shippuden",
        "figura Demon Slayer regalo",
        "figura Attack on Titan",
        "manga box set regalo",
        "poster anime metal regalo",
        "katana decorativa regalo",
        
        # Gaming Merchandise
        "figura Zelda regalo",
        "figura Pokemon regalo",
        "figura Final Fantasy regalo",
        "libro arte videojuegos regalo",
        "réplica espada videojuego",
        "camiseta gaming premium",
        "sudadera gaming regalo",
        
        # Juegos de Mesa Premium
        "Catan edición especial regalo",
        "ajedrez temático regalo premium",
        "Risk edición coleccionista",
        "Monopoly edición especial",
        "juego mesa estrategia premium",
        "Dungeons Dragons starter set",
        "cartas Magic gathering regalo",
        "cartas Pokemon regalo premium",
    ],
    
    # =========================================================================
    # ZEN - Wellness, Meditación, Relax, Spa
    # =========================================================================
    "Zen": [
        # Aromaterapia & Velas
        "difusor aceites esenciales regalo",
        "set aceites esenciales regalo premium",
        "vela aromática lujo regalo",
        "vela masaje regalo",
        "incienso japonés premium regalo",
        "palo santo premium regalo",
        "quemador incienso diseño",
        "lámpara sal himalaya regalo",
        
        # Meditación
        "cojín meditación zafu regalo",
        "banco meditación madera",
        "cuenco tibetano regalo",
        "campana tibetana meditación",
        "mala meditación piedras naturales",
        "app meditación suscripción regalo",
        "libro meditación regalo",
        
        # Yoga
        "esterilla yoga premium regalo",
        "bloque yoga corcho regalo",
        "correa yoga algodón",
        "rueda yoga regalo",
        "bolster yoga regalo",
        "manta yoga regalo",
        "leggings yoga regalo premium",
        
        # Masaje & Relajación
        "masajeador cervical regalo",
        "pistola masaje regalo",
        "rodillo masaje facial jade",
        "gua sha regalo jade",
        "almohadilla térmica regalo",
        "cojín masaje shiatsu regalo",
        "hamaca cervical regalo",
        "bola masaje pies regalo",
        
        # Spa en Casa
        "albornoz algodón egipcio regalo",
        "zapatillas spa regalo lujo",
        "set spa regalo premium",
        "sales baño regalo lujo",
        "bomba baño regalo set",
        "exfoliante corporal natural regalo",
        "mascarilla facial premium regalo",
        "aceite corporal regalo",
        
        # Sueño & Descanso
        "almohada viscoelástica regalo",
        "antifaz seda dormir regalo",
        "máquina ruido blanco regalo",
        "difusor dormitorio regalo",
        "spray almohada lavanda regalo",
        "luz despertador amanecer regalo",
        "weighted blanket manta pesada",
        
        # Té & Infusiones Relax
        "set té relax regalo",
        "infusiones relajantes regalo",
        "tetera cristal regalo",
        "taza térmica regalo",
    ],
    
    # =========================================================================
    # VIAJES - Aventura, Mochileros, Exploradores
    # =========================================================================
    "Viajes": [
        # Equipaje Premium
        "maleta cabina regalo premium",
        "maleta Samsonite regalo",
        "mochila viaje 40L regalo",
        "mochila antirrobo regalo",
        "neceser viaje organizador regalo",
        "organizadores maleta set regalo",
        "funda pasaporte piel regalo",
        "etiqueta maleta cuero regalo",
        
        # Comodidad Viaje
        "almohada viaje memory foam regalo",
        "antifaz viaje seda regalo",
        "tapones oídos viaje regalo",
        "manta viaje compacta regalo",
        "reposapiés avión regalo",
        "cojín lumbar viaje regalo",
        
        # Tecnología Viajero
        "adaptador universal viaje regalo",
        "powerbank 20000mah regalo",
        "cargador portátil solar regalo",
        "traductor instantáneo regalo",
        "wifi portátil internacional regalo",
        "rastreador maleta AirTag regalo",
        "kindle paperwhite regalo",
        "cámara viaje compacta regalo",
        
        # Outdoor & Aventura
        "tienda campaña ultraligera regalo",
        "saco dormir compacto regalo",
        "colchoneta inflable camping regalo",
        "linterna frontal regalo",
        "navaja suiza victorinox regalo",
        "filtro agua portátil regalo",
        "cocina camping gas regalo",
        "hamaca camping regalo",
        
        # Accesorios Viajero
        "botella agua plegable regalo",
        "toalla microfibra viaje regalo",
        "candado TSA regalo",
        "riñonera viaje antirrobo regalo",
        "gafas sol polarizadas viaje regalo",
        "sombrero viaje plegable regalo",
        
        # Experiencias & Guías
        "guía lonely planet regalo",
        "mapa scratch viajes regalo",
        "diario viaje cuero regalo",
        "libro fotografía viajes regalo",
        
        # Playa & Verano
        "toalla playa premium regalo",
        "nevera portátil playa regalo",
        "hamaca playa regalo",
        "altavoz bluetooth impermeable regalo",
        "gafas snorkel regalo",
        "cámara acuática regalo",
    ],
    
    # =========================================================================
    # DEPORTE - Fitness, Running, Outdoor
    # =========================================================================
    "Deporte": [
        # Fitness & Gym
        "mancuernas ajustables regalo",
        "kettlebell regalo fitness",
        "banda resistencia set regalo",
        "ab roller rueda abdominal regalo",
        "cuerda saltar profesional regalo",
        "step fitness regalo",
        "pelota ejercicio regalo",
        "TRX entrenamiento suspensión regalo",
        "foam roller masaje regalo",
        "pistola masaje muscular regalo",
        
        # Running
        "zapatillas running regalo premium",
        "reloj GPS running regalo",
        "cinturón running hidratación regalo",
        "auriculares deporte bluetooth regalo",
        "chaleco running reflectante regalo",
        "calcetines compresión running regalo",
        "gorra running transpirable regalo",
        "gafas sol deportivas regalo",
        
        # Ciclismo
        "casco ciclismo regalo",
        "luz bicicleta potente regalo",
        "guantes ciclismo regalo",
        "maillot ciclismo regalo",
        "culotte ciclismo regalo",
        "ciclocomputador GPS regalo",
        "candado bicicleta regalo",
        "herramientas bicicleta kit regalo",
        
        # Natación
        "gafas natación regalo",
        "gorro silicona natación regalo",
        "bañador competición regalo",
        "toalla natación microfibra regalo",
        "bolsa natación impermeable regalo",
        "reloj natación regalo",
        
        # Deportes Raqueta
        "raqueta padel regalo",
        "paletero padel regalo",
        "raqueta tenis regalo",
        "bolsa tenis regalo",
        "overgrip raqueta regalo",
        
        # Outdoor Sports
        "bastones trekking plegables regalo",
        "mochila hidratación trail regalo",
        "botas montaña regalo",
        "brújula profesional regalo",
        "prismáticos compactos regalo",
        "GPS montaña Garmin regalo",
        
        # Yoga & Pilates
        "esterilla yoga premium regalo",
        "bloque yoga corcho regalo",
        "aro pilates regalo",
        "pelota pilates regalo",
        "reformer pilates portátil regalo",
        
        # Recuperación
        "masajeador percusión regalo",
        "electroestimulador muscular regalo",
        "botas compresión recuperación regalo",
        "hielo gel recuperación regalo",
        "crema recuperación muscular regalo",
    ],
    
    # =========================================================================
    # MODA - Fashion, Accesorios, Joyería
    # =========================================================================
    "Moda": [
        # Relojes
        "reloj automatico regalo hombre",
        "reloj mujer regalo elegante",
        "reloj minimalista regalo",
        "smartwatch elegante regalo",
        "correa reloj cuero premium regalo",
        "caja relojes regalo",
        "reloj vintage regalo",
        
        # Gafas de Sol
        "gafas sol Ray-Ban regalo",
        "gafas sol polarizadas regalo premium",
        "gafas sol diseñador regalo",
        "funda gafas cuero regalo",
        
        # Bolsos & Carteras
        "bolso piel regalo mujer",
        "cartera piel regalo hombre",
        "mochila cuero regalo",
        "neceser piel regalo",
        "monedero diseñador regalo",
        "clutch fiesta regalo",
        "bandolera piel regalo",
        
        # Joyería
        "collar plata 925 regalo",
        "pulsera oro regalo",
        "pendientes diseño regalo",
        "anillo compromiso regalo",
        "gemelos camisa regalo hombre",
        "relicario foto regalo",
        "joyero organizador regalo",
        "pulsera personalizada regalo",
        
        # Cinturones & Accesorios
        "cinturón piel italiano regalo",
        "tirantes premium regalo",
        "corbata seda regalo",
        "pañuelo seda regalo",
        "fular cashmere regalo",
        "guantes piel regalo",
        
        # Calzado Premium
        "zapatillas limited edition regalo",
        "mocasines piel regalo",
        "botines cuero regalo",
        "sandalias diseñador regalo",
        "sneakers premium regalo",
        
        # Ropa Premium
        "camisa lino premium regalo",
        "jersey cashmere regalo",
        "chaqueta piel regalo",
        "abrigo lana regalo",
        "vestido diseñador regalo",
        "pijama seda regalo",
        "albornoz algodón egipcio regalo",
        
        # Fragancias
        "perfume nicho regalo",
        "colonia premium regalo hombre",
        "set perfume regalo mujer",
        "difusor hogar lujo regalo",
        "vela perfumada lujo regalo",
        
        # Cuidado Personal Premium
        "set afeitado premium regalo",
        "neceser viaje cuero regalo",
        "espejo aumento iluminado regalo",
        "set manicura premium regalo",
    ],
    
    # =========================================================================
    # HOGAR - Decoración, Casa, Diseño (NUEVA CATEGORÍA)
    # =========================================================================
    "Hogar": [
        # Decoración
        "cuadro decorativo moderno regalo",
        "espejo decorativo regalo",
        "jarrón diseño regalo",
        "escultura decorativa regalo",
        "reloj pared diseño regalo",
        "lámpara diseño regalo",
        "cojines decorativos set regalo",
        "manta decorativa regalo",
        
        # Plantas & Jardín
        "maceta diseño regalo",
        "kit bonsai regalo",
        "terrario plantas regalo",
        "jardín vertical interior regalo",
        "kit huerto urbano regalo",
        "herramientas jardín premium regalo",
        
        # Cocina Diseño
        "vajilla diseño regalo",
        "cristalería premium regalo",
        "cubertería acero inoxidable regalo",
        "juego ollas diseño regalo",
        "electrodoméstico retro regalo",
        "cafetera diseño regalo",
        "tostadora retro regalo",
        
        # Iluminación
        "lámpara mesa diseño regalo",
        "lámpara pie regalo",
        "vela LED diseño regalo",
        "guirnalda luces decorativa regalo",
        "neón personalizado regalo",
        
        # Textiles Hogar
        "sábanas algodón egipcio regalo",
        "edredón plumas regalo",
        "toallas algodón egipcio regalo",
        "alfombra diseño regalo",
        "cortinas terciopelo regalo",
    ],
    
    # =========================================================================
    # NIÑOS - Regalos para peques (NUEVA CATEGORÍA)
    # =========================================================================
    "Peques": [
        # Juguetes Educativos
        "juguete STEM regalo niño",
        "kit ciencia niños regalo",
        "microscopio niños regalo",
        "telescopio niños regalo",
        "robot programable niños regalo",
        "kit electrónica niños regalo",
        
        # LEGO & Construcción
        "LEGO Friends regalo",
        "LEGO City regalo",
        "LEGO Ninjago regalo",
        "LEGO Disney regalo",
        "Playmobil regalo",
        "Mega Construx regalo",
        
        # Juegos Creativos
        "set manualidades niños regalo",
        "kit pintura niños regalo",
        "plastilina Play-Doh regalo",
        "kit joyería niña regalo",
        "máquina coser niños regalo",
        "kit costura niños regalo",
        
        # Aire Libre
        "bicicleta niños regalo",
        "patinete niños regalo",
        "patines niños regalo",
        "tienda campaña niños regalo",
        "piscina hinchable regalo",
        "cometa niños regalo",
        
        # Peluches & Muñecos
        "peluche gigante regalo",
        "Squishmallow regalo",
        "muñeca regalo",
        "figura acción niños regalo",
        "marioneta regalo",
        
        # Libros Infantiles
        "libro infantil ilustrado regalo",
        "colección libros niños regalo",
        "libro interactivo niños regalo",
        "audiolibro niños regalo",
        
        # Tecnología Niños
        "tablet niños regalo",
        "cámara niños regalo",
        "reloj niños GPS regalo",
        "auriculares niños regalo",
        "karaoke niños regalo",
    ],
    
    # =========================================================================
    # PAREJAS - Regalos románticos (NUEVA CATEGORÍA)
    # =========================================================================
    "Parejas": [
        # Experiencias Románticas
        "cena romantica kit regalo",
        "spa pareja regalo",
        "escapada romantica regalo",
        "cata vinos pareja regalo",
        "clase cocina pareja regalo",
        
        # Joyería Pareja
        "anillo compromiso regalo",
        "pulsera pareja personalizada regalo",
        "collar corazón regalo",
        "colgante foto regalo",
        "alianzas regalo",
        
        # Personalizado
        "album fotos personalizado regalo",
        "cuadro personalizado pareja regalo",
        "estrella nombre regalo",
        "libro amor personalizado regalo",
        "puzzle foto pareja regalo",
        
        # Hogar Pareja
        "set desayuno cama regalo",
        "sábanas seda regalo",
        "vela masaje pareja regalo",
        "albornoz pareja set regalo",
        
        # Experiencias
        "vuelo globo regalo",
        "paseo barco regalo",
        "hotel romántico regalo",
        "picnic gourmet regalo",
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