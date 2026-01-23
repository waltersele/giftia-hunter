#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tracking de productos ya procesados para evitar duplicados y pérdida de tiempo
"""
import json
import os
from datetime import datetime

TRACKING_FILE = "productos_procesados_tracking.json"

def load_tracking():
    """Carga el registro de productos ya procesados"""
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"productos": {}, "categorias_rechazadas": {}}

def save_tracking(tracking):
    """Guarda el registro"""
    with open(TRACKING_FILE, "w", encoding="utf-8") as f:
        json.dump(tracking, f, indent=2, ensure_ascii=False)

def mark_processed(ean, status, title="", category=""):
    """Marca un producto como procesado
    
    Args:
        ean: Identificador único del producto
        status: 'published', 'rejected', 'error'
        title: Título del producto
        category: Categoría del producto
    """
    tracking = load_tracking()
    
    tracking["productos"][ean] = {
        "status": status,
        "title": title[:50],
        "category": category,
        "timestamp": datetime.now().isoformat()
    }
    
    # Si fue rechazado, contar categoría
    if status == "rejected" and category:
        if category not in tracking["categorias_rechazadas"]:
            tracking["categorias_rechazadas"][category] = 0
        tracking["categorias_rechazadas"][category] += 1
    
    save_tracking(tracking)

def is_already_processed(ean):
    """Verifica si un producto ya fue procesado"""
    tracking = load_tracking()
    return ean in tracking["productos"]

def get_rejected_categories():
    """Retorna categorías que Gemini rechaza frecuentemente"""
    tracking = load_tracking()
    cats = tracking.get("categorias_rechazadas", {})
    # Categorías con >10 rechazos
    return [cat for cat, count in cats.items() if count > 10]

def get_stats():
    """Estadísticas del tracking"""
    tracking = load_tracking()
    productos = tracking["productos"]
    
    stats = {
        "total": len(productos),
        "published": len([p for p in productos.values() if p["status"] == "published"]),
        "rejected": len([p for p in productos.values() if p["status"] == "rejected"]),
        "error": len([p for p in productos.values() if p["status"] == "error"])
    }
    
    return stats

if __name__ == "__main__":
    stats = get_stats()
    print(f"Productos procesados: {stats['total']}")
    print(f"  ✓ Publicados: {stats['published']}")
    print(f"  ✗ Rechazados: {stats['rejected']}")
    print(f"  ⚠ Errores: {stats['error']}")
    
    rejected = get_rejected_categories()
    if rejected:
        print(f"\nCategorías rechazadas frecuentemente:")
        for cat in rejected[:10]:
            print(f"  - {cat}")
