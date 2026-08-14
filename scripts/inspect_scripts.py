# -*- coding: utf-8 -*-
import sys
import os
import json
import re
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

with open('scripts/sample_mm_hu_search.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
scripts = soup.find_all('script')
print(f'Total scripts: {len(scripts)}')

for i, s in enumerate(scripts):
    content = s.string or ''
    t = s.get('type', '')
    sid = s.get('id', '')
    if t == 'application/ld+json' or '__NEXT_DATA__' in sid or 'products' in content.lower() or 'datalayer' in content.lower():
        print(f"[{i}] id='{sid}', type='{t}', len={len(content)}")
        if len(content) > 0:
            print(f"    Snippet: {content[:200]}...\n")

