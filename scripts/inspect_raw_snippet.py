# -*- coding: utf-8 -*-
import sys
import os
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('scripts/sample_mm_hu_search.html', 'r', encoding='utf-8') as f:
    html = f.read()

idx = html.find('window.__PRELOADED_STATE__')
if idx != -1:
    snippet = html[idx:idx+5000]
    print(snippet[:1000])
    print("--- around 4500 ---")
    print(snippet[4400:4600])

