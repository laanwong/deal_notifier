# --- CONFIGURATION ---
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"  # Generated from Google Account App Passwords
RECIPIENT_EMAIL = "wife_email@gmail.com"

def get_woolworths_half_price():
    """Fetch 50% off specials from Woolworths API."""
    url = "https://www.woolworths.com.au/apis/ui/browse/category"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    payload = {
        "categoryId": "1_39A132C", # Specials category
        "pageNumber": 1,
        "pageSize": 20,
        "sortType": "TraderRelevance"
    }
    deals = []
    try:
        res = requests.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            products = res.json().get("Bundles", [])
            for p in products:
                name = p.get("Name")
                price = p.get("Price")
                was_price = p.get("WasPrice")
                if price and was_price and price <= (was_price * 0.5):
                    deals.append(f"• Woolies: {name} - ${price} (Was ${was_price})")
    except Exception as e:
        print(f"Error fetching Woolworths data: {e}")
    return deals

def send_email_summary(deals):
    """Sends the daily/weekly digest via Email."""
    if not deals:
        content = "No major 50% off deals found today!"
    else:
        content = "Hi! Here are this week's top half-price grocery deals:\n\n" + "\n".join(deals)

    msg = MIMEText(content)
    msg['Subject'] = "🛒 Today's Grocery Deals & Discount Summary"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    print("Email sent successfully!")

if __name__ == "__main__":
    woolies_deals = get_woolworths_half_price()
    send_email_summary(woolies_deals)
