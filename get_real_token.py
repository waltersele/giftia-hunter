#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get the real token from the server
"""
import requests
import re

urls = [
    "https://giftia.es/wp-content/plugins/giftfinder-core/verify.php",
    "https://giftia.es/wp-admin/admin.php?page=giftia-settings"
]

print("Buscando token en servidor...\n")

for url in urls:
    try:
        response = requests.get(url, verify=False, timeout=5)
        if response.status_code == 200:
            # Buscar tokens en formato común
            patterns = [
                r"WP_API_TOKEN[\'\":\s]+([a-zA-Z0-9]{32})",
                r"gf_wp_api_token[\'\":\s]+([a-zA-Z0-9]{32})",
                r"nu27OrX2t5VZQmrGXfoZ[a-zA-Z0-9]*",
                r"([a-zA-Z0-9]{32})"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        print(f"[{url}]")
                        print(f"  Token encontrado: {match}\n")
                        break
    except:
        pass

print("\nSi no encontró el token arriba, ve a:")
print("https://giftia.es/wp-admin/admin.php?page=giftia-settings")
print("\nBusca el campo 'Token de API (WP_API_TOKEN)' y copia el valor.")
