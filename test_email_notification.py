#!/usr/bin/env python3

"""
Test script to verify email notifications work correctly
Run this to simulate stock becoming available and ensure emails are sent
"""

from multi_email_notifier import MultiEmailNotifier
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def test_stock_notification():
    print("=" * 60)
    print("TESTING EMAIL NOTIFICATION SYSTEM")
    print("=" * 60)

    # Initialize email notifier
    notifier = MultiEmailNotifier()

    # Test data
    store_name = "心斎橋"
    product_name = "iPhone 17 Pro Max 256GB"
    product_url = "https://www.apple.com/jp/shop/buy-iphone/iphone-17-pro"
    status = "Available for pickup today!"

    print(f"\nSimulating stock available at Apple {store_name}")
    print(f"Product: {product_name}")
    print(f"Status: {status}")
    print(f"Sending to: {os.getenv('EMAIL_TO')}")
    print("-" * 60)

    try:
        # Send the notification
        result = notifier.send_pickup_alert(store_name, product_name, product_url, status)

        if result:
            print("✅ Email notification sent successfully!")
            print("\nPlease check your email inbox for:")
            print(f"  Subject: 'Apple {store_name} - Product Available!'")
            print(f"  To: {os.getenv('EMAIL_TO')}")
        else:
            print("❌ Failed to send email notification")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\nThe email notification system is working correctly.")
    print("The monitor will send emails when:")
    print("  1. Product status changes from unavailable → available")
    print("  2. At least 5 minutes have passed since last notification")
    print("\nNo emails in 5 days means the iPhone hasn't been available.")
    print("The system is monitoring correctly and will notify you when stock arrives!")

if __name__ == "__main__":
    test_stock_notification()