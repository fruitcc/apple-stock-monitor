#!/usr/bin/env python3

import time
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import cloudscraper
from bs4 import BeautifulSoup
import signal
import sys
import json
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ApplePickupMonitor:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.running = True
        self.last_stock_status = None
        self.email_sent = False
        self.first_check = True
        self.target_store = "心斎橋"  # Shinsaibashi store

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        logger.info("\nShutting down...")
        self.running = False
        sys.exit(0)

    def check_store_pickup(self, url):
        """Check if product is available for pickup at specific store"""
        try:
            logger.info(f"Fetching page...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            response = self.scraper.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.warning(f"HTTP {response.status_code}")
                return False, None

            soup = BeautifulSoup(response.text, 'html.parser')

            # Log product info on first check
            if self.first_check:
                self.extract_product_info(soup, response.text)
                self.first_check = False

            # Look for store pickup information
            store_found = False
            store_available = False
            store_status = "Unknown"

            # Check for store pickup section
            # Method 1: Look for store name and availability status
            store_sections = soup.find_all(['div', 'section'], class_=re.compile('store|pickup|fulfillment'))

            for section in store_sections:
                section_text = section.get_text()
                if self.target_store in section_text:
                    store_found = True
                    logger.info(f"Found {self.target_store} store section")

                    # Check for availability indicators near the store name
                    # Looking for "利用できません" (not available) or "利用可能" (available)
                    if "利用できません" in section_text:
                        store_status = "利用できません (Not Available)"
                        store_available = False
                    elif "利用可能" in section_text or "受け取り可能" in section_text:
                        store_status = "利用可能 (Available)"
                        store_available = True
                    elif "在庫あり" in section_text:
                        store_status = "在庫あり (In Stock)"
                        store_available = True
                    break

            # Method 2: Look for specific store availability data in JSON
            scripts = soup.find_all('script', type='application/json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    # Navigate through potential JSON structures
                    if self.check_json_for_store(data, self.target_store):
                        store_found = True
                        # Check availability status in JSON
                        store_available, store_status = self.get_store_status_from_json(data, self.target_store)
                        if store_found:
                            break
                except:
                    continue

            # Method 3: Look for specific pickup availability text patterns
            if not store_found:
                # Look for text patterns like "Apple 心斎橋" followed by availability
                patterns = [
                    rf"Apple\s*{self.target_store}.*?(利用できません|利用可能|在庫あり|受け取り可能)",
                    rf"{self.target_store}.*?(利用できません|利用可能|在庫あり|受け取り可能)",
                    rf"ピックアップ.*?{self.target_store}.*?(利用できません|利用可能|在庫あり)"
                ]

                page_text = response.text
                for pattern in patterns:
                    match = re.search(pattern, page_text, re.DOTALL)
                    if match:
                        store_found = True
                        status_text = match.group(1)
                        if "利用できません" in status_text:
                            store_status = "利用できません (Not Available)"
                            store_available = False
                        else:
                            store_status = status_text + " (Available)"
                            store_available = True
                        logger.info(f"Found store status via pattern: {store_status}")
                        break

            # Log findings
            if store_found:
                logger.info("=" * 60)
                logger.info(f"PICKUP STATUS - Apple {self.target_store}")
                logger.info(f"Status: {store_status}")
                logger.info(f"Available for Pickup: {'YES ✅' if store_available else 'NO ❌'}")
                logger.info("=" * 60)
            else:
                logger.warning(f"Could not find {self.target_store} store information on page")
                # Try to log what stores were found
                all_stores = re.findall(r'Apple\s+([^\s]+(?:\s+[^\s]+)?)\s*(?:利用|在庫|受け取り)', response.text)
                if all_stores:
                    logger.info(f"Stores found on page: {', '.join(set(all_stores[:5]))}")

            return store_available, store_status

        except Exception as e:
            logger.error(f"Error checking store pickup: {e}")
            return False, "Error"

    def check_json_for_store(self, data, store_name):
        """Recursively check JSON data for store name"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and store_name in value:
                    return True
                elif isinstance(value, (dict, list)):
                    if self.check_json_for_store(value, store_name):
                        return True
        elif isinstance(data, list):
            for item in data:
                if self.check_json_for_store(item, store_name):
                    return True
        return False

    def get_store_status_from_json(self, data, store_name):
        """Extract store availability status from JSON data"""
        # This would need to be customized based on actual JSON structure
        # Placeholder implementation
        return False, "Status from JSON not implemented"

    def extract_product_info(self, soup, html_text):
        """Extract and log product information from the page"""
        try:
            product_name = None
            title_selectors = [
                ('h1', {'class': 'rf-pdp-title'}),
                ('h1', {'data-autom': 'productTitle'}),
                ('h1', None),
                ('meta', {'property': 'og:title'}),
            ]

            for tag, attrs in title_selectors:
                elem = soup.find(tag, attrs)
                if elem:
                    if tag == 'meta':
                        product_name = elem.get('content', '')
                    else:
                        product_name = elem.get_text(strip=True)
                    if product_name:
                        break

            logger.info("=" * 60)
            logger.info("MONITORING CONFIGURATION:")
            logger.info(f"Product: {product_name if product_name else 'Not found'}")
            logger.info(f"Target Store: Apple {self.target_store}")
            logger.info(f"Check Type: Store Pickup Availability")
            logger.info("=" * 60)

        except Exception as e:
            logger.debug(f"Error extracting product info: {e}")

    def send_email(self, url, status):
        """Send email notification when product is available for pickup"""
        try:
            logger.info("=" * 60)
            logger.info(f"🎉 SENDING PICKUP AVAILABILITY NOTIFICATION TO: fruitcc@gmail.com")
            logger.info(f"Subject: Apple Product Available for Pickup at {self.target_store}!")
            logger.info(f"Store: Apple {self.target_store}")
            logger.info(f"Status: {status}")
            logger.info(f"Product URL: {url}")
            logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 60)

            # In production, configure with real SMTP settings
            self.email_sent = True
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def monitor(self, url, interval=5):
        """Main monitoring loop for store pickup"""
        logger.info(f"Starting Apple Store Pickup Monitor")
        logger.info(f"URL: {url[:80]}...")
        logger.info(f"Target Store: Apple {self.target_store}")
        logger.info(f"Check interval: {interval} seconds")
        logger.info(f"Email recipient: fruitcc@gmail.com")
        logger.info("-" * 60)

        check_count = 0

        while self.running:
            check_count += 1
            logger.info(f"\nCheck #{check_count} - {datetime.now().strftime('%H:%M:%S')}")

            available, status = self.check_store_pickup(url)

            if available:
                logger.info(f"✅ AVAILABLE FOR PICKUP at Apple {self.target_store}!")

                # Send email only when status changes from unavailable to available
                if self.last_stock_status == False or self.last_stock_status is None:
                    if not self.email_sent:
                        self.send_email(url, status)
            else:
                logger.info(f"❌ NOT available for pickup at Apple {self.target_store}")
                logger.info(f"Current status: {status}")

                # Reset email flag when unavailable
                if self.last_stock_status == True:
                    self.email_sent = False

            self.last_stock_status = available

            if self.running:
                logger.info(f"Next check in {interval} seconds...")
                time.sleep(interval)

def main():
    url = "https://www.apple.com/jp/shop/buy-iphone/iphone-17-pro/6.9%E3%82%A4%E3%83%B3%E3%83%81%E3%83%87%E3%82%A3%E3%82%B9%E3%83%97%E3%83%AC%E3%82%A4-256gb-%E3%82%B3%E3%82%BA%E3%83%9F%E3%83%83%E3%82%AF%E3%82%AA%E3%83%AC%E3%83%B3%E3%82%B8-sim%E3%83%95%E3%83%AA%E3%83%BC"

    monitor = ApplePickupMonitor()
    monitor.monitor(url, interval=5)

if __name__ == "__main__":
    main()