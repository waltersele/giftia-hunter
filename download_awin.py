import requests
import gzip
import shutil
import os
import sys

URL = "https://productdata.awin.com/datafeed/download/apikey/04bfc9f4d3229d8a86efab4488948c02/language/es/fid/33801,33803/rid/0/hasEnhancedFeeds/0/columns/aw_deep_link,product_name,aw_product_id,merchant_product_id,merchant_image_url,description,merchant_category,search_price,merchant_name,merchant_id,category_name,category_id,aw_image_url,currency,store_price,delivery_cost,merchant_deep_link,language,last_updated,display_price,data_feed_id,brand_name,brand_id,colour,product_short_description,specifications,condition,product_model,model_number,dimensions,keywords,promotional_text,product_type,commission_group,merchant_product_category_path,merchant_product_second_category,merchant_product_third_category,rrp_price,saving,savings_percent,base_price,base_price_amount,base_price_text,product_price_old,delivery_restrictions,delivery_weight,warranty,terms_of_contract,delivery_time,in_stock,stock_quantity,valid_from,valid_to,is_for_sale,web_offer,pre_order,stock_status,size_stock_status,size_stock_amount,merchant_thumb_url,large_image,alternate_image,aw_thumb_url,alternate_image_two,alternate_image_three,alternate_image_four,reviews,average_rating,rating,number_available,ean,isbn,upc,mpn,parent_product_id,product_GTIN,basket_link/format/csv/delimiter/%2C/compression/gzip/adultcontent/1/"

OUTPUT_GZ = "feed_eci.csv.gz"
OUTPUT_CSV = "feed_eci.csv"

def download_and_extract():
    print(f"⬇️ Iniciando descarga de feed Awin (Stream)...")
    try:
        response = requests.get(URL, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(OUTPUT_GZ, 'wb') as f:
            for i, chunk in enumerate(response.iter_content(chunk_size=1024*1024)): # 1MB chunks
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    mb = downloaded / (1024*1024)
                    print(f"   ⏳ Descargados: {mb:.2f} MB", end='\r')
                    
                    # SAFETY LIMIT: Cortamos a 350MB para intentar ver categorías Tech/Gamer
                    if mb > 350: 
                        print("\n🛑 Límite de seguridad alcanzado (350MB). Parando descarga para proteger sistema.")
                        break
        
        print(f"\n✅ Descarga parcial completada: {OUTPUT_GZ}")
        
        print(f"📦 Descomprimiendo stream...")
        with gzip.open(OUTPUT_GZ, 'rb') as f_in:
            with open(OUTPUT_CSV, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        print(f"✅ Descompresión exitosa: {OUTPUT_CSV}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    download_and_extract()
