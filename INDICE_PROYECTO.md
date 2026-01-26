# 🗺️ ÍNDICE MAESTRO DEL PROYECTO (GIFTIA HUNTER)

> **REGLA DE ORO:** Este archivo es el mapa oficial del Hunter. Aquí se definen los pipelines de datos y la orquestación de IA. Mantener el orden es la prioridad #1.

---

## 🕷️ 1. RECOLECTORES (Ingesta)

Scripts responsables de traer datos crudos al sistema.

| Archivo | Rol | Fuente | Descripción |
|---------|-----|--------|-------------|
| **`hunter_amazon.py`** | 🕵️ **Scraper** | Amazon | Navegación real (Selenium) para capturar ASINs, precios y detalles. |
| **`hunter_awin.py`** | 📥 **Ingestor** | Feeds (CSV) | Procesa feeds masivos de Awin, normaliza datos y genera IDs (`AWIN00...`). |

---

## 🧠 2. CEREBRO (Procesamiento AI)

Donde ocurre la magia de Gemini.

| Archivo | Rol | Descripción |
|---------|-----|-------------|
| **`process_queue.py`** | ⚡ **Orquestador** | Lee `pending_products.json`. Gestiona lotes (Batch), rate-limits y prompt engineering con Gemini v2 Flash. Envía a WP. |
| **`giftia_schema.json`** | 📜 **LEY** | **SINGLE SOURCE OF TRUTH**. Define todas las categorías, tags, edades y estructuras de datos permitidas. |

---

## 🗄️ 3. ALMACENAMIENTO (Estado)

Archivos JSON que mantienen el estado de los datos en tránsito.

| Archivo | Rol | Descripción |
|---------|-----|-------------|
| **`pending_products.json`** | ⏳ **Cola** | Buffer de entrada. Los Hunters escriben aquí, `process_queue` lee de aquí. |
| **`processed_products.json`** | 📝 **Log** | Historial de éxito/error. Usado para debug y evitar re-procesamiento infinito. |
| **`published_inventory.json`** | 📦 **Inventario** | (Opcional/Legacy) Caché local de lo que ya está en WordPress. |

---

## 🛠️ 4. HERRAMIENTAS Y MANTENIMIENTO

Scripts de utilidad para tareas específicas.

| Archivo | Descripción |
|---------|-------------|
| **`fix_seo_today.py`** | Reprocesamiento forzado de SEO para productos específicos. |
| **`check_wp_status.py`** | Verific health-check o estado de la API de WordPress. |
| **`test_*.py`** | Scripts de pruebas unitarias o de integración (e.g., `test_e2e_complete.py`). |

---

## 📚 5. DOCUMENTACIÓN Y CONTEXTO

| Archivo | Descripción |
|---------|-------------|
| **`ESTADO_ACTUAL.md`** | **Bitácora**. Versión actual del Hunter (v12). |
| **`.github/copilot-instructions.md`** | **Contexto AI**. Reglas del asistente. |
| **`.env`** | **Secretos**. Keys de Gemini/WP (NO SUBIR A GIT). |

---

## ⚡ PROTOCOLO DE MODIFICACIÓN

1. **Flujo de Datos Unidireccional:**
   - Hunter (`.py`) → `pending_products.json` → Process (`.py`) → WordPress API.
   - **Nunca** modifiques este flujo sin actualizar este diagrama.

2. **Schema Intocable:**
   - Si necesitas una nueva categoría o tag, **primero** edita `giftia_schema.json`.
   - Luego actualiza los scripts que dependen de él.

3. **Orden:**
   - Si creas un script nuevo (ej. `hunter_ebay.py`), añádelo a la sección **1. RECOLECTORES**.

---
*Última actualización: 24 Enero 2026 - Hunter v12*
