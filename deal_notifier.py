import os
import json
import requests
from datetime import datetime, timezone
import time

API_KEY = os.environ.get("PARSE_API_KEY")
WOOLIES_ID = "d5aff3d6-33c4-431f-bf9d-6191efaec2e6"

ITEMS = [
    "whole chicken",
    "chicken breast",
    "beef mince",
    "pork mince",
    "lamb chops",
    "bacon",
    "bananas",
    "apples",
    "avocado",
    "oranges",
    "broccoli",
    "carrots",
    "potatoes",
    "tomatoes",
    "onions",
    "lettuce",
    "pumpkin",
    "white bread",
    "wholemeal bread",
    "raisin bread",
    "tortilla wraps",
    "full cream milk 1l",
    "free range eggs",
    "butter",
    "jam",
    "peanut butter",
    "cereal",
    "nuts",
    "chewing gum"
]

def search_woolworths(term):
    url = f"https://api.parse.bot/scraper/{WOOLIES_ID}/search_products"
    payload = {
        "search_term": term,
        "page": 1,
        "page_size": 3,
        "is_special": "false"
    }
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 402:
            print("Out of free credits (402). Stopping.")
            return None  # signal to stop
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "success":
            return data.get("data", {}).get("products", [])
    except Exception as e:
        print(f"Error searching '{term}': {e}")
    return []

def normalise(product, search_term):
    name = product.get("name") or "Unknown"
    price = product.get("price") or 0
    was = product.get("was_price") or price
    on_special = product.get("is_on_special") or False
    cup = product.get("cup_string") or ""

    try:
        price = float(price)
        was = float(was)
    except:
        price = 0
        was = 0

    return {
        "name": name,
        "store": "Woolworths",
        "price": price,
        "was_price": was,
        "is_on_special": bool(on_special) or (was > price + 0.05),
        "cup_string": cup,
        "search_term": search_term
    }

def main():
    print(f"=== Eugene's Deal Finder – {datetime.now().isoformat()} ===")
    results = []

    for term in ITEMS:
        print(f"Searching: {term}")
        products = search_woolworths(term)

        if products is None:  # out of credits
            break

        if products:
            # Take only the best (first) match
            results.append(normalise(products[0], term))

        time.sleep(1)  # small pause to be polite

    output = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "items": results
    }

    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Saved {len(results)} items to prices.json")

if __name__ == "__main__":
    main()
