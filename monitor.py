#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor Hunter.py progress
"""
import os
import time
from pathlib import Path

log_file = Path("d:\\HunterScrap\\hunter.log")

print("Monitoreando Hunter.py progress...\n")
print("="*70)

last_pos = 0
while True:
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(last_pos)
            new_lines = f.readlines()
            last_pos = f.tell()
            
            for line in new_lines:
                # Mostrar líneas importantes
                if any(x in line for x in ['ENVIANDO', 'OK:', 'Error', 'Found', 'INICIANDO', 'Selected']):
                    print(line.rstrip())
    
    time.sleep(2)
