import urllib.request
import json
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
}

currys_urls = [
    ('LG', '43LB65006LA', 43, 'https://www.currys.co.uk/products/lg-lb650b-43-smart-hd-hdr-led-tv-43lb65006la-10305659.html'),
    ('LG', '50QNED86A6C', 50, 'https://www.currys.co.uk/products/lg-qned86-50-qned-evo-ai-mini-led-4k-hdr-smart-tv-2025-50qned86a6c-10282156.html'),
    ('LG', '55NANO80A6B', 55, 'https://www.currys.co.uk/products/lg-nano80-55-nanocell-ai-4k-hdr-smart-tv-2025-55nano80a6b-10282088.html'),
    ('LG', '55QNED82A6B', 55, 'https://www.currys.co.uk/products/lg-qned82-55-qned-ai-4k-hdr-smart-tv-2025-55qned82a6b-10281537.html'),
    ('LG', 'OLED65G54LW', 65, 'https://www.currys.co.uk/products/lg-g5-65-oled-evo-ai-4k-hdr-smart-tv-2025-wall-mount-version-oled65g54lw-10280771.html'),
    ('LG', 'OLED65G66LS', 65, 'https://www.currys.co.uk/products/lg-g6-65-oled-ai-4k-hdr-smart-tv-2026-stand-version-oled65g66ls-10301977.html'),
    ('LG', 'OLED77C66LB', 77, 'https://www.currys.co.uk/products/lg-c6-77-oled-ai-4k-hdr-smart-tv-2026-oled77c66lb-10301810.html'),
    ('LG', 'OLED83B65LA', 83, 'https://www.currys.co.uk/products/lg-b6-83-oled-ai-4k-hdr-smart-tv-2026-oled83b65la-10301911.html'),
    ('LG', '85QNED72B6A', 85, 'https://www.currys.co.uk/products/lg-qned72-85-qned-ai-4k-hdr-smart-tv-2026-85qned72b6a-10301307.html'),
    ('LG', '86NANO81A6A', 86, 'https://www.currys.co.uk/products/lg-nano81a-86-nanocell-ai-4k-hdr-smart-tv-2025-86nano81a6a-10282162.html'),
    ('LG', '86QNED86A6A', 86, 'https://www.currys.co.uk/products/lg-qned86-86-qned-evo-ai-mini-led-4k-hdr-smart-tv-2025-86qned86a6a-10280294.html'),
    ('LG', '98NU900B6LB', 98, 'https://www.currys.co.uk/products/lg-nu90-98-led-4k-hdr-smart-tv-2026-98nu900b6lb-10301898.html'),
    ('LG', '115QNED93B6', 115, 'https://www.currys.co.uk/products/lg-qned93-115-qned-ai-mini-led-4k-hdr-smart-tv-2026-115qned93b6-10306309.html'),
    ('SAMSUNG', 'UE27LSM7FA', 27, 'https://www.currys.co.uk/products/samsung-the-movingstyle-ue27lsm7faxxxu-27-smart-quad-hd-hdr-led-tv-white-10296272.html')
]

for b, code, size, url in currys_urls:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            
            price = None
            avail = 'Unknown'
            for s in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(s.string)
                    if isinstance(data, dict) and 'offers' in data:
                        offers = data['offers']
                        if isinstance(offers, dict):
                            price = offers.get('price')
                            avail = offers.get('availability', '')
                        elif isinstance(offers, list):
                            price = offers[0].get('price')
                            avail = offers[0].get('availability', '')
                except:
                    pass
            is_in_stock = 'instock' in str(avail).lower()
            print(f'[{b}] {code} ({size}in): Price=GBP {price}, InStock={is_in_stock}, Status={resp.status}')
    except urllib.error.HTTPError as e:
        print(f'[{b}] {code}: HTTP {e.code}')
    except Exception as e:
        print(f'[{b}] {code}: Error {e}')
