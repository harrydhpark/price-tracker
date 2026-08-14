# -*- coding: utf-8 -*-
import sys
import os
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('scripts/preloaded_state_fixed.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

apollo = d.get('apolloState', {})

# Find all price features
for k, v in apollo.items():
    if k.startswith("CofrPriceFeature:"):
        print("PRICE KEY:", k)
        print("PRICE VAL:", json.dumps(v, ensure_ascii=False, indent=2))
        break

