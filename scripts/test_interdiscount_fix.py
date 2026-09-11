import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('C:/Users/harry.park/.gemini/antigravity/brain/c4e89f42-4283-436e-907c-28b97a4e6da0/.system_generated/steps/264/output.txt', 'r', encoding='utf-8') as f:
    text = f.read()
if text.startswith('### Result'): text = text[len('### Result'):].strip()
idx = text.find('### Ran Playwright')
if idx != -1: text = text[:idx].strip()
d = json.loads(text)

def extract_precise_price(title, full_text):
    # Match price right before title
    clean_frag = title[:18]
    pat1 = r'(\d[\d’\']*(?:\.\d{2}|.–|\.95))\s*(?:CHF)?\s*\n+\s*' + re.escape(clean_frag)
    m = re.findall(pat1, full_text, re.IGNORECASE)
    if m:
        p_raw = m[0].replace('’', '').replace("'", '').replace('.–', '.00')
        return float(p_raw)
        
    t_idx = full_text.find(clean_frag)
    if t_idx != -1:
        chunk_before = full_text[max(0, t_idx-150):t_idx]
        m_before = re.findall(r'(\d[\d’\']*(?:\.\d{2}|.–|\.95))\s*(?:CHF)?', chunk_before)
        if m_before:
            p_raw = m_before[-1].replace('’', '').replace("'", '').replace('.–', '.00')
            return float(p_raw)
            
    return 0.0

print('=== PRECISE INTERDISCOUNT PRICES (Samsung Sample) ===')
for it in d.get('samsung', []):
    t = it.get('title', '')
    if not t: continue
    p = extract_precise_price(t, it.get('text', ''))
    if any(x in t for x in ['S9', 'S8', 'QN8', 'LS03', 'U80']):
        print(f'{t[:55]:<55} | {p:>8.2f} CHF')
