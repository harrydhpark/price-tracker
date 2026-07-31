# -*- coding: utf-8 -*-
import sys
import os
import json
import re
from scrapling.fetchers import StealthySession

sys.stdout.reconfigure(encoding='utf-8')

urls = [
    ("Kotsovolos_LED", "https://www.kotsovolos.gr/sound-vision/televisions/led-lcd"),
    ("Kotsovolos_OLED", "https://www.kotsovolos.gr/sound-vision/televisions/oled"),
    ("Kotsovolos_Search_Samsung", "https://www.kotsovolos.gr/site/search.jsp?q=samsung+tv"),
    ("Kotsovolos_Search_LG", "https://www.kotsovolos.gr/site/search.jsp?q=lg+tv"),
    ("Public_OLED", "https://www.public.gr/cat/sound-and-vision/tvs/oled"),
    ("Public_QLED", "https://www.public.gr/cat/sound-and-vision/tvs/qled"),
    ("Public_4K", "https://www.public.gr/cat/sound-and-vision/tvs/4k-ultra-hd"),
    ("Public_Search_Samsung", "https://www.public.gr/search?q=samsung+tv"),
    ("Public_Search_LG", "https://www.public.gr/search?q=lg+tv"),
]

def test():
    with StealthySession(headless=True) as session:
        for name, url in urls:
            try:
                res = session.fetch(url, wait=3000)
                body = res.body if hasattr(res, 'body') else str(res)
                if isinstance(body, bytes):
                    body = body.decode('utf-8', errors='ignore')
                print(f"[{name}] Status OK, Length: {len(body)}")
                filename = f"data/debug_{name.lower()}.html"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(body)
            except Exception as e:
                print(f"[{name}] Error: {e}")

if __name__ == '__main__':
    test()
