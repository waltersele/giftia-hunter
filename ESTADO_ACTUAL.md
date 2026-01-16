# 🚀 GIFTIA - Estado Actual y Próximos Pasos

**Fecha:** 16 Enero 2026  
**Sesión:** Mañana

---

## ✅ COMPLETADO HOY

### 1. Corrección de Bugs
- ✅ Cambiado icono `fa-house-chimney-heart` → `fa-people-roof` (no existía en FA Free)
- ✅ Movido JavaScript a archivo externo `giftia-app.js` (soluciona SyntaxError)
- ✅ Añadido `window.` prefix a todas las funciones onclick
- ✅ Filtro de alcohol expandido con más términos en español
- ✅ Restricciones de edad en vibes (min_age por categoría)

### 2. Limpieza y Documentación
- ✅ Eliminada documentación dispersa (10+ archivos .md)
- ✅ Eliminados archivos legacy/backup del plugin
- ✅ Eliminados scripts de fix temporales del Hunter
- ✅ Creado README.md exhaustivo en plugin
- ✅ Creado README.md exhaustivo en Hunter

### 3. Archivos Activos Actuales

**Plugin (c:\webproject\giftia\giftfinder-core\):**
```
giftfinder-core.php     # Core del plugin
frontend-ui-v4.php      # UI actual (JS externo)
giftia-app.js           # JavaScript
api-recommend.php       # API Gemini
install.php             # Tablas DB
admin-settings.php      # Panel admin
config/giftia-config.php
includes/env-loader.php
includes/giftia-utils.php
README.md               # Documentación completa
```

**Hunter (D:\giftia-hunter-clean\):**
```
hunter.py               # Scraper principal
.env                    # Configuración
requirements.txt        # Dependencias
README.md               # Documentación completa
```

---

## ❌ PENDIENTE - BUG CRÍTICO

### Feed de Resultados Roto

**Síntoma:** Cuando llegan los resultados de Gemini, se muestran con:
- Espacios blancos en laterales
- Elementos descuadrados
- CSS no cubre toda la pantalla

**Archivos afectados:**
- `frontend-ui-v4.php` → Sección CSS `#gf-feed`
- `giftia-app.js` → Función `gfRenderFeed()`

**Lo que ya intentamos:**
- Añadir `!important` a todos los estilos del feed
- Usar selectores más específicos (`#gf-feed .gf-feed-item`)
- Mover feed al body con JavaScript

**Próximas soluciones a intentar:**
1. Inspeccionar con DevTools qué estilos de WordPress sobrescriben
2. Añadir `all: unset` al contenedor del feed
3. Usar iframe aislado para el feed
4. Usar Shadow DOM para encapsular estilos

---

## 📂 ESTRUCTURA DE WORKSPACES

```
C:\webproject\giftia\giftfinder-core\   ← Plugin WordPress (ACTIVO)
D:\giftia-hunter-clean\                  ← Hunter Python (ACTIVO)
D:\HunterScrap\                          ← IGNORAR (copia corrupta)
```

---

## 🔑 CREDENCIALES Y CONFIGURACIÓN

**Servidor:**
- URL: https://giftia.es
- IP: 51.68.67.38
- Usuario SSH: giftia

**API Token (para Hunter):**
- Variable: `WP_API_TOKEN`
- Valor: `nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5`

**Amazon Affiliate:**
- Tag: `GIFTIA-21`

**Gemini API:**
- Configurar en WP Admin → Ajustes → Giftia

---

## 📋 PARA CONTINUAR EN CASA

1. **Subir archivos al servidor:**
   - `frontend-ui-v4.php`
   - `giftia-app.js`
   - `giftfinder-core.php`

2. **Debuggear feed de resultados:**
   - Abrir https://giftia.es
   - Completar perfilador hasta resultados
   - Abrir DevTools (F12) → Inspeccionar `#gf-feed`
   - Ver qué estilos de WordPress sobrescriben

3. **Posible solución rápida:**
   Añadir al CSS del feed:
   ```css
   #gf-feed, #gf-feed * {
       all: revert !important;
   }
   #gf-feed {
       /* re-aplicar estilos después del reset */
   }
   ```

---

## 📖 DOCUMENTACIÓN COMPLETA

- **Plugin:** `c:\webproject\giftia\giftfinder-core\README.md`
- **Hunter:** `D:\giftia-hunter-clean\README.md`

Ambos README tienen documentación exhaustiva de cada función, flujo y configuración.
