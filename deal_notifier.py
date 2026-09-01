"""
Quick diagnostic: are we being blocked by IP reputation, or something else?

Run this SAME script in two places and compare the output:
  1. Locally, on your home/office internet connection
  2. In a GitHub Actions job (add a step: `python diagnose_block.py`)

What to look for:
  - If local succeeds (200 + real content) but Actions gets 403/empty,
    that strongly confirms IP-based blocking -> proxy/residential IP needed.
  - If BOTH get blocked, the issue is browser fingerprinting or TLS
    fingerprinting, not just IP -> stealth patches worth trying first.
  - If BOTH succeed, something else was wrong in the original script
    (selectors, timing, etc.) rather than bot detection at all.
"""
import requests
from playwright.sync_api import sync_playwright

URL = "https://www.woolworths.com.au/shop/browse/specials/half-price"


def check_with_requests():
    print("\n--- Plain requests.get() (no browser) ---")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(URL, headers=headers, timeout=20)
        print(f"Status: {resp.status_code}")
        print(f"Content length: {len(resp.text)}")
        print(f"First 300 chars: {resp.text[:300]!r}")
    except Exception as e:
        print(f"Failed: {e}")


def check_with_playwright(headless=True):
    print(f"\n--- Playwright (headless={headless}) ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()
        try:
            response = page.goto(URL, timeout=30000, wait_until="domcontentloaded")
            print(f"Status: {response.status if response else 'no response'}")
            content = page.content()
            print(f"Content length: {len(content)}")
            has_tiles = page.query_selector(".product-tile-v2") is not None
            print(f"Found .product-tile-v2 on page: {has_tiles}")
            # Save for manual inspection
            with open("diag_output.html", "w", encoding="utf-8") as f:
                f.write(content)
            page.screenshot(path="diag_screenshot.png", full_page=True)
            print("Saved diag_output.html and diag_screenshot.png")
        except Exception as e:
            print(f"Failed: {e}")
        finally:
            browser.close()


if __name__ == "__main__":
    import socket
    try:
        # Cheap way to log which IP this run is coming from
        import urllib.request
        ip = urllib.request.urlopen("https://api.ipify.org", timeout=10).read().decode()
        print(f"Outbound IP for this run: {ip}")
    except Exception as e:
        print(f"Could not determine outbound IP: {e}")

    check_with_requests()
    check_with_playwright(headless=True)
