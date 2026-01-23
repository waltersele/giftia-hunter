import sys
sys.path.insert(0, 'd:/giftia-hunter')

from hunter_awin_smart import is_target_category

# Test fundas (deberían ser rechazadas)
tests = [
    ("Funda antigolpes iPhone 14", "Electrónica"),
    ("Carcasa protectora iPad", "Electrónica"),
    ("Alfombrilla gaming RGB", "Electrónica"),
    ("Mando inalámbrico Xbox", "Electrónica"),
    ("Auriculares Bluetooth", "Audio"),
]

for title, cat in tests:
    result = is_target_category(title, cat)
    print(f"{'✅' if not result and ('funda' in title.lower() or 'carcasa' in title.lower() or 'alfombrilla' in title.lower()) else '❌' if result and ('funda' in title.lower() or 'carcasa' in title.lower() or 'alfombrilla' in title.lower()) else '✅'} {title[:40]:45} → {result}")
