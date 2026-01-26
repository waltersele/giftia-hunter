import json
import os

pending_file = 'c:/Users/Walter/Projects/giftia-hunter/pending_products.json'
processed_file = 'c:/Users/Walter/Projects/giftia-hunter/processed_products.json'

report = []

if os.path.exists(pending_file):
    try:
        with open(pending_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            report.append(f"PENDING: {len(data)}")
    except:
        report.append("PENDING: Error reading")
else:
    report.append("PENDING: File not found")

if os.path.exists(processed_file):
    try:
        with open(processed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            report.append(f"PROCESSED: {len(data)}")
    except:
        report.append("PROCESSED: Error reading")
else:
    report.append("PROCESSED: File not found")

with open('c:/Users/Walter/Projects/giftia-hunter/status_report_temp.txt', 'w') as f:
    f.write('\n'.join(report))
