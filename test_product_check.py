#!/usr/bin/env python3

"""
Test script to verify we're checking the correct product
"""

import requests
import json
import re
from bs4 import BeautifulSoup

def check_product_page():
    """Extract and identify the correct part number for Orange 256GB iPhone 17 Pro Max"""

    url = "https://www.apple.com/jp/shop/buy-iphone/iphone-17-pro/6.9インチディスプレイ-256gb-コズミックオレンジ-simフリー"

    print("Fetching product page...")
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return None

    # Look for the specific product in the page data
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the page title
    title = soup.find('h1')
    if title:
        print(f"Product title: {title.get_text(strip=True)}")

    # Find script tags with product data
    scripts = soup.find_all('script', type='application/json')

    for script in scripts:
        try:
            data = json.loads(script.string)
            # Navigate through the data structure to find products
            if isinstance(data, dict):
                check_dict_for_products(data, "")
        except:
            pass

    # Also extract directly from the URL - it should have the part number
    print("\n" + "="*60)
    print("The URL itself specifies:")
    print("- 6.9インチディスプレイ (6.9 inch display)")
    print("- 256GB storage")
    print("- コズミックオレンジ (Cosmic Orange)")
    print("- SIMフリー (SIM-free)")

    # Extract part numbers found on the page
    part_numbers = re.findall(r'"partNumber":"([^"]+)"', response.text)
    unique_parts = list(set(part_numbers))

    print(f"\nFound {len(unique_parts)} unique part numbers on page:")
    for part in unique_parts[:10]:
        print(f"  - {part}")

    return unique_parts

def check_dict_for_products(d, path):
    """Recursively search for product data in JSON"""
    if isinstance(d, dict):
        # Check if this dict contains product info
        if 'partNumber' in d and 'dimensionColor' in d and 'dimensionCapacity' in d:
            if '256' in str(d.get('dimensionCapacity', '')) and 'オレンジ' in str(d.get('dimensionColor', '')):
                print(f"\nFound Orange 256GB variant:")
                print(f"  Part Number: {d.get('partNumber')}")
                print(f"  Color: {d.get('dimensionColor')}")
                print(f"  Capacity: {d.get('dimensionCapacity')}")
                print(f"  Price: {d.get('price', {}).get('value', 'N/A')}")

        # Recurse
        for key, value in d.items():
            check_dict_for_products(value, f"{path}/{key}")
    elif isinstance(d, list):
        for i, item in enumerate(d):
            check_dict_for_products(item, f"{path}[{i}]")

def check_api_with_parts(parts):
    """Test the Apple fulfillment API with specific part numbers"""

    print("\n" + "="*60)
    print("Testing fulfillment API...")

    # Test with just the first part number
    if parts:
        test_part = parts[0]
        api_url = f"https://www.apple.com/jp/shop/fulfillment-messages?parts.0={test_part}&location=osaka"

        print(f"Testing with part number: {test_part}")
        print(f"API URL: {api_url}")

        try:
            response = requests.get(api_url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
            })

            if response.status_code == 200:
                data = response.json()

                # Check if there's pickup info
                if 'body' in data and 'content' in data['body']:
                    content = data['body']['content']
                    if 'pickupMessage' in content:
                        pickup = content['pickupMessage']
                        print(f"\nPickup info found:")
                        print(f"  Product: {pickup.get('orderByDeliveryBy', {}).get('displayName', 'Unknown')}")

                        if 'stores' in pickup:
                            print(f"  Found {len(pickup['stores'])} stores")
                            for store in pickup['stores'][:5]:
                                store_name = store.get('storeName', 'Unknown')
                                availability = store.get('partsAvailability', {})

                                for part_num, avail_info in availability.items():
                                    status = avail_info.get('messageTypes', {}).get('regular', {}).get('storePickupProductTitle', 'Unknown')
                                    print(f"    {store_name}: {status}")
                                    break
            else:
                print(f"API returned status {response.status_code}")

        except Exception as e:
            print(f"Error calling API: {e}")

if __name__ == "__main__":
    print("="*60)
    print("PRODUCT VERIFICATION TEST")
    print("="*60)

    parts = check_product_page()

    if parts:
        check_api_with_parts(parts)

    print("\n" + "="*60)
    print("IMPORTANT: We need to ensure we're checking ONLY the")
    print("Orange 256GB iPhone 17 Pro Max, not other variants!")
    print("="*60)