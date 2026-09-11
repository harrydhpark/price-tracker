import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
path = os.path.join(ROOT_DIR, "data", "eu_price_dashboard_template.html")

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

target1 = '"DE": "EUR", "AT": "EUR", "CH": "CHF", "ES": "EUR", "NL": "EUR", "UK": "GBP", "FR": "EUR", "SE": "SEK", "IT": "EUR"'
replacement1 = '"DE": "EUR", "AT": "EUR", "CH": "CHF", "ES": "EUR", "NL": "EUR", "UK": "GBP", "FR": "EUR", "CZ": "CZK", "SE": "SEK", "IT": "EUR"'

target2 = '"EUR": "€", "GBP": "£", "SEK": "kr"'
replacement2 = '"EUR": "€", "GBP": "£", "CHF": "CHF ", "CZK": "Kč ", "SEK": "kr "'

if target1 in content:
    content = content.replace(target1, replacement1)
    print("Replaced target1 successfully!")
else:
    print("target1 NOT found")

if target2 in content:
    content = content.replace(target2, replacement2)
    print("Replaced target2 successfully!")
else:
    print("target2 NOT found")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated template file.")
