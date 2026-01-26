#!/usr/bin/env python3
"""
Verificar calidad de datos de Gemini
"""
import json

with open('processed_products.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filtrar publicados
published = [p for p in data if p.get('ai_result', {}).get('status') == 'published']
rejected = [p for p in data if p.get('ai_result', {}).get('status') == 'rejected']

print(f"═══════════════════════════════════════════")
print(f"📊 ESTADÍSTICAS DE GEMINI")
print(f"═══════════════════════════════════════════")
print(f"✅ Publicados: {len(published)}")
print(f"❌ Rechazados: {len(rejected)}")
print(f"📈 Tasa aprobación: {len(published)/(len(published)+len(rejected))*100:.1f}%")

# Estadísticas de calidad
qualities = [p.get('gift_quality', 0) for p in published if p.get('gift_quality')]
if qualities:
    print(f"\n📊 CALIDAD (gift_quality):")
    print(f"   Promedio: {sum(qualities)/len(qualities):.1f}/10")
    print(f"   Mínimo: {min(qualities)}/10")
    print(f"   Máximo: {max(qualities)}/10")

# Ratings
ratings = [p.get('rating_value', 0) for p in published if p.get('rating_value', 0) > 0]
if ratings:
    print(f"\n⭐ RATING AMAZON:")
    print(f"   Promedio: {sum(ratings)/len(ratings):.2f}/5")
    print(f"   Mínimo: {min(ratings):.1f}/5")
    print(f"   Máximo: {max(ratings):.1f}/5")

# Reviews
reviews = [p.get('review_count', 0) for p in published if p.get('review_count', 0) > 0]
if reviews:
    print(f"\n💬 REVIEWS:")
    print(f"   Promedio: {sum(reviews)/len(reviews):.0f}")
    print(f"   Mínimo: {min(reviews)}")
    print(f"   Máximo: {max(reviews)}")

# Categorías
categories = {}
for p in published:
    cat = p.get('gemini_category', 'N/A')
    categories[cat] = categories.get(cat, 0) + 1

print(f"\n📦 CATEGORÍAS:")
for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f"   {cat}: {count}")

# Motivos de rechazo
print(f"\n❌ MOTIVOS DE RECHAZO:")
rejection_reasons = {}
for p in rejected:
    reason = p.get('ai_result', {}).get('reason', 'desconocido')
    rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
for reason, count in sorted(rejection_reasons.items(), key=lambda x: -x[1]):
    print(f"   {reason}: {count}")

# Verificar campos SEO completos
print(f"\n📝 CAMPOS SEO (últimos 10 publicados):")
fields_check = ['short_description', 'expert_opinion', 'pros', 'full_description', 'verdict', 'faqs']
for p in published[-10:]:
    title = p.get('title', '')[:40]
    missing = []
    for field in fields_check:
        val = p.get(field)
        if not val or (isinstance(val, list) and len(val) == 0):
            missing.append(field)
    if missing:
        print(f"   ⚠️ {title}... falta: {', '.join(missing)}")
    else:
        print(f"   ✅ {title}... COMPLETO")

# Mostrar un producto ejemplo completo
print(f"\n═══════════════════════════════════════════")
print(f"📋 EJEMPLO DE PRODUCTO COMPLETO")
print(f"═══════════════════════════════════════════")
if published:
    p = published[-1]
    print(f"Título: {p.get('title', '')[:70]}")
    print(f"Rating: {p.get('rating_value', 0)}⭐ | Reviews: {p.get('review_count', 0)}")
    print(f"Categoría: {p.get('gemini_category', 'N/A')} | Quality: {p.get('gift_quality', 0)}/10")
    print(f"\n📌 Short description:")
    print(f"   {p.get('short_description', 'N/A')[:200]}")
    print(f"\n💡 Expert opinion:")
    print(f"   {p.get('expert_opinion', 'N/A')[:200]}")
    print(f"\n✅ Pros: {p.get('pros', [])[:3]}")
    print(f"\n❌ Cons: {p.get('cons', [])[:2]}")
    print(f"\n🎯 Verdict:")
    print(f"   {p.get('verdict', 'N/A')[:150]}")
