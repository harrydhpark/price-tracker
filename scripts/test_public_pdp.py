import sys, re, json
from bs4 import BeautifulSoup
from scrapling.fetchers import StealthySession

sys.stdout.reconfigure(encoding='utf-8')

test_urls = [
    ('LG', '43UA75006LA', 'https://www.public.gr/product/tileoraseis/tileoraseis/lg-led-43-4k-smart-tileorasi-43ua75006la/2044148'),
    ('LG', '55NANO81A6A', 'https://www.public.gr/product/tileoraseis/tileoraseis/lg-nanocell-55-4k-smart-tileorasi-55nano81a6a/2035071'),
    ('LG', '43QNED81B6C', 'https://www.public.gr/product/tileoraseis/tileoraseis/lg-qned-43-4k-smart-tileorasi-43qned81b6c-ai/2133567'),
    ('SAMSUNG', 'QE50QN80F', 'https://www.public.gr/product/tileoraseis/tileoraseis/samsung-neo-qled-50-4k-smart-tileorasi-qe50qn80fatxxh/2043689'),
]

with StealthySession(headless=True) as session:
    for brand, code, url in test_urls:
        try:
            res = session.fetch(url, wait=3000)
            print(f'[{brand}] {code}: Status={res.status}')
            if res.status == 200:
                soup = BeautifulSoup(res.body, 'html.parser')
                text = soup.get_text(' ', strip=True)
                
                # Check out of stock
                is_out = any(x in text.upper() for x in ['ΕΞΑΝΤΛΗΘΗΚΕ', 'ΜΗ ΔΙΑΘΕΣΙΜΟ', 'OUT OF STOCK', 'ΠΡΟΣΩΡΙΝΑ ΜΗ ΔΙΑΘΕΣΙΜΟ'])
                
                # Look for price in ld+json
                ld_price = None
                for s in soup.find_all('script', type='application/ld+json'):
                    try:
                        d = json.loads(s.string)
                        if isinstance(d, dict) and 'offers' in d:
                            ld_price = d['offers'].get('price')
                    except:
                        pass
                        
                # regex price
                prices = re.findall(r'(\d[\d\.\s]*[,\.]\d{2})\s*€', text)
                print(f'   Out={is_out}, LD_Price={ld_price}, Prices={prices[:4]}')
        except Exception as e:
            print(f'[{brand}] {code}: Error {e}')
