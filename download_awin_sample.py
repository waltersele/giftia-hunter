import requests
import gzip
import csv
import sys
import shutil

URL = "https://productdata.awin.com/datafeed/download/apikey/04bfc9f4d3229d8a86efab4488948c02/language/es/fid/33801,33803/rid/0/hasEnhancedFeeds/0/columns/aw_deep_link,product_name,aw_product_id,merchant_product_id,merchant_image_url,description,merchant_category,search_price,merchant_name,merchant_id,category_name,category_id,aw_image_url,currency,store_price,delivery_cost,merchant_deep_link,language,last_updated,display_price,data_feed_id,brand_name,brand_id,colour,product_short_description,specifications,condition,product_model,model_number,dimensions,keywords,promotional_text,product_type,commission_group,merchant_product_category_path,merchant_product_second_category,merchant_product_third_category,rrp_price,saving,savings_percent,base_price,base_price_amount,base_price_text,product_price_old,delivery_restrictions,delivery_weight,warranty,terms_of_contract,delivery_time,in_stock,stock_quantity,valid_from,valid_to,is_for_sale,web_offer,pre_order,stock_status,size_stock_status,size_stock_amount,merchant_thumb_url,large_image,alternate_image,aw_thumb_url,alternate_image_two,alternate_image_three,alternate_image_four,reviews,average_rating,rating,number_available,ean,isbn,upc,mpn,parent_product_id,product_GTIN,basket_link/format/csv/delimiter/%2C/compression/gzip/adultcontent/1/"

OUTPUT_FILE = "feed_eci_sample.csv"
LIMIT_ROWS = 2000

def download_sample():
    print(f"⬇️ Conectando a Awin para extraer muestra de {LIMIT_ROWS} productos...")
    
    try:
        # stream=True mantiene la conexión abierta sin bajar todo
        response = requests.get(URL, stream=True)
        response.raise_for_status()
        
        # Usamos gzip.open sobre el raw stream
        # response.raw es un file-like object binario
        with gzip.open(response.raw, mode='rt', encoding='utf-8', errors='ignore') as f_in:
            reader = csv.reader(f_in)
            
            with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f_out:
                writer = csv.writer(f_out)
                
                count = 0
                for row in reader:
                    writer.writerow(row)
                    count += 1
                    
                    if count % 100 == 0:
                         print(f"   ⏳ Extraídos: {count} filas...", end='\r')
                    
                    if count >= LIMIT_ROWS:
                        break
                        
        print(f"\n✅ Muestra lista: {OUTPUT_FILE} ({count} filas)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    download_sample()
