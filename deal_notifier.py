import os
import requests
from datetime import datetime

API_KEY = os.environ["PARSE_API_KEY"]
STOCKCODES = ["32731"]          # add more product IDs here

url = "https://api.parse.bot/scraper/d5aff3d6-33c4-431f-bf9d-6191efaec2e6/get_product_detail"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

print(f"=== Woolworths price check – {datetime.now().isoformat()} ===\n")

for stockcode in STOCKCODES:
    try:
        r = requests.get(url, headers=headers, params={"stockcode": stockcode}, timeout=30)
        r.raise_for_status()
        data = r.json()

        if data.get("status") == "success":
            p = data["data"]
            print(f"{p['name']}")
            print(f"  Price     : ${p['price']}")
            print(f"  Was       : ${p.get('was_price')}")
            print(f"  On special: {p.get('is_on_special')}")
            print(f"  Cup       : {p.get('cup_string')}")
            print(f"  In stock  : {p.get('is_in_stock')}")
            print()
        else:
            print(f"Error for {stockcode}: {data}")
    except Exception as e:
        print(f"Failed for {stockcode}: {e}")
