import os
import sys
import smtplib
from email.mime.text import MIMEText
import requests
from playwright.sync_api import sync_playwright

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", SENDER_EMAIL)

# NOTE: These endpoints/headers are reverse-engineered from Coles' own mobile
# app traffic by third parties (not an official/public API). They can change
# or stop working at any time without notice.
COLES_SEARCH_URL = "https://api.coles.com.au/customer/v1/coles/products/search"
COLES_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip",
    "Accept-Language": "en-AU;q=1",
    "User-Agent": "Shopmate/3.4.1 (iPhone; iOS 11.4.1; Scale/3.00)",
    # These key/secret values are the ones publicly circulated in old scraper
    # repos. They may be revoked/rotated at any time - if requests start
    # failing, re-capture fresh values from the Coles app's network traffic.
    "X-Coles-API-Key": "046bc0d4-3854-481f-80dc-85f9e846503d",
    "X-Coles-API-Secret": "e6ab96ff-453b-45ba-a2be-ae8d7c12cadf",
}


def get_coles_deals(store_id="7716", limit=15):
    """Fetch half-price / special products from Coles via their internal
    (unofficial, reverse-engineered) product search API."""
    deals = []
    try:
        params = {
            "q": "specials",
            "start": 0,
            "limit": limit,
            "storeId": store_id,
            "type": "SKU",
        }
        resp = requests.get(COLES_SEARCH_URL, headers=COLES_HEADERS, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("Results", []) or data.get("results", [])
        for item in results[:limit]:
            product = item.get("Product", item)
            name = product.get("Name") or product.get("name")
            price = product.get("Pricing", {}).get("Now") if isinstance(product.get("Pricing"), dict) else None
            was = product.get("Pricing", {}).get("Was") if isinstance(product.get("Pricing"), dict) else None
            if name and price:
                line = f"• Coles: {name} - ${price}"
                if was:
                    line += f" (was ${was})"
                deals.append(line)
    except requests.exceptions.RequestException as e:
        print(f"[Coles] Request failed: {e}", file=sys.stderr)
    except (ValueError, KeyError) as e:
        print(f"[Coles] Unexpected response format: {e}", file=sys.stderr)
    return deals


def get_woolworths_deals(page):
    """Scrape half-price deals from Woolworths using Playwright.
    Falls back to a screenshot + page-state dump on failure so CI runs are
    debuggable (bot detection / selector drift are the most likely causes)."""
    deals = []
    try:
        response = page.goto(
            "https://www.woolworths.com.au/shop/browse/specials/half-price",
            timeout=60000,
            wait_until="domcontentloaded",
        )
        status = response.status if response else "no response"
        print(f"[Woolworths] Navigated, HTTP status: {status}")

        page.wait_for_selector(".product-tile-v2", timeout=15000)
        tiles = page.query_selector_all(".product-tile-v2")
        for tile in tiles[:15]:
            title_el = tile.query_selector(".product-title")
            price_el = tile.query_selector(".primary")
            if title_el and price_el:
                title = title_el.inner_text().strip()
                price = price_el.inner_text().strip()
                deals.append(f"• Woolies: {title} - {price}")
    except Exception as e:
        print(f"[Woolworths] Error: {e}", file=sys.stderr)
        try:
            os.makedirs("debug", exist_ok=True)
            page.screenshot(path="debug/woolworths_failure.png", full_page=True)
            with open("debug/woolworths_failure.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print("[Woolworths] Saved debug/woolworths_failure.png and .html")
        except Exception as inner_e:
            print(f"[Woolworths] Could not save debug artifacts: {inner_e}", file=sys.stderr)
    return deals


def send_email_summary(deals):
    """Sends the summary via email."""
    if not deals:
        content = (
            "No deals retrieved from either store this run.\n"
            "Check the workflow logs / uploaded debug/ artifacts for details."
        )
    else:
        content = "Hi! Here are this week's top half-price grocery deals:\n\n" + "\n".join(deals)

    msg = MIMEText(content)
    msg["Subject"] = "🛒 Weekly Half-Price Grocery Summary"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    print("Email sent successfully!")


if __name__ == "__main__":
    all_deals = []

    # Coles: plain HTTP request, no browser needed
    coles_deals = get_coles_deals()
    print(f"[Coles] Retrieved {len(coles_deals)} deals")
    all_deals.extend(coles_deals)

    # Woolworths: needs a real browser due to bot protection
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()
        woolies_deals = get_woolworths_deals(page)
        print(f"[Woolworths] Retrieved {len(woolies_deals)} deals")
        all_deals.extend(woolies_deals)
        browser.close()

    send_email_summary(all_deals)

    # Fail the CI run visibly if both sources came back empty - an empty
    # "no deals" email every week silently masks a broken scraper.
    if not all_deals:
        print("WARNING: no deals retrieved from any source this run.", file=sys.stderr)
        sys.exit(1)
