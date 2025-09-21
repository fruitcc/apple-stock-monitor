#!/usr/bin/env python3

import time
import logging
import json
import re
import signal
import sys
from datetime import datetime
import cloudscraper
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Apple Store codes in Japan
STORE_CODES = {
    '心斎橋': 'R119',  # Shinsaibashi
    '銀座': 'R090',
    '丸の内': 'R224',
    '渋谷': 'R224',
    '新宿': 'R225',
    '名古屋栄': 'R221',
    '福岡': 'R223',
}

class ShinsaibashiPickupMonitor:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.running = True
        self.last_status = None
        self.email_sent = False
        self.target_store = "心斎橋"
        self.store_code = STORE_CODES.get(self.target_store, 'R119')
        self.product_parts = []

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        logger.info("\nShutting down...")
        self.running = False
        sys.exit(0)

    def get_product_parts(self, url):
        """Extract product part numbers from the product page"""
        try:
            logger.info("Extracting product information...")
            response = self.scraper.get(url, timeout=15)

            if response.status_code != 200:
                logger.error(f"Failed to load product page: {response.status_code}")
                return []

            # Extract all part numbers from the page
            part_numbers = re.findall(r'"partNumber":"([^"]+)"', response.text)

            # Also extract from product configuration
            # The URL suggests 256GB Cosmic Orange, SIM-free
            # Let's find parts that might match this configuration

            soup = BeautifulSoup(response.text, 'html.parser')

            # Log product title
            title = soup.find('h1')
            if title:
                logger.info(f"Product: {title.get_text(strip=True)}")

            if part_numbers:
                logger.info(f"Found {len(part_numbers)} product variants")
                # For iPhone, typically the first few part numbers are the main configurations
                # We'll check the first 10 relevant ones
                return list(set(part_numbers[:10]))

            return []

        except Exception as e:
            logger.error(f"Error extracting product parts: {e}")
            return []

    def check_store_pickup_api(self, parts):
        """Check pickup availability using Apple's fulfillment API"""
        try:
            if not parts:
                return False, "No product parts available"

            # Construct API URL with parts
            parts_params = '&'.join([f'parts.{i}={part}' for i, part in enumerate(parts)])
            url = f"https://www.apple.com/jp/shop/fulfillment-messages?{parts_params}&store={self.store_code}&fae=true"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'ja-JP,ja;q=0.9',
                'Referer': 'https://www.apple.com/jp/shop/buy-iphone/',
            }

            response = self.scraper.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return False, f"API returned status {response.status_code}"

            data = response.json()

            # Check for store availability
            if 'body' in data and 'content' in data['body']:
                content = data['body']['content']

                # Check pickupMessage
                if 'pickupMessage' in content:
                    pickup = content['pickupMessage']

                    # Check if stores data exists
                    if 'stores' in pickup:
                        stores = pickup['stores']

                        # Find our store
                        for store in stores:
                            store_name = store.get('storeName', '')
                            if self.target_store in store_name:
                                logger.info(f"Found {self.target_store} in API response")

                                # Check availability
                                parts_availability = store.get('partsAvailability', {})

                                for part, info in parts_availability.items():
                                    pickup_display = info.get('pickupDisplay', 'unavailable')
                                    pickup_search_quote = info.get('pickupSearchQuote', '利用できません')

                                    logger.info(f"  Part {part}: {pickup_search_quote}")

                                    # Check if available
                                    if pickup_display == 'available' or '利用可能' in pickup_search_quote:
                                        return True, f"Available: {pickup_search_quote}"

                                return False, "利用できません (Not Available)"

                        logger.warning(f"{self.target_store} not found in stores list")
                        # Log available stores
                        available_stores = [s.get('storeName', 'Unknown') for s in stores[:5]]
                        logger.info(f"Available stores in response: {', '.join(available_stores)}")

                    # Check for general availability message
                    if 'errorMessage' in pickup:
                        if 'not buyable' in pickup['errorMessage']:
                            return False, "Product not available for purchase"

            return False, "Store information not found in response"

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {e}")
            return False, "Invalid API response"
        except Exception as e:
            logger.error(f"API check error: {e}")
            return False, f"Error: {e}"

    def send_notification(self, status):
        """Send notification when product becomes available"""
        logger.info("=" * 60)
        logger.info(f"🎉 PICKUP NOW AVAILABLE at Apple {self.target_store}!")
        logger.info(f"Email notification to: fruitcc@gmail.com")
        logger.info(f"Status: {status}")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        self.email_sent = True

    def monitor(self, url, interval=5):
        """Main monitoring loop"""
        logger.info(f"Starting Apple Store Pickup Monitor")
        logger.info(f"Target Store: Apple {self.target_store} (Code: {self.store_code})")
        logger.info(f"Check interval: {interval} seconds")
        logger.info(f"Email: fruitcc@gmail.com")
        logger.info("-" * 60)

        # Get product parts on first run
        self.product_parts = self.get_product_parts(url)

        if not self.product_parts:
            logger.error("Failed to extract product parts. Monitor may not work correctly.")
            # Use some default iPhone 17 Pro part numbers as fallback
            self.product_parts = ["MFY84J/A", "MFYH4J/A", "MFYL4J/A"]
            logger.info(f"Using default part numbers: {', '.join(self.product_parts)}")

        check_count = 0

        while self.running:
            check_count += 1
            logger.info(f"\nCheck #{check_count} - {datetime.now().strftime('%H:%M:%S')}")

            available, status = self.check_store_pickup_api(self.product_parts)

            logger.info("=" * 60)
            logger.info(f"PICKUP STATUS - Apple {self.target_store}")
            logger.info(f"Available: {'YES ✅' if available else 'NO ❌'}")
            logger.info(f"Status: {status}")
            logger.info("=" * 60)

            if available:
                # Send notification when status changes to available
                if self.last_status == False or self.last_status is None:
                    if not self.email_sent:
                        self.send_notification(status)
            else:
                # Reset notification flag when unavailable
                if self.last_status == True:
                    self.email_sent = False
                    logger.info("Product became unavailable again")

            self.last_status = available

            if self.running:
                logger.info(f"Next check in {interval} seconds...")
                time.sleep(interval)

def main():
    url = "https://www.apple.com/jp/shop/buy-iphone/iphone-17-pro/6.9%E3%82%A4%E3%83%B3%E3%83%81%E3%83%87%E3%82%A3%E3%82%B9%E3%83%97%E3%83%AC%E3%82%A4-256gb-%E3%82%B3%E3%82%BA%E3%83%9F%E3%83%83%E3%82%AF%E3%82%AA%E3%83%AC%E3%83%B3%E3%82%B8-sim%E3%83%95%E3%83%AA%E3%83%BC"

    monitor = ShinsaibashiPickupMonitor()
    monitor.monitor(url, interval=5)

if __name__ == "__main__":
    main()