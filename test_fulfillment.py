#!/usr/bin/env python3

import cloudscraper
import json

def test_fulfillment():
    # Try the fulfillment messages API
    base_url = "https://www.apple.com"

    # Product details from the URL
    product_config = {
        "parts": ["MYX63J/A"],  # This might be the part number for the product
        "location": "27.06",  # Osaka area code
        "store": "R119"  # Shinsaibashi store code (guessing)
    }

    urls_to_try = [
        f"{base_url}/jp/shop/fulfillment-messages?fae=true&parts.0=MYX63J/A",
        f"{base_url}/jp/shop/retail/pickup-message?parts.0=MYX63J/A&location=大阪",
        f"{base_url}/jp/shop/retail/pickup-message?parts.0=MYX63J/A&store=R119",
        f"{base_url}/jp/shop/bagx/fulfillment?product=iphone-17-pro",
    ]

    scraper = cloudscraper.create_scraper()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ja-JP,ja;q=0.9',
        'Referer': 'https://www.apple.com/jp/shop/buy-iphone/iphone-17-pro',
    }

    for url in urls_to_try:
        print(f"\nTrying: {url}")
        try:
            response = scraper.get(url, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                # Try to parse as JSON
                try:
                    data = response.json()
                    print(f"Response type: JSON")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
                except:
                    print(f"Response type: HTML/Text")
                    print(response.text[:500])
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_fulfillment()