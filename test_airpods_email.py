#!/usr/bin/env python3

import cloudscraper
import json
import re
import os
import sys
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from working_email_notifier import EmailNotifier
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_airpods_with_email():
    """Test email notifications with AirPods Pro 3 (which has stock)"""

    # Load environment variables
    load_dotenv()

    # Initialize email notifier
    notifier = EmailNotifier()

    print("=" * 60)
    print("Testing Email Notifications with AirPods Pro 3")
    print("=" * 60)

    # First, verify email configuration
    print("\n1. Testing email configuration...")
    success, message = notifier.test_connection()
    if not success:
        print(f"❌ Email test failed: {message}")
        return
    print(f"✅ Email configuration valid!")

    # Now check AirPods inventory
    url = "https://www.apple.com/jp/shop/buy-airpods/airpods-pro-3"
    scraper = cloudscraper.create_scraper()

    print("\n2. Checking AirPods Pro 3 inventory...")
    response = scraper.get(url, timeout=15)

    if response.status_code != 200:
        print(f"Failed to load page: {response.status_code}")
        return

    # Extract part numbers
    part_numbers = re.findall(r'"partNumber":"([^"]+)"', response.text)[:5]

    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('h1')
    product_name = title.get_text(strip=True) if title else "AirPods Pro 3"

    # Check inventory
    parts_params = '&'.join([f'parts.{i}={part}' for i, part in enumerate(part_numbers)])
    api_url = f"https://www.apple.com/jp/shop/fulfillment-messages?{parts_params}&location=大阪&fae=true"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ja-JP,ja;q=0.9',
        'Referer': url,
    }

    response = scraper.get(api_url, headers=headers, timeout=10)
    data = response.json()

    # Parse stores
    stores_to_notify = []

    if 'body' in data:
        body = data['body']
        if 'content' in body and 'pickupMessage' in body['content']:
            stores_data = body['content']['pickupMessage'].get('stores', [])

            for store in stores_data:
                store_name = store.get('storeName', '')

                # Check for 心斎橋 and 梅田
                if '心斎橋' in store_name or '梅田' in store_name:
                    parts_availability = store.get('partsAvailability', {})

                    for part, info in parts_availability.items():
                        pickup_quote = info.get('pickupSearchQuote', '利用できません')
                        if '本日' in pickup_quote or '利用可能' in pickup_quote:
                            store_short_name = '心斎橋' if '心斎橋' in store_name else '梅田'
                            stores_to_notify.append({
                                'name': store_short_name,
                                'status': pickup_quote
                            })
                            break

    # Send test emails for available stores
    print(f"\n3. Found {len(stores_to_notify)} stores with stock")

    if stores_to_notify:
        print("\nSending email notifications for stores with stock...")

        for store_info in stores_to_notify:
            print(f"\n📧 Sending notification for Apple {store_info['name']}...")

            success = notifier.send_pickup_alert(
                store_name=store_info['name'],
                product_name=product_name,
                product_url=url,
                status=store_info['status']
            )

            if success:
                print(f"✅ Email sent for Apple {store_info['name']}!")
            else:
                print(f"❌ Failed to send email for Apple {store_info['name']}")

        print("\n" + "=" * 60)
        print("📬 Check your inbox at fruitcc@gmail.com")
        print("   (Also check spam folder if not in inbox)")
        print("=" * 60)
    else:
        print("No stores with stock found - no emails to send")

if __name__ == "__main__":
    test_airpods_with_email()