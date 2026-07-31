# -*- coding: utf-8 -*-
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open('currys_cards_debug.txt', 'r', encoding='utf-16le') as f:
    text = f.read()

blocks = text.split('--- ITEM CARD ---')
print(f"Total blocks found: {len(blocks)}")
for i, block in enumerate(blocks[1:6], 1):
    print(f"\n================ CARD #{i} ================")
    print(block.strip())
