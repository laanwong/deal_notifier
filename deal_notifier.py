import os
import json
import requests
from datetime import datetime, timezone

API_KEY = os.environ.get("PARSE_API_KEY")

# Woolworths and Coles scraper IDs on Parse.bot
WOOLIES_ID = "d5aff3d6-33c4-431f-bf9d-6191efaec2e6"
COLES_ID   = "dd2897d9-0135-464a-b16a-54ccc10e02e4"

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
        "page_size": 5,
        "is_special": "false"
    }
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "success":
            return data.get("data", {}).get("products", [])
    except Exception as e:
        print(f"Woolworths error for '{term}': {e}")
    return []

def search_coles(term):
    url = f"https://api.parse.bot/scraper/{COLES_ID}/search_products"
    params = {"query": term, "page": 1}
    headers = {"X-API-Key": API_KEY}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        # Coles response structure may vary slightly – we handle the common cases
        if isinstance(data, dict):
            products = data.get("data", {}).get("products") or data.get("products") or []
            return products
    except Exception as e:
        print(f"Coles error for '{term}': {e}")
    return []

def normalise(product, store, search_term):
    """Turn different store responses into one simple format"""
    name = product.get("name") or product.get("Name") or product.get("title") or "Unknown"
    price = product.get("price") or product.get("Price") or 0
    was = product.get("was_price") or product.get("WasPrice") or price
    on_special = product.get("is_on_special") or product.get("IsOnSpecial") or False
    cup = product.get("cup_string") or product.get("CupString") or ""

    try:
        price = float(price)
        was = float(was)
    except:
        price = 0
        was = 0

    return {
        "name": name,
        "store": store,
        "price": price,
        "was_price": was,
        "is_on_special": bool(on_special) or (was > price + 0.01),
        "cup_string": cup,
        "search_term": search_term
    }

def main():
    print(f"=== Eugene's Deal Finder – {datetime.now().isoformat()} ===")
    results = []

    for term in ITEMS:
        print(f"Searching: {term}")

        # Woolworths
        for p in search_woolworths(term)[:2]:   # take top 2 matches
            results.append(normalise(p, "Woolworths", term))

        # Coles
        for p in search_coles(term)[:2]:
            results.append(normalise(p, "Coles", term))

    # Save the file the website reads
    output = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "items": results
    }

    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Saved {len(results)} items to prices.json")

if __name__ == "__main__":
    main()
