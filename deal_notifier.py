import requests
import smtplib
from email.mime.text import MIMEText
import os

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("SENDER_EMAIL")  # Change to your wife's email if different

def get_coles_half_price():
    """Fetch 50% off specials from Coles API."""
    url = "https://www.coles.com.au/api/bff/products/specials"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    params = {
        "page": 1,
        "pageSize": 30,
        "filter_Special": "halfprice"
    }
    deals = []
    try:
        res = requests.get(url, headers=headers, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            products = data.get("results", [])
            for p in products:
                name = p.get("name")
                pricing = p.get("pricing", {})
                price = pricing.get("now")
                was_price = pricing.get("was")
                if name and price and was_price:
                    deals.append(f"• Coles: {name} - ${price:.2f} (Was ${was_price:.2f})")
        else:
            print(f"Coles API returned status code: {res.status_code}")
    except Exception as e:
        print(f"Error fetching Coles data: {e}")
    return deals

def get_woolworths_half_price():
    """Fetch 50% off specials from Woolworths endpoint."""
    url = "https://www.woolworths.com.au/apis/ui/browse/category"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Origin": "https://www.woolworths.com.au",
        "Referer": "https://www.woolworths.com.au/shop/browse/specials/half-price"
    }
    payload = {
        "categoryId": "1_39A132C",
        "pageNumber": 1,
        "pageSize": 30,
        "sortType": "TraderRelevance"
    }
    deals = []
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        if res.status_code == 200:
            products = res.json().get("Bundles", [])
            for p in products:
                products_list = p.get("Products", [])
                if products_list:
                    prod = products_list[0]
                    name = prod.get("Name")
                    price = prod.get("Price")
                    was_price = prod.get("WasPrice")
                    if name and price and was_price and price <= (was_price * 0.55):
                        deals.append(f"• Woolies: {name} - ${price:.2f} (Was ${was_price:.2f})")
        else:
            print(f"Woolies API returned status code: {res.status_code}")
    except Exception as e:
        print(f"Error fetching Woolworths data: {e}")
    return deals

def send_email_summary(deals):
    """Sends the daily/weekly digest via Email."""
    if not deals:
        content = "No 50% off deals retrieved. The store endpoints may be temporarily blocking requests."
    else:
        content = "Hi! Here are this week's top half-price grocery deals from Coles & Woolworths:\n\n" + "\n".join(deals)

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
    all_deals.extend(get_coles_half_price())
    all_deals.extend(get_woolworths_half_price())
    send_email_summary(all_deals)
