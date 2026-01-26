import subprocess
import time
import sys

def run_pipeline():
    print("🚀 INICIANDO PIPELINE AUTOMÁTICO V52 (Modo Limpieza)")
    
    # 1. Ejecutar Hunter (Descarga y Filtrado)
    # Usamos limit=500 para traer un lote fresco de productos buenos
    print("\n📦 PASO 1: CAZANDO PRODUCTOS (Hunter)...")
    try:
        # Aseguramos que usamos el feed descargado anteriormente
        # Asumimos que feed_eci.csv es el bueno grande
        result = subprocess.run(
            ["python", "hunter_awin.py", "feed_eci.csv", "--limit", "500"], 
            check=True
        )
    except subprocess.CalledProcessError:
        print("❌ Error en Hunter. Abortando.")
        return

    # 2. Ejecutar Limpieza de Seguridad (Por si acaso se coló algo)
    print("\n🧹 PASO 2: LIMPIEZA DE SEGURIDAD...")
    try:
        subprocess.run(["python", "emergency_clean.py"], check=True)
    except subprocess.CalledProcessError:
         print("⚠️ Error en limpieza, continuando con precaución...")

    # 3. Ejecutar Procesador AI (Publicación)
    print("\n🧠 PASO 3: PROCESANDO CON GEMINI (Queue)...")
    try:
        subprocess.run(["python", "process_queue.py"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Error en Procesador.")
        return

if __name__ == "__main__":
    run_pipeline()
