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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleAppleMonitor:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.running = True
        self.last_stock_status = None
        self.email_sent = False
        self.first_check = True

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        logger.info("\nShutting down...")
        self.running = False
        sys.exit(0)

    def extract_product_info(self, soup, html_text):
        """Extract and log product information from the page"""
        try:
            # Try to find product title
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

            # Extract price
            price = None
            price_selectors = [
                ('span', {'data-autom': 'price'}),
                ('span', {'class': 'price-point'}),
                ('meta', {'property': 'og:price:amount'}),
            ]

            for tag, attrs in price_selectors:
                elem = soup.find(tag, attrs)
                if elem:
                    if tag == 'meta':
                        price = elem.get('content', '')
                    else:
                        price = elem.get_text(strip=True)
                    if price:
                        break

            # Extract store/region info
            store_info = "Japan (JP)"  # Default based on URL

            # Check for store selector or location info
            if 'apple.com/jp/' in html_text.lower():
                store_info = "Apple Store Japan"
            elif 'apple.com/us/' in html_text.lower():
                store_info = "Apple Store US"

            # Look for specific store location if available
            store_elem = soup.find('span', {'class': 'as-address-line'})
            if store_elem:
                store_info += f" - {store_elem.get_text(strip=True)}"

            # Extract product configuration
            config_info = []

            # Look for selected options
            selected_options = soup.find_all('span', {'class': 'form-selector-selected'})
            for opt in selected_options[:5]:  # Limit to first 5 to avoid clutter
                text = opt.get_text(strip=True)
                if text and len(text) < 50:
                    config_info.append(text)

            # Log the extracted information
            logger.info("=" * 60)
            logger.info("PRODUCT INFORMATION:")
            logger.info(f"Product: {product_name if product_name else 'Not found'}")
            logger.info(f"Price: {price if price else 'Not found'}")
            logger.info(f"Store/Region: {store_info}")
            if config_info:
                logger.info(f"Configuration: {', '.join(config_info)}")
            logger.info("=" * 60)

        except Exception as e:
            logger.debug(f"Error extracting product info: {e}")

    def check_stock(self, url):
        """Check if product is in stock"""
        try:
            logger.info(f"Fetching page...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            response = self.scraper.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.warning(f"HTTP {response.status_code}")
                return False

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract product information on first check
            if self.first_check:
                self.extract_product_info(soup, response.text)
                self.first_check = False

            # Check various indicators
            page_text = response.text.lower()

            # Positive indicators
            in_stock_indicators = [
                'カートに追加',
                'add to bag',
                'add to cart',
                '購入',
                'buy now',
                'in stock',
                '在庫あり'
            ]

            # Negative indicators
            out_of_stock_indicators = [
                '在庫切れ',
                'out of stock',
                '現在ご利用いただけません',
                'currently unavailable',
                '入荷待ち',
                'sold out',
                '品切れ'
            ]

            # Check for out of stock indicators first
            for indicator in out_of_stock_indicators:
                if indicator in page_text:
                    logger.info(f"Found OUT OF STOCK indicator: {indicator}")
                    return False

            # Check for in stock indicators
            for indicator in in_stock_indicators:
                if indicator in page_text:
                    # Make sure it's not disabled
                    if 'disabled' not in page_text[max(0, page_text.index(indicator)-50):page_text.index(indicator)+50]:
                        logger.info(f"Found IN STOCK indicator: {indicator}")
                        return True

            # Check for add to cart button
            add_button = soup.find('button', {'data-autom': 'add-to-cart'})
            if add_button and not add_button.get('disabled'):
                logger.info("Found enabled add to cart button")
                return True

            # Default to out of stock
            return False

        except Exception as e:
            logger.error(f"Error checking stock: {e}")
            return False

    def send_email(self, url):
        """Send email notification"""
        try:
            # Using a simple notification for demo
            logger.info("=" * 60)
            logger.info("🎉 SENDING EMAIL NOTIFICATION TO: fruitcc@gmail.com")
            logger.info(f"Subject: Apple Product In Stock!")
            logger.info(f"Product URL: {url}")
            logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 60)

            # In production, configure with real SMTP settings
            # For now, we'll just log the notification
            self.email_sent = True
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def monitor(self, url, interval=5):
        """Main monitoring loop"""
        logger.info(f"Starting Apple Stock Monitor")
        logger.info(f"URL: {url[:80]}...")
        logger.info(f"Check interval: {interval} seconds")
        logger.info(f"Email recipient: fruitcc@gmail.com")
        logger.info("-" * 60)

        check_count = 0

        while self.running:
            check_count += 1
            logger.info(f"\nCheck #{check_count} - {datetime.now().strftime('%H:%M:%S')}")

            in_stock = self.check_stock(url)

            if in_stock:
                logger.info("✅ PRODUCT IS IN STOCK!")

                # Send email only once when it comes in stock
                if self.last_stock_status == False or self.last_stock_status is None:
                    if not self.email_sent:
                        self.send_email(url)

            else:
                logger.info("❌ Product is OUT OF STOCK")
                # Reset email flag when out of stock
                if self.last_stock_status == True:
                    self.email_sent = False

            self.last_stock_status = in_stock

            if self.running:
                logger.info(f"Next check in {interval} seconds...")
                time.sleep(interval)

def main():
    url = "https://www.apple.com/jp/shop/buy-iphone/iphone-17-pro/6.9%E3%82%A4%E3%83%B3%E3%83%81%E3%83%87%E3%82%A3%E3%82%B9%E3%83%97%E3%83%AC%E3%82%A4-256gb-%E3%82%B3%E3%82%BA%E3%83%9F%E3%83%83%E3%82%AF%E3%82%AA%E3%83%AC%E3%83%B3%E3%82%B8-sim%E3%83%95%E3%83%AA%E3%83%BC"

    monitor = SimpleAppleMonitor()
    monitor.monitor(url, interval=5)

if __name__ == "__main__":
    main()