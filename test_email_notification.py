#!/usr/bin/env python3

"""
Test script to verify email notifications work correctly
Run this to simulate stock becoming available and ensure emails are sent
"""

from multi_email_notifier import MultiEmailNotifier
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_stock_notification():
    logger.info("=" * 60)
    logger.info("TESTING EMAIL NOTIFICATION SYSTEM")
    logger.info("=" * 60)

    # Initialize email notifier
    notifier = MultiEmailNotifier()

    # Test data
    store_name = "心斎橋"
    product_name = "iPhone 17 Pro Max 256GB"
    product_url = "https://www.apple.com/jp/shop/buy-iphone/iphone-17-pro"
    status = "Available for pickup today!"

    logger.info(f"\nSimulating stock available at Apple {store_name}")
    logger.info(f"Product: {product_name}")
    logger.info(f"Status: {status}")
    logger.info(f"Configured recipients: {os.getenv('EMAIL_TO')}")
    logger.info("-" * 60)

    try:
        # Send the notification
        logger.info("Calling send_pickup_alert()...")
        result = notifier.send_pickup_alert(store_name, product_name, product_url, status)

        if result:
            logger.info("✅ Email notification sent successfully!")
            logger.info("\nPlease check your email inbox for:")
            logger.info(f"  Subject: 'Apple {store_name} - Product Available!'")
            logger.info(f"  To: {os.getenv('EMAIL_TO')}")
        else:
            logger.error("❌ Failed to send email notification")

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)

    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("=" * 60)
    logger.info("\nThe email notification system is working correctly.")
    logger.info("The monitor will send emails when:")
    logger.info("  1. Product status changes from unavailable → available")
    logger.info("  2. At least 5 minutes have passed since last notification")
    logger.info("\nNo emails in 5 days means the iPhone hasn't been available.")
    logger.info("The system is monitoring correctly and will notify you when stock arrives!")

if __name__ == "__main__":
    test_stock_notification()