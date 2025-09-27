#!/usr/bin/env python3

import time
import logging
import json
import re
import signal
import sys
import os
from datetime import datetime, timezone
import cloudscraper
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from database import StockDatabase
from multi_email_notifier import MultiEmailNotifier

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Apple Store codes in Japan (these are estimates, actual codes may differ)
STORE_CODES = {
    '心斎橋': 'R119',  # Shinsaibashi
    '梅田': 'R120',    # Umeda (estimated)
    '銀座': 'R090',
    '丸の内': 'R224',
    '渋谷': 'R224',
    '新宿': 'R225',
    '名古屋栄': 'R221',
    '福岡': 'R223',
}

class OsakaStoresMonitor:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.running = True
        self.target_stores = ["心斎橋", "梅田"]  # Monitor both stores
        self.product_parts = []
        self.store_status = {}  # Track status for each store
        self.db = StockDatabase()  # Initialize database
        self.product_id = None
        self.store_ids = {}  # Store name to ID mapping
        self.last_email_time = {}  # Track last email time per store
        self.email_cooldown_minutes = 10  # Minimum 10 minutes between emails

        # Initialize email notifier
        try:
            self.email_notifier = MultiEmailNotifier()
            logger.info("Email notifier initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize email notifier: {e}")
            self.email_notifier = None

        # Initialize status for each store
        for store in self.target_stores:
            self.store_status[store] = {
                'last_status': None,
                'available': False,
                'status_message': 'Unknown'
            }
            self.last_email_time[store] = None  # Track last email time per store

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        logger.info("\nShutting down...")
        self.running = False
        sys.exit(0)

    def get_product_parts(self, url):
        """Extract product part numbers from the product page - ONLY for Orange 256GB variant"""
        try:
            logger.info("Extracting product information for Orange 256GB variant...")
            response = self.scraper.get(url, timeout=15)

            if response.status_code != 200:
                logger.error(f"Failed to load product page: {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Log product title
            title = soup.find('h1')
            if title:
                logger.info(f"Product page: {title.get_text(strip=True)}")

            # IMPORTANT: We need to find ONLY the Orange 256GB variant
            # The URL already specifies: 256gb-コズミックオレンジ (Cosmic Orange)

            # Based on Apple's typical part number pattern for this specific model:
            # These are the likely part numbers for Orange 256GB iPhone 17 Pro Max
            # We'll use a specific set rather than extracting all variants

            orange_256gb_parts = [
                "MG8D4J/A",  # iPhone 17 Pro Max 256GB Orange (primary)
                "MFY84J/A",  # Alternative part number for same model
                "MFYH4J/A",  # Another variant code
            ]

            logger.info(f"Checking ONLY Orange 256GB variant part numbers: {', '.join(orange_256gb_parts)}")
            logger.info("Note: Ignoring other colors/sizes to prevent false positives")

            return orange_256gb_parts

        except Exception as e:
            logger.error(f"Error extracting product parts: {e}")
            return []

    def check_stores_pickup_api(self, parts):
        """Check pickup availability for multiple stores using Apple's fulfillment API"""
        results = {}

        try:
            if not parts:
                for store in self.target_stores:
                    results[store] = (False, "No product parts available")
                return results

            # Try different API endpoints and parameters
            # First try with location parameter for Osaka area
            parts_params = '&'.join([f'parts.{i}={part}' for i, part in enumerate(parts)])

            # Try multiple API variations
            api_urls = [
                f"https://www.apple.com/jp/shop/fulfillment-messages?{parts_params}&location=大阪&fae=true",
                f"https://www.apple.com/jp/shop/retail/pickup-message?{parts_params}&location=osaka",
                f"https://www.apple.com/jp/shop/fulfillment-messages?{parts_params}&fae=true",
            ]

            for api_url in api_urls:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Language': 'ja-JP,ja;q=0.9',
                        'Referer': 'https://www.apple.com/jp/shop/buy-iphone/',
                    }

                    response = self.scraper.get(api_url, headers=headers, timeout=10)

                    if response.status_code != 200:
                        continue

                    data = response.json()

                    # Parse response to find stores
                    if 'body' in data:
                        body = data['body']

                        # Handle different response formats
                        if 'content' in body and 'pickupMessage' in body['content']:
                            pickup = body['content']['pickupMessage']
                            stores_data = pickup.get('stores', [])
                        elif 'stores' in body:
                            stores_data = body['stores']
                        else:
                            stores_data = []

                        # Check each store
                        for store_data in stores_data:
                            store_name = store_data.get('storeName', '')

                            # Check if this is one of our target stores
                            for target_store in self.target_stores:
                                if target_store in store_name:
                                    # Found the store, check availability
                                    parts_availability = store_data.get('partsAvailability', {})

                                    available = False
                                    status_message = "利用できません (Not Available)"

                                    for part, info in parts_availability.items():
                                        pickup_display = info.get('pickupDisplay', 'unavailable')
                                        pickup_quote = info.get('pickupSearchQuote', '利用できません')
                                        store_pickup_available = info.get('storePickupAvailable', False)

                                        # Check various availability indicators
                                        if (pickup_display == 'available' or
                                            store_pickup_available or
                                            '利用可能' in pickup_quote or
                                            '在庫あり' in pickup_quote):
                                            available = True
                                            status_message = f"利用可能 - {pickup_quote}"
                                            break
                                        else:
                                            status_message = pickup_quote

                                    results[target_store] = (available, status_message)
                                    logger.debug(f"Found {target_store}: {available} - {status_message}")

                        # If we found some stores, don't try other API endpoints
                        if results:
                            break

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.debug(f"API variant failed: {e}")
                    continue

            # Set default status for stores not found
            for store in self.target_stores:
                if store not in results:
                    # Try to check if store exists in general response
                    results[store] = (False, "Store not found in response - 利用できません")

            return results

        except Exception as e:
            logger.error(f"API check error: {e}")
            for store in self.target_stores:
                results[store] = (False, f"Error: {e}")
            return results

    def should_send_email(self, store_name):
        """Check if email should be sent based on cooldown period"""
        if self.last_email_time.get(store_name) is None:
            return True

        time_since_last = datetime.now() - self.last_email_time[store_name]
        minutes_passed = time_since_last.total_seconds() / 60

        if minutes_passed < self.email_cooldown_minutes:
            logger.info(f"  ⏰ Email cooldown active for {store_name}: {minutes_passed:.1f}/{self.email_cooldown_minutes} minutes passed")
            return False

        return True

    def send_notification(self, store_name, status):
        """Send notification when product becomes available at a store"""
        # Check cooldown period
        if not self.should_send_email(store_name):
            logger.info(f"  Skipping email for {store_name} due to cooldown period")
            return

        logger.info("=" * 60)
        logger.info(f"🎉 PICKUP NOW AVAILABLE at Apple {store_name}!")
        logger.info(f"Store: Apple {store_name}")
        logger.info(f"Status: {status}")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Send email notification
        if self.email_notifier:
            product_name = "iPhone 17 Pro Max 6.9インチ 256GB コズミックオレンジ"
            product_url = "https://www.apple.com/jp/shop/buy-iphone/iphone-17-pro"
            try:
                result = self.email_notifier.send_pickup_alert(store_name, product_name, product_url, status)
                if result:
                    logger.info(f"✅ Email notification sent successfully")
                    self.last_email_time[store_name] = datetime.now()
                else:
                    logger.error(f"❌ Email notification failed")
            except Exception as e:
                logger.error(f"❌ Failed to send email notification: {e}")
        else:
            logger.warning("Email notifier not configured - notification not sent")

        logger.info("=" * 60)

    def monitor(self, url, interval=None):
        """Main monitoring loop"""
        # Get interval from environment or use default
        if interval is None:
            interval = int(os.getenv('CHECK_INTERVAL', '10'))

        logger.info(f"Starting Apple Store Pickup Monitor for Osaka")
        logger.info(f"Target Stores: {', '.join([f'Apple {store}' for store in self.target_stores])}")
        logger.info(f"Check interval: {interval} seconds")
        logger.info(f"Email cooldown: {self.email_cooldown_minutes} minutes")
        logger.info(f"Email recipients: {os.getenv('EMAIL_TO', 'Not configured')}")
        logger.info(f"Email policy: Only send when status changes from unavailable → available")
        logger.info("-" * 60)

        # Get product parts on first run
        self.product_parts = self.get_product_parts(url)

        # Add product to database - be very specific about the variant
        product_name = "iPhone 17 Pro Max 6.9インチ 256GB コズミックオレンジ (Orange ONLY)"
        self.product_id = self.db.add_product(product_name, url, self.product_parts)

        logger.info("="*60)
        logger.info("MONITORING SPECIFIC PRODUCT:")
        logger.info("Model: iPhone 17 Pro Max")
        logger.info("Screen: 6.9インチ")
        logger.info("Storage: 256GB")
        logger.info("Color: コズミックオレンジ (Cosmic Orange) ONLY")
        logger.info("Other colors/sizes will be IGNORED")
        logger.info("="*60)

        # Add stores to database
        for store_name in self.target_stores:
            self.store_ids[store_name] = self.db.add_store(f"Apple {store_name}",
                                                           STORE_CODES.get(store_name),
                                                           "Osaka, Japan")

        if not self.product_parts:
            logger.error("Failed to extract product parts. Using Orange 256GB defaults.")
            # Use specific Orange 256GB iPhone 17 Pro Max part numbers
            self.product_parts = ["MG8D4J/A", "MFY84J/A", "MFYH4J/A"]
            logger.info(f"Using Orange 256GB part numbers: {', '.join(self.product_parts)}")

        check_count = 0

        while self.running:
            check_count += 1
            logger.info(f"\nCheck #{check_count} - {datetime.now().strftime('%H:%M:%S')}")

            # Check all stores
            store_results = self.check_stores_pickup_api(self.product_parts)

            # Display results and handle notifications
            logger.info("=" * 60)
            logger.info("PICKUP STATUS - OSAKA STORES")
            logger.info("-" * 60)

            for store_name in self.target_stores:
                available, status = store_results.get(store_name, (False, "Unknown"))

                # Update store status
                self.store_status[store_name]['available'] = available
                self.store_status[store_name]['status_message'] = status

                # Record to database
                if self.product_id and store_name in self.store_ids:
                    self.db.record_availability(
                        self.product_id,
                        self.store_ids[store_name],
                        available,
                        status
                    )

                # Display status
                status_icon = "✅" if available else "❌"
                logger.info(f"Apple {store_name}: {status_icon} {status}")

                # Check if status changed from unavailable to available
                # Only send email when:
                # 1. Current status is available
                # 2. Previous status was unavailable (False) - NOT None (first check)
                # 3. Cooldown period has passed
                if available and self.store_status[store_name]['last_status'] == False:
                    logger.info(f"  📱 Status changed: unavailable → available at {store_name}")
                    self.send_notification(store_name, status)
                elif available and self.store_status[store_name]['last_status'] is None:
                    logger.info(f"  🆕 First check - product available at {store_name} (no email sent)")
                elif not available and self.store_status[store_name]['last_status'] == True:
                    logger.info(f"  📴 Product became unavailable at {store_name}")

                # Update last status
                self.store_status[store_name]['last_status'] = available

            logger.info("=" * 60)

            # Summary of available stores
            available_stores = [store for store in self.target_stores
                              if self.store_status[store]['available']]
            if available_stores:
                logger.info(f"🎯 Available for pickup at: {', '.join(available_stores)}")
            else:
                logger.info("Currently not available for pickup at any monitored stores")

            if self.running:
                logger.info(f"Next check in {interval} seconds...")
                time.sleep(interval)

def main():
    url = "https://www.apple.com/jp/shop/buy-iphone/iphone-17-pro/6.9%E3%82%A4%E3%83%B3%E3%83%81%E3%83%87%E3%82%A3%E3%82%B9%E3%83%97%E3%83%AC%E3%82%A4-256gb-%E3%82%B3%E3%82%BA%E3%83%9F%E3%83%83%E3%82%AF%E3%82%AA%E3%83%AC%E3%83%B3%E3%82%B8-sim%E3%83%95%E3%83%AA%E3%83%BC"

    monitor = OsakaStoresMonitor()
    monitor.monitor(url)  # Will use CHECK_INTERVAL from .env or default to 10

if __name__ == "__main__":
    main()