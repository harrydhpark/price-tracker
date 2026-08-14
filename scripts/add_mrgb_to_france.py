# -*- coding: utf-8 -*-
import json, os, sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. Update france_master_urls.json with Micro RGB items
master_file = 'data/france_master_urls.json'
with open(master_file, 'r', encoding='utf-8') as f:
    master_data = json.load(f)

samsung_mrgb = [
    {
        "name": "TV LED Samsung Micro RGB TMR65R95H 165 cm 2026",
        "title": "TV LED Samsung Micro RGB TMR65R95H 165 cm 2026",
        "url": "https://www.fnac.com/TV-LED-Samsung-Micro-RGB-TMR65R95H-165-cm-2026/a22999892/w-4",
        "price": 3499.0,
        "promo": "None"
    },
    {
        "name": "TV LED Samsung Micro RGB TMR75R95H 190 cm 2026",
        "title": "TV LED Samsung Micro RGB TMR75R95H 190 cm 2026",
        "url": "https://www.fnac.com/TV-LED-Samsung-Micro-RGB-TMR75R95H-190-cm-2026/a22999919/w-4",
        "price": 4299.0,
        "promo": "None"
    },
    {
        "name": "TV LED Samsung Micro RGB TMR85R95H 216 cm 2026",
        "title": "TV LED Samsung Micro RGB TMR85R95H 216 cm 2026",
        "url": "https://www.fnac.com/TV-LED-Samsung-Micro-RGB-TMR85R95H-216-cm-2026/a22999893/w-4",
        "price": 6199.0,
        "promo": "None"
    },
    {
        "name": "TV LED Samsung Micro RGB TMR55R85H 140 cm 2026",
        "title": "TV LED Samsung Micro RGB TMR55R85H 140 cm 2026",
        "url": "https://www.fnac.com/TV-LED-Samsung-Micro-RGB-TMR55R85H-140-cm-2026/a22999884/w-4",
        "price": 1299.0,
        "promo": "None"
    },
    {
        "name": "TV LED Samsung Micro RGB TMR65R85H 165 cm 2026",
        "title": "TV LED Samsung Micro RGB TMR65R85H 165 cm 2026",
        "url": "https://www.fnac.com/TV-LED-Samsung-Micro-RGB-TMR65R85H-165-cm-2026/a22999911/w-4",
        "price": 1799.0,
        "promo": "None"
    },
    {
        "name": "TV LED Samsung Micro RGB TMR75R85H 190 cm 2026",
        "title": "TV LED Samsung Micro RGB TMR75R85H 190 cm 2026",
        "url": "https://www.fnac.com/TV-LED-Samsung-Micro-RGB-TMR75R85H-190-cm-2026/a22999925/w-4",
        "price": 2299.0,
        "promo": "Sale; was EUR 2399.00"
    },
    {
        "name": "TV LED Samsung Micro RGB TMR85R85H 216 cm 2026",
        "title": "TV LED Samsung Micro RGB TMR85R85H 216 cm 2026",
        "url": "https://www.fnac.com/TV-LED-Samsung-Micro-RGB-TMR85R85H-216-cm-2026/a22999899/w-4",
        "price": 3999.0,
        "promo": "None"
    }
]

lg_mrgb = [
    {
        "name": "TV LG Micro RGB evo 100MRGB96 254 cm 2026",
        "title": "TV LG Micro RGB evo 100MRGB96 254 cm 2026",
        "url": "https://www.fnac.com/TV-LG-Micro-RGB-evo-100MRGB96-254-cm-2026/a23103478/w-4",
        "price": 9999.0,
        "promo": "None"
    },
    {
        "name": "TV LG Micro RGB evo 86MRGB96 218 cm 2026",
        "title": "TV LG Micro RGB evo 86MRGB96 218 cm 2026",
        "url": "https://www.fnac.com/TV-LG-Micro-RGB-evo-86MRGB96-218-cm-2026/a23103470/w-4",
        "price": 6999.0,
        "promo": "None"
    }
]

for item in samsung_mrgb:
    master_data["samsung"][item["name"]] = item

for item in lg_mrgb:
    master_data["lg"][item["name"]] = item

with open(master_file, 'w', encoding='utf-8') as f:
    json.dump(master_data, f, ensure_ascii=False, indent=2)

with open('data/raw_fnac_samsung.json', 'w', encoding='utf-8') as f:
    json.dump(list(master_data["samsung"].values()), f, ensure_ascii=False, indent=2)

with open('data/raw_fnac_lg.json', 'w', encoding='utf-8') as f:
    json.dump(list(master_data["lg"].values()), f, ensure_ascii=False, indent=2)

print(f"Master URL Registry updated: Samsung={len(master_data['samsung'])}, LG={len(master_data['lg'])}")
