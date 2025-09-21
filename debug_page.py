#!/usr/bin/env python3

import cloudscraper
from bs4 import BeautifulSoup
import re

def debug_page():
    url = "https://www.apple.com/jp/shop/buy-iphone/iphone-17-pro/6.9%E3%82%A4%E3%83%B3%E3%83%81%E3%83%87%E3%82%A3%E3%82%B9%E3%83%97%E3%83%AC%E3%82%A4-256gb-%E3%82%B3%E3%82%BA%E3%83%9F%E3%83%83%E3%82%AF%E3%82%AA%E3%83%AC%E3%83%B3%E3%82%B8-sim%E3%83%95%E3%83%AA%E3%83%BC"

    scraper = cloudscraper.create_scraper()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8',
    }

    print("Fetching page...")
    response = scraper.get(url, headers=headers, timeout=15)

    # Save HTML for inspection
    with open('apple_page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)

    print(f"Saved HTML to apple_page.html ({len(response.text)} bytes)")

    # Look for any mention of stores or pickup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Search for keywords
    keywords = ['心斎橋', 'ピックアップ', 'pickup', 'store', '店舗', '受け取り', '利用できません']

    for keyword in keywords:
        if keyword in response.text:
            print(f"\nFound keyword '{keyword}' in page")
            # Find context around the keyword
            index = response.text.find(keyword)
            start = max(0, index - 100)
            end = min(len(response.text), index + 100)
            context = response.text[start:end]
            print(f"Context: ...{context}...")

    # Look for any store-related elements
    store_elements = soup.find_all(text=re.compile(r'(心斎橋|店舗|ストア|ピックアップ)', re.IGNORECASE))
    if store_elements:
        print(f"\nFound {len(store_elements)} store-related text elements")
        for elem in store_elements[:3]:
            parent = elem.parent
            print(f"- Text: {elem.strip()[:50]}...")
            if parent:
                print(f"  Parent tag: {parent.name}")
                print(f"  Parent classes: {parent.get('class', [])}")

if __name__ == "__main__":
    debug_page()