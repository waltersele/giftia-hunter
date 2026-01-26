#!/usr/bin/env python3
"""
Test directo API - verificar que campos SEO se guardan
"""

import requests
import json

# Test payload con todos los campos SEO v51
test_payload = {
    "asin": "B0FPCMSNJC",
    "price": "49.99",
    "title": "Test SEO Update",
    "update_existing": True,
    
    # Clasificación completa según schema
    "category": "Gourmet",
    "target_gender": "unisex", 
    "ages": ["adultos", "seniors"],
    "recipients": ["pareja", "padre", "amigo"],
    "occasions": ["cumpleanos", "sin-motivo"],
    "marketing_hook": "core",
    "gift_quality": 8,
    
    # Campos SEO v51 de prueba
    "seo_title": "Termómetro Inteligente para Carnes - Precisión Perfecta",
    "meta_description": "Descubre el termómetro inteligente que revoluciona tu cocina. Carnes perfectas cada vez con tecnología de precisión avanzada.",
    "h1_title": "Termómetro Inteligente: Tu Chef Personal",
    "short_description": "Termómetro inteligente para carnes que garantiza resultados perfectos en cada cocción. Con sensores de alta precisión y conectividad Bluetooth, nunca más tendrás carnes pasadas o crudas.",
    "expert_opinion": "Este termómetro inteligente representa un salto tecnológico en la cocina moderna. Su precisión excepcional y facilidad de uso lo convierten en una herramienta indispensable para cualquier amante de la cocina.",
    "pros": [
        "Precisión excepcional en cada medición",
        "Conectividad Bluetooth para monitoreo remoto", 
        "Diseño ergonómico y fácil de usar",
        "Compatible con múltiples tipos de carne",
        "Aplicación intuitiva con recetas incluidas"
    ],
    "cons": [
        "Requiere recarga periódica de batería",
        "Precio superior a termómetros básicos"
    ],
    "full_description": "El termómetro inteligente para carnes representa la evolución natural de la cocina doméstica. Con sensores de alta precisión y conectividad avanzada, este dispositivo garantiza resultados perfectos en cada cocción. Su diseño ergonómico facilita el uso, mientras que la aplicación móvil proporciona recetas y guías paso a paso.",
    "who_is_for": "Ideal para entusiastas de la cocina que buscan precisión profesional en casa. Perfecto para familias que disfrutan de carnes perfectamente cocidas y chefs aficionados que quieren elevar su nivel culinario.",
    "faqs": [
        {"question": "¿Es fácil de usar?", "answer": "Sí, su diseño intuitivo permite uso inmediato sin complicaciones."},
        {"question": "¿Funciona con todos los tipos de carne?", "answer": "Sí, está optimizado para res, cerdo, pollo, pescado y más."},
        {"question": "¿Necesita app móvil?", "answer": "No es obligatoria, pero la app mejora significativamente la experiencia."},
        {"question": "¿Vale la pena la inversión?", "answer": "Absolutamente, la precisión y comodidad justifican completamente el precio."}
    ],
    "verdict": "Una inversión inteligente para cualquier cocina moderna que busque precisión profesional y resultados consistentes.",
    "seo_slug": "termometro-inteligente-carnes-perfectas"
}

def test_api_direct():
    print("🧪 TEST: API directo con campos SEO v51")
    print("="*50)
    
    headers = {
        'Content-Type': 'application/json',
        'X-GIFTIA-TOKEN': 'nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5'
    }
    
    url = "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php"
    
    print(f"📤 Enviando datos a API...")
    print(f"   URL: {url}")
    print(f"   ASIN: {test_payload['asin']}")
    print(f"   Campos SEO: {len([k for k in test_payload.keys() if k.startswith(('seo_', 'h1_', 'meta_', 'short_', 'expert_', 'pros', 'cons', 'full_', 'who_', 'faqs', 'verdict'))])} campos")
    
    try:
        response = requests.post(
            url,
            data=json.dumps(test_payload, ensure_ascii=False).encode('utf-8'),
            headers=headers,
            timeout=30
        )
        
        print(f"\n📥 Respuesta de API:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:300]}...")
        
        if response.status_code == 200:
            print(f"\n✅ API respondió correctamente")
        else:
            print(f"\n❌ Error en API: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Error de conexión: {e}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    test_api_direct()