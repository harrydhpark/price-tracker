# -*- coding: utf-8 -*-
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from scrapling.fetchers import DynamicFetcher
import re

url = 'https://www.currys.co.uk/tv-and-audio/televisions/tvs/lg?start=0&sz=20'
p = DynamicFetcher.fetch(url, headless=True, real_chrome=True, network_idle=True, timeout=90000, wait=2500)
seen = set()
for a in p.css('a[href*="/products/"]'):
    href = a.attrib.get('href') or ''
    name = a.get_all_text(strip=True) or ''
    if not re.match(r'^(SAMSUNG|LG)\b', name) or len(name) < 25 or href in seen or '£' in name:
        continue
    seen.add(href)
    node = a
    t = ''
    for _ in range(6):
        node = node.parent
        if node is None:
            break
        cand = node.get_all_text(strip=True) or ''
        if '£' in cand and len(cand) < 2000 and name[:30] in cand:
            t = cand
            break
    print('--- ITEM CARD ---')
    print('NAME:', name)
    print('TEXT:', t)
