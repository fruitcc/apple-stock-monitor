#!/usr/bin/env python3

import logging
import sys
from scraper import AppleStockChecker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_scraper():
    """Test the scraper with the provided URL"""

    test_url = "https://www.apple.com/jp/shop/buy-iphone/iphone-17-pro/6.9%E3%82%A4%E3%83%B3%E3%83%81%E3%83%87%E3%82%A3%E3%82%B9%E3%83%97%E3%83%AC%E3%82%A4-256gb-%E3%82%B3%E3%82%BA%E3%83%9F%E3%83%83%E3%82%AF%E3%82%AA%E3%83%AC%E3%83%B3%E3%82%B8-sim%E3%83%95%E3%83%AA%E3%83%BC"

    logger.info("Starting Apple Stock Checker Test")
    logger.info(f"Testing URL: {test_url[:80]}...")

    checker = AppleStockChecker(headless=False)  # Show browser for testing

    try:
        logger.info("\nTesting Selenium method...")
        result = checker.check_stock_selenium(test_url)

        logger.info(f"\nSelenium Results:")
        logger.info(f"  In Stock: {result['in_stock']}")
        logger.info(f"  Method: {result['method']}")
        logger.info(f"  Error: {result['error']}")
        logger.info(f"  Details: {result['details']}")

        if result['error'] and 'cloudflare' in str(result['error']).lower():
            logger.info("\nCloudflare detected, testing cloudscraper fallback...")
            result = checker.check_stock_cloudscraper(test_url)

            logger.info(f"\nCloudscraper Results:")
            logger.info(f"  In Stock: {result['in_stock']}")
            logger.info(f"  Method: {result['method']}")
            logger.info(f"  Error: {result['error']}")
            logger.info(f"  Details: {result['details']}")

        logger.info("\n" + "="*50)
        logger.info("FINAL RESULT:")
        if result['in_stock']:
            logger.info("✅ Product is IN STOCK!")
        else:
            logger.info("❌ Product is OUT OF STOCK")
        logger.info("="*50)

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)

    finally:
        checker.cleanup()

    logger.info("\nTest completed successfully")


if __name__ == "__main__":
    test_scraper()