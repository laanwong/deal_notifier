import os
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("SENDER_EMAIL")

def get_woolworths_deals(page):
    """Scrape half-price deals from Woolworths using Playwright."""
    deals = []
    try:
        page.goto("https://www.woolworths.com.au/shop/browse/specials/half-price", timeout=60000)
        page.wait_for_selector(".product-tile-v2", timeout=15000)
        
        tiles = page.query_selector_all(".product-tile-v2")
        for tile in tiles[:15]:  # Grab top 15 deals
            title_el = tile.query_selector(".product-title")
            price_el = tile.query_selector(".primary")
            if title_el and price_el:
                title = title_el.inner_text().strip()
                price = price_el.inner_text().strip()
                deals.append(f"• Woolies: {title} - {price}")
    except Exception as e:
        print(f"Error fetching Woolworths: {e}")
    return deals

def send_email_summary(deals):
    """Sends the summary via email."""
    if not deals:
        content = "No deals retrieved. Check Playwright selectors or site loading."
    else:
        content = "Hi! Here are this week's top half-price grocery deals:\n\n" + "\n".join(deals)

    msg = MIMEText(content)
    msg['Subject'] = "🛒 Weekly Half-Price Grocery Summary"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    print("Email sent successfully!")

if __name__ == "__main__":
    all_deals = []
    with sync_playwright() as p:
        # Launch headless browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        all_deals.extend(get_woolworths_deals(page))
        browser.close()

    send_email_summary(all_deals)
