# 🚀 GIFTIA HUNTER - Estado Actual

**Fecha:** 25 Enero 2026  
**Versión:** v12 (Multi-Vendor Supported)  
**Estado:** ✅ Operativo

Este es el único archivo de estado vivo. No hay otros resúmenes paralelos.

---

## ✅ CAMBIOS RECIENTES (últimas 24h)

- Hunter: añadidos checkers y scripts de corrección/reproceso (`check_*`, `fix_seo_today.py`, `fix_massive_seo.py`, `reprocess_products.py`, `patch_hunter.py`, `patch_shipping.py`), nuevos tests de Gemini SEO/ingestión y se incorporó `feed_eci.csv.gz` para pruebas multi-vendor.
- Core WP: [templates/single-gf_gift.php](templates/single-gf_gift.php) ahora muestra CTAs multi-oferta, badge de entrega, pill de “mejor oferta”, tabla de otras ofertas, UI de pros/cons y shipping; se añadieron docs [ESTADO_PROYECTO_V52.md](ESTADO_PROYECTO_V52.md) e [INDICE_PROYECTO.md](INDICE_PROYECTO.md); scripts de mantenimiento (flush-v52.php, emergency-purge.php) y prototipos legacy en `_deprecated/`.
- No se han consolidado ni revertido cambios tras el listado de diffs; pendiente decidir qué pasa a rama estable.

---

## 🏗️ ARQUITECTURA DE PIPELINE

```
                         [Fuente 1: Amazon] 
                                 │
                                 ▼
                          hunter_amazon.py
                                 │
[Fuente 2: Awin] ──▶ hunter_awin.py ──┼──▶ pending_products.json
                                      │
                                      ▼
                               process_queue.py (Gemini AI)
                                      │
                                      ▼
                               WordPress API (api-ingest.php)
```

### Archivos Clave

| Archivo | Función | Estado |
|---------|---------|--------|
| `hunter_awin.py` | Ingesta feed Awin + ID patching | ✅ Activo |
| `hunter.py` | Scraper Amazon (Selenium) | ✅ Estable |
| `process_queue.py` | Orquestador IA + envío WP | ✅ v52 ajustado |
| `giftia_schema.json` | FUENTE ÚNICA DE VERDAD (categorías/taxonomías) | ✅ Master |

---

## ⚙️ CONFIGURACIÓN

- Entorno: `.env` (gitignored)
- API Keys: Gemini + WordPress Token
- Logs: `processed_products.json` mantiene historial de éxito/error

---

## 📝 NOTAS DE OPERACIÓN
- Ingesta Awin: `python hunter_awin.py feed.csv`
- Procesar cola con IA: `python process_queue.py`
- Reprocesos/correcciones: usar scripts `fix_*` / `reprocess_*` según el caso

---

## 📖 DOCUMENTACIÓN ÚNICA

- README general: `README.md`
- Schema central: `giftia_schema.json`
