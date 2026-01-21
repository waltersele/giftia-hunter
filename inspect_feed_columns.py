#!/usr/bin/env python3
"""
Script temporal para inspeccionar columnas reales de feeds Awin
"""
import os
import requests
import csv
import gzip
from io import StringIO
from dotenv import load_dotenv

load_dotenv()

def main():
    # 1. Get feedList
    print("📋 Obteniendo lista de feeds...")
    feedlist_url = os.getenv('AWIN_FEEDLIST_URL')
    response = requests.get(feedlist_url, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ Error obteniendo feedList: {response.status_code}")
        return
    
    lines = response.text.strip().split('\n')
    reader = csv.DictReader(lines)
    feeds = list(reader)
    
    # 2. Find first Sprinter feed (smaller, faster download)
    target_feed = None
    for feed in feeds:
        if feed['Advertiser ID'] == '27904':  # Sprinter
            target_feed = feed
            break
    
    if not target_feed:
        print("❌ No se encontró feed de Sprinter")
        return
    
    print(f"\n✅ Feed seleccionado:")
    print(f"   Merchant: {target_feed['Advertiser Name']}")
    print(f"   Feed: {target_feed['Feed Name']}")
    print(f"   Products: {target_feed['No of products']}")
    print(f"   Feed ID: {target_feed['Feed ID']}")
    
    # 3. Download and inspect first product
    print(f"\n📥 Descargando feed de productos...")
    feed_url = target_feed['URL']
    
    try:
        feed_response = requests.get(feed_url, timeout=60)
        if feed_response.status_code != 200:
            print(f"❌ Error descargando feed: {feed_response.status_code}")
            return
        
        # Decompress gzip
        decompressed = gzip.decompress(feed_response.content).decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(StringIO(decompressed))
        
        # Get first product
        first_product = next(csv_reader, None)
        
        if not first_product:
            print("❌ Feed vacío")
            return
        
        # Show all columns
        print(f"\n📊 COLUMNAS DEL FEED ({len(first_product.keys())} columnas):")
        print("="*80)
        
        columns = sorted(first_product.keys())
        for col in columns:
            value = first_product[col]
            # Truncate long values
            if len(str(value)) > 50:
                value = str(value)[:47] + "..."
            print(f"  • {col:30s} = {value}")
        
        print("\n" + "="*80)
        
        # Check for review/rating columns
        review_related = [col for col in columns if any(keyword in col.lower() for keyword in ['review', 'rating', 'star', 'score', 'opinion', 'valoracion'])]
        
        if review_related:
            print(f"\n✅ COLUMNAS DE REVIEWS/RATINGS ENCONTRADAS:")
            for col in review_related:
                print(f"   🎯 {col}")
        else:
            print(f"\n❌ NO SE ENCONTRARON COLUMNAS DE REVIEWS/RATINGS")
            print("   Columnas buscadas: review*, rating*, star*, score*, opinion*, valoracion*")
        
        # Show price-related columns
        price_related = [col for col in columns if any(keyword in col.lower() for keyword in ['price', 'precio'])]
        print(f"\n💰 Columnas de precio: {', '.join(price_related)}")
        
        # Show stock-related columns
        stock_related = [col for col in columns if any(keyword in col.lower() for keyword in ['stock', 'availability', 'disponib'])]
        print(f"📦 Columnas de stock: {', '.join(stock_related)}")
        
        # Show EAN columns
        ean_related = [col for col in columns if any(keyword in col.lower() for keyword in ['ean', 'gtin', 'barcode'])]
        print(f"🔢 Columnas de EAN: {', '.join(ean_related)}")
        
    except Exception as e:
        print(f"❌ Error procesando feed: {e}")

if __name__ == "__main__":
    main()
