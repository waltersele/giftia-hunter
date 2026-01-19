#!/usr/bin/env python3
"""
Test de Gemini para verificar generación de FICHA SEO COMPLETA v51.
Incluye: full_description (600-800 palabras), FAQs, expert_opinion, cons, etc.
"""

import sys
import json
import time

sys.path.insert(0, '.')

# Producto de prueba (solo 1 para ver toda la ficha completa)
TEST_PRODUCTS = [
    {
        'asin': 'B09XYZ1234',
        'title': 'Auriculares Bluetooth Sony WH-1000XM5 con Cancelación de Ruido Activa',
        'price': '349',
        'image_url': 'https://example.com/sony-headphones.jpg',
        'affiliate_url': 'https://www.amazon.es/dp/B09XYZ1234?tag=giftiaes-21',
        'rating': '4.7',
        'reviews_count': 15234,
        'category': 'Tech',
        'source': 'amazon'
    }
]

def count_words(text):
    """Cuenta palabras en un texto."""
    if not text:
        return 0
    return len(text.split())

def test_gemini_seo_v51():
    """Testea la generación de ficha SEO completa v51."""
    
    print("=" * 80)
    print("🧪 TEST: Ficha SEO Completa - GOLD MASTER v51")
    print("=" * 80)
    print()
    
    try:
        from process_queue import classify_batch_with_gemini
        print("✅ Módulos importados correctamente")
    except Exception as e:
        print(f"❌ Error importando: {e}")
        return
    
    print()
    print(f"📦 Enviando 1 producto a Gemini para análisis completo...")
    print()
    
    start_time = time.time()
    results = classify_batch_with_gemini(TEST_PRODUCTS)
    elapsed = time.time() - start_time
    
    print(f"⏱️ Tiempo de respuesta: {elapsed:.2f}s")
    print()
    
    if not results or not results[0]:
        print("❌ No se obtuvieron resultados de Gemini")
        return
    
    result = results[0]
    product = TEST_PRODUCTS[0]
    
    if not result.get('is_good_gift', False):
        print(f"❌ RECHAZADO - Quality: {result.get('gift_quality', 0)}/10")
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # MOSTRAR FICHA COMPLETA
    # ═══════════════════════════════════════════════════════════════════════
    
    print("=" * 80)
    print(f"📦 {product.get('title', 'N/A')[:60]}...")
    print(f"   💰 €{product.get('price')} | ⭐ {product.get('rating')} ({product.get('reviews_count')} reviews)")
    print("=" * 80)
    
    # ─────────────────────────────────────────────────────────────────────────
    # 📊 METADATOS SEO
    # ─────────────────────────────────────────────────────────────────────────
    print()
    print("┌" + "─" * 78 + "┐")
    print("│ 📊 METADATOS SEO (Google SERP)                                              │")
    print("└" + "─" * 78 + "┘")
    
    seo_title = result.get('seo_title', '')
    meta_desc = result.get('meta_description', '')
    
    print(f"\n🔍 SEO TITLE ({len(seo_title)} chars - objetivo: 50-60):")
    print(f"   {seo_title}")
    status = "✅" if 50 <= len(seo_title) <= 60 else "⚠️"
    print(f"   {status} {'Óptimo' if status == '✅' else 'Revisar longitud'}")
    
    print(f"\n📝 META DESCRIPTION ({len(meta_desc)} chars - objetivo: 150-160):")
    print(f"   {meta_desc}")
    status = "✅" if 150 <= len(meta_desc) <= 160 else "⚠️"
    print(f"   {status} {'Óptimo' if status == '✅' else 'Revisar longitud'}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 🏷️ TÍTULOS Y GANCHO
    # ─────────────────────────────────────────────────────────────────────────
    print()
    print("┌" + "─" * 78 + "┐")
    print("│ 🏷️ TÍTULOS Y GANCHO                                                         │")
    print("└" + "─" * 78 + "┘")
    
    h1 = result.get('h1_title', '')
    print(f"\n🎯 H1 TITLE ({len(h1)} chars - objetivo: 40-70):")
    print(f"   {h1}")
    
    short_desc = result.get('short_description', '')
    short_words = count_words(short_desc)
    print(f"\n📖 SHORT DESCRIPTION ({short_words} palabras - objetivo: 80-120):")
    print(f"   {short_desc}")
    status = "✅" if 80 <= short_words <= 120 else "⚠️"
    print(f"   {status} {'Óptimo' if status == '✅' else f'Revisar ({short_words} palabras)'}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # ⭐ SCORES
    # ─────────────────────────────────────────────────────────────────────────
    print()
    print("┌" + "─" * 78 + "┐")
    print("│ ⭐ VALORACIONES                                                              │")
    print("└" + "─" * 78 + "┘")
    
    print(f"\n   Giftia Score: {'⭐' * int(result.get('giftia_score', 0))} {result.get('giftia_score', 0)}/5")
    print(f"   Quality (interno): {result.get('gift_quality', 0)}/10")
    print(f"   Marketing Hook: {result.get('marketing_hook', 'N/A')}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 💬 OPINIÓN DEL EXPERTO
    # ─────────────────────────────────────────────────────────────────────────
    print()
    print("┌" + "─" * 78 + "┐")
    print("│ 💬 OPINIÓN DEL EXPERTO (E-E-A-T)                                            │")
    print("└" + "─" * 78 + "┘")
    
    expert = result.get('expert_opinion', '')
    expert_words = count_words(expert)
    print(f"\n({expert_words} palabras - objetivo: 100-150)")
    print()
    for line in expert.split('\n'):
        if line.strip():
            print(f"   {line}")
    status = "✅" if 100 <= expert_words <= 150 else "⚠️"
    print(f"\n   {status} {'Óptimo' if status == '✅' else f'Revisar ({expert_words} palabras)'}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # ✅ PROS Y ❌ CONTRAS
    # ─────────────────────────────────────────────────────────────────────────
    print()
    print("┌" + "─" * 78 + "┐")
    print("│ ✅ PROS Y ❌ CONTRAS                                                         │")
    print("└" + "─" * 78 + "┘")
    
    pros = result.get('pros', [])
    cons = result.get('cons', [])
    
    print(f"\n✅ PROS ({len(pros)} - objetivo: 5-6):")
    for p in pros:
        print(f"   • {p}")
    
    print(f"\n❌ CONTRAS ({len(cons)} - objetivo: 2-3):")
    for c in cons:
        print(f"   • {c}")
    
    status_pros = "✅" if 5 <= len(pros) <= 6 else "⚠️"
    status_cons = "✅" if 2 <= len(cons) <= 3 else "⚠️"
    print(f"\n   {status_pros} Pros: {'Óptimo' if status_pros == '✅' else 'Revisar cantidad'}")
    print(f"   {status_cons} Cons: {'Óptimo' if status_cons == '✅' else 'Revisar cantidad'}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 📝 DESCRIPCIÓN LARGA SEO
    # ─────────────────────────────────────────────────────────────────────────
    print()
    print("┌" + "─" * 78 + "┐")
    print("│ 📝 DESCRIPCIÓN LARGA SEO (posiciona la URL)                                 │")
    print("└" + "─" * 78 + "┘")
    
    full_desc = result.get('full_description', '')
    full_words = count_words(full_desc)
    
    print(f"\n({full_words} palabras - objetivo: 600-800)")
    print()
    
    # Mostrar con formato
    for line in full_desc.split('\n'):
        if line.strip():
            if line.startswith('##'):
                print(f"\n   {line}")
            else:
                print(f"   {line}")
    
    print()
    status = "✅" if 600 <= full_words <= 800 else "⚠️"
    print(f"   {status} {'Óptimo' if status == '✅' else f'Revisar ({full_words} palabras)'}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 👤 BUYER PERSONA
    # ─────────────────────────────────────────────────────────────────────────
    print()
    print("┌" + "─" * 78 + "┐")
    print("│ 👤 BUYER PERSONA (long tails)                                               │")
    print("└" + "─" * 78 + "┘")
    
    who = result.get('who_is_for', '')
    who_words = count_words(who)
    print(f"\n({who_words} palabras - objetivo: 80-100)")
    print(f"\n   {who}")
    status = "✅" if 80 <= who_words <= 100 else "⚠️"
    print(f"\n   {status} {'Óptimo' if status == '✅' else f'Revisar ({who_words} palabras)'}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # ❓ FAQs
    # ─────────────────────────────────────────────────────────────────────────
    print()
    print("┌" + "─" * 78 + "┐")
    print("│ ❓ FAQs (Featured Snippets)                                                 │")
    print("└" + "─" * 78 + "┘")
    
    faqs = result.get('faqs', [])
    print(f"\n({len(faqs)} preguntas - objetivo: 4-5)")
    
    for i, faq in enumerate(faqs, 1):
        q = faq.get('q', '') if isinstance(faq, dict) else ''
        a = faq.get('a', '') if isinstance(faq, dict) else ''
        print(f"\n   {i}. ❓ {q}")
        print(f"      💬 {a}")
    
    status = "✅" if 4 <= len(faqs) <= 5 else "⚠️"
    print(f"\n   {status} {'Óptimo' if status == '✅' else f'Revisar ({len(faqs)} FAQs)'}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 🏁 VEREDICTO
    # ─────────────────────────────────────────────────────────────────────────
    print()
    print("┌" + "─" * 78 + "┐")
    print("│ 🏁 VEREDICTO FINAL                                                          │")
    print("└" + "─" * 78 + "┘")
    
    verdict = result.get('verdict', '')
    verdict_words = count_words(verdict)
    print(f"\n({verdict_words} palabras - objetivo: 50-80)")
    print(f"\n   {verdict}")
    status = "✅" if 50 <= verdict_words <= 80 else "⚠️"
    print(f"\n   {status} {'Óptimo' if status == '✅' else f'Revisar ({verdict_words} palabras)'}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 📊 RESUMEN FINAL
    # ─────────────────────────────────────────────────────────────────────────
    print()
    print("=" * 80)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("=" * 80)
    
    checks = [
        ("seo_title", 50 <= len(seo_title) <= 65, f"{len(seo_title)} chars"),
        ("meta_description", 140 <= len(meta_desc) <= 165, f"{len(meta_desc)} chars"),
        ("h1_title", 35 <= len(h1) <= 75, f"{len(h1)} chars"),
        ("short_description", 40 <= short_words <= 120, f"{short_words} palabras"),
        ("expert_opinion", 60 <= expert_words <= 150, f"{expert_words} palabras"),
        ("pros", 4 <= len(pros) <= 6, f"{len(pros)} bullets"),
        ("cons", 2 <= len(cons) <= 4, f"{len(cons)} bullets"),
        ("full_description", 350 <= full_words <= 600, f"{full_words} palabras"),  # 400-500 es suficiente
        ("who_is_for", 40 <= who_words <= 120, f"{who_words} palabras"),
        ("faqs", 4 <= len(faqs) <= 6, f"{len(faqs)} preguntas"),
        ("verdict", 40 <= verdict_words <= 100, f"{verdict_words} palabras"),
        ("slug", len(result.get('slug', '')) > 0, result.get('slug', '')),
    ]
    
    passed = 0
    for name, ok, value in checks:
        status = "✅" if ok else "⚠️"
        if ok:
            passed += 1
        print(f"   {status} {name}: {value}")
    
    print()
    print(f"   📈 Score: {passed}/{len(checks)} campos óptimos")
    print()
    
    # Taxonomías
    print("📂 TAXONOMÍAS:")
    print(f"   Categoría: {result.get('category', 'N/A')}")
    print(f"   Edades: {result.get('ages', [])}")
    print(f"   Género: {result.get('gender', 'N/A')}")
    print(f"   Destinatarios: {result.get('recipients', [])}")
    print(f"   Ocasiones: {result.get('occasions', [])}")
    print(f"   Hook: {result.get('marketing_hook', 'N/A')}")
    print(f"   Slug: {result.get('seo_slug', 'N/A')}")
    print()

if __name__ == '__main__':
    test_gemini_seo_v51()
