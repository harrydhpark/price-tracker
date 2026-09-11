import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/raw_currys_samsung.json', 'r', encoding='utf-8') as f:
    sams = json.load(f)
with open('data/raw_currys_lg.json', 'r', encoding='utf-8') as f:
    lgs = json.load(f)

print('=== SAMSUNG CURRYS LOW PRICES / JUNK ===')
for it in sams:
    p = it.get('price', 0)
    mc = it.get('model_code', '')
    disp = it.get('display', '')
    sz = it.get('size', 0)
    tt = it.get('title', '')
    if p < 500 or mc in ['MONTH', 'CLAIM', 'TRADE', 'STARS', 'SAMSUNG', 'Unknown']:
        print(f'{mc:<16} | {disp:<10} | {sz} inch | £{p:>7.2f} | {tt}')

print('\n=== LG CURRYS LOW PRICES / JUNK ===')
for it in lgs:
    p = it.get('price', 0)
    mc = it.get('model_code', '')
    disp = it.get('display', '')
    sz = it.get('size', 0)
    tt = it.get('title', '')
    if p < 500 or mc in ['MONTH', 'CLAIM', 'TRADE', 'STARS', 'LG', 'Unknown'] or 'OLED' in mc or 'MRGB' in mc:
        print(f'{mc:<16} | {disp:<10} | {sz} inch | £{p:>7.2f} | {tt}')
