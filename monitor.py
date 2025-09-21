#!/usr/bin/env python3

import os
import sys
import time
import signal
import logging
import argparse
from datetime import datetime
from typing import Optional, List
from dotenv import load_dotenv

from scraper import AppleStockChecker
from email_notifier import EmailNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('apple_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AppleStockMonitor:
    def __init__(self, check_interval: int = 5, headless: bool = True):
        """
        Initialize the Apple Stock Monitor

        Args:
            check_interval: Seconds between checks (default 5)
            headless: Run browser in headless mode (default True)
        """
        self.check_interval = check_interval
        self.headless = headless
        self.running = False
        self.checker = None
        self.notifier = None
        self.products_in_stock = set()
        self.consecutive_errors = 0
        self.max_consecutive_errors = 10

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("Received shutdown signal, cleaning up...")
        self.stop()
        sys.exit(0)

    def setup_email(self, smtp_server: str, smtp_port: int, email_from: str,
                   email_password: str, email_to: str) -> bool:
        """Setup email notifier"""
        try:
            self.notifier = EmailNotifier(
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                email_from=email_from,
                email_password=email_password,
                email_to=email_to
            )
            logger.info("Email notifier configured successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to setup email notifier: {e}")
            return False

    def monitor_products(self, urls: List[str]):
        """
        Monitor multiple product URLs for stock availability

        Args:
            urls: List of Apple product URLs to monitor
        """
        self.running = True
        self.checker = AppleStockChecker(headless=self.headless)

        logger.info(f"Starting monitoring for {len(urls)} product(s)")
        logger.info(f"Check interval: {self.check_interval} seconds")
        logger.info(f"Email notifications: {'Enabled' if self.notifier else 'Disabled'}")

        check_count = 0

        while self.running:
            try:
                check_count += 1
                logger.info(f"\n{'='*50}")
                logger.info(f"Check #{check_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*50}")

                for url in urls:
                    if not self.running:
                        break

                    try:
                        logger.info(f"Checking: {url[:80]}...")

                        result = self.checker.check_stock(url)

                        if result['error']:
                            logger.warning(f"Error checking stock: {result['error']}")
                            self.consecutive_errors += 1

                            if self.consecutive_errors >= self.max_consecutive_errors:
                                logger.error("Too many consecutive errors, restarting checker...")
                                self.checker.cleanup()
                                self.checker = AppleStockChecker(headless=self.headless)
                                self.consecutive_errors = 0

                                if self.notifier:
                                    self.notifier.send_error_notification(
                                        f"Too many errors, checker restarted after {self.max_consecutive_errors} failures"
                                    )

                        else:
                            self.consecutive_errors = 0

                            if result['in_stock']:
                                logger.info(f"✅ IN STOCK! Method: {result['method']}")
                                logger.info(f"   Details: {result['details']}")

                                if url not in self.products_in_stock:
                                    self.products_in_stock.add(url)
                                    logger.info("🎉 NEW STOCK DETECTED!")

                                    if self.notifier:
                                        if self.notifier.send_stock_alert(url, result):
                                            logger.info("📧 Email notification sent!")
                                        else:
                                            logger.error("Failed to send email notification")
                                else:
                                    logger.info("Product already known to be in stock")

                            else:
                                logger.info(f"❌ OUT OF STOCK - Method: {result['method']}")

                                if url in self.products_in_stock:
                                    self.products_in_stock.remove(url)
                                    logger.info("Product went out of stock")

                    except KeyboardInterrupt:
                        raise
                    except Exception as e:
                        logger.error(f"Unexpected error checking {url}: {e}")
                        self.consecutive_errors += 1

                if self.running:
                    logger.info(f"\nNext check in {self.check_interval} seconds...")
                    logger.info(f"Products in stock: {len(self.products_in_stock)}")
                    time.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("Monitoring interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitoring loop: {e}")
                if self.running:
                    time.sleep(self.check_interval)

        self.stop()

    def stop(self):
        """Stop monitoring and cleanup resources"""
        self.running = False
        if self.checker:
            self.checker.cleanup()
        logger.info("Monitoring stopped")


def main():
    parser = argparse.ArgumentParser(description='Apple Stock Monitor')
    parser.add_argument('--urls', nargs='+', help='Product URLs to monitor')
    parser.add_argument('--interval', type=int, default=5, help='Check interval in seconds (default: 5)')
    parser.add_argument('--no-headless', action='store_true', help='Show browser window')
    parser.add_argument('--env-file', default='.env', help='Path to .env file')

    args = parser.parse_args()

    load_dotenv(args.env_file)

    default_urls = [
        "https://www.apple.com/jp/shop/buy-iphone/iphone-17-pro/6.9%E3%82%A4%E3%83%B3%E3%83%81%E3%83%87%E3%82%A3%E3%82%B9%E3%83%97%E3%83%AC%E3%82%A4-256gb-%E3%82%B3%E3%82%BA%E3%83%9F%E3%83%83%E3%82%AF%E3%82%AA%E3%83%AC%E3%83%B3%E3%82%B8-sim%E3%83%95%E3%83%AA%E3%83%BC"
    ]

    urls = args.urls if args.urls else default_urls

    monitor = AppleStockMonitor(
        check_interval=args.interval,
        headless=not args.no_headless
    )

    email_from = os.getenv('EMAIL_FROM')
    email_password = os.getenv('EMAIL_PASSWORD')
    email_to = os.getenv('EMAIL_TO', 'fruitcc@gmail.com')
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))

    if email_from and email_password:
        if monitor.setup_email(smtp_server, smtp_port, email_from, email_password, email_to):
            logger.info(f"Email notifications will be sent to: {email_to}")
        else:
            logger.warning("Email setup failed, continuing without notifications")
    else:
        logger.warning("Email credentials not found in environment, notifications disabled")
        logger.info("To enable email notifications, create a .env file with:")
        logger.info("  EMAIL_FROM=your_email@gmail.com")
        logger.info("  EMAIL_PASSWORD=your_app_password")

    try:
        monitor.monitor_products(urls)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()