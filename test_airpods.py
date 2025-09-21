#!/usr/bin/env python3

import cloudscraper
import json
import re
from bs4 import BeautifulSoup

def check_airpods_inventory():
    """Check AirPods Pro 3 inventory at Osaka stores"""

    url = "https://www.apple.com/jp/shop/buy-airpods/airpods-pro-3"
    scraper = cloudscraper.create_scraper()

    print("=" * 60)
    print("Checking AirPods Pro 3 Inventory")
    print("=" * 60)

    # First, get the product page to extract part numbers
    print("\n1. Fetching product page...")
    response = scraper.get(url, timeout=15)

    if response.status_code != 200:
        print(f"Failed to load page: {response.status_code}")
        return

    # Extract part numbers
    part_numbers = re.findall(r'"partNumber":"([^"]+)"', response.text)

    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('h1')
    if title:
        print(f"Product: {title.get_text(strip=True)}")

    if part_numbers:
        print(f"Found {len(part_numbers)} variants")
        print(f"Part numbers: {', '.join(part_numbers[:5])}...")
    else:
        print("No part numbers found!")
        return

    # Check inventory using the fulfillment API
    print("\n2. Checking store inventory...")

    # Use the first few part numbers
    parts_to_check = part_numbers[:5]
    parts_params = '&'.join([f'parts.{i}={part}' for i, part in enumerate(parts_to_check)])

    # Try different API endpoints
    api_urls = [
        f"https://www.apple.com/jp/shop/fulfillment-messages?{parts_params}&location=大阪&fae=true",
        f"https://www.apple.com/jp/shop/retail/pickup-message?{parts_params}&location=osaka",
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ja-JP,ja;q=0.9',
        'Referer': url,
    }

    stores_found = {}

    for api_url in api_urls:
        try:
            print(f"\nTrying API: {api_url[:80]}...")
            response = scraper.get(api_url, headers=headers, timeout=10)

            if response.status_code != 200:
                print(f"API returned status {response.status_code}")
                continue

            data = response.json()

            # Parse the response
            stores_data = []

            if 'body' in data:
                body = data['body']
                if 'content' in body and 'pickupMessage' in body['content']:
                    stores_data = body['content']['pickupMessage'].get('stores', [])
                elif 'stores' in body:
                    stores_data = body['stores']

            # Check each store
            for store in stores_data:
                store_name = store.get('storeName', '')

                # Check for our target stores
                if '心斎橋' in store_name or '梅田' in store_name:
                    parts_availability = store.get('partsAvailability', {})

                    store_status = {
                        'name': store_name,
                        'available': False,
                        'status': '利用できません',
                        'details': []
                    }

                    for part, info in parts_availability.items():
                        pickup_quote = info.get('pickupSearchQuote', '利用できません')
                        pickup_display = info.get('pickupDisplay', 'unavailable')
                        store_pickup = info.get('storePickupAvailable', False)

                        store_status['details'].append({
                            'part': part,
                            'quote': pickup_quote,
                            'available': store_pickup or pickup_display == 'available'
                        })

                        if store_pickup or pickup_display == 'available' or '利用可能' in pickup_quote:
                            store_status['available'] = True
                            store_status['status'] = pickup_quote

                    stores_found[store_name] = store_status

            if stores_found:
                break  # Found stores, no need to try other APIs

        except Exception as e:
            print(f"Error with API: {e}")
            continue

    # Display results
    print("\n" + "=" * 60)
    print("INVENTORY STATUS - OSAKA STORES")
    print("=" * 60)

    target_stores = ['心斎橋', '梅田']

    for target in target_stores:
        found = False
        for store_name, status in stores_found.items():
            if target in store_name:
                found = True
                icon = "✅" if status['available'] else "❌"
                print(f"\nApple {target}: {icon}")
                print(f"  Status: {status['status']}")

                # Show details for each variant
                if status['details']:
                    print(f"  Variants checked:")
                    for detail in status['details'][:3]:  # Show first 3
                        variant_icon = "✓" if detail['available'] else "✗"
                        print(f"    {variant_icon} {detail['part']}: {detail['quote']}")
                break

        if not found:
            print(f"\nApple {target}: ❓")
            print(f"  Status: Store not found in response")

    # Summary
    print("\n" + "=" * 60)
    available_stores = [name for name, status in stores_found.items()
                       if status['available'] and any(t in name for t in target_stores)]

    if available_stores:
        print(f"🎯 Available for pickup at: {', '.join(available_stores)}")
    else:
        print("Currently not available for pickup at 心斎橋 or 梅田")

if __name__ == "__main__":
    check_airpods_inventory()