#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from multi_email_notifier import MultiEmailNotifier
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_multiple_emails():
    """Test sending to multiple email addresses"""

    print("=" * 60)
    print("Testing Multiple Email Recipients")
    print("=" * 60)

    # Show current configuration
    load_dotenv()
    current_emails = os.getenv('EMAIL_TO', 'fruitcc@gmail.com')
    print(f"\nCurrent EMAIL_TO setting: {current_emails}")

    # Example configurations
    print("\n📧 MULTIPLE EMAIL EXAMPLES:")
    print("\nYou can set EMAIL_TO in .env to any of these formats:")
    print("  1. Comma separated:")
    print("     EMAIL_TO=fruitcc@gmail.com, user2@gmail.com, user3@outlook.com")
    print("\n  2. Semicolon separated:")
    print("     EMAIL_TO=fruitcc@gmail.com; user2@gmail.com; user3@outlook.com")
    print("\n  3. Space separated:")
    print("     EMAIL_TO=fruitcc@gmail.com user2@gmail.com user3@outlook.com")

    # Test with current configuration
    print("\n" + "=" * 60)
    print("Testing with current configuration...")

    notifier = MultiEmailNotifier()

    # Test connection
    success, message = notifier.test_connection()
    if success:
        print(f"✅ {message}")

        # Ask if user wants to send test
        print("\nWould you like to send a test email to all recipients?")
        response = input("Enter 'yes' to send: ").strip().lower()

        if response == 'yes':
            print("\n📤 Sending test notification to all recipients...")

            success = notifier.send_pickup_alert(
                store_name="心斎橋",
                product_name="TEST - Multiple Recipients Test",
                product_url="https://www.apple.com/jp/",
                status="This is a test of multiple recipients"
            )

            if success:
                print("\n✅ Test emails sent successfully!")
                print(f"📬 Check inboxes for: {', '.join(notifier.email_to_list)}")
            else:
                print("\n❌ Some or all emails failed to send")
    else:
        print(f"❌ {message}")

    # Show how to update for multiple emails
    print("\n" + "=" * 60)
    print("TO ADD MULTIPLE RECIPIENTS:")
    print("1. Edit .env file")
    print("2. Update EMAIL_TO line with multiple emails:")
    print("   EMAIL_TO=fruitcc@gmail.com, friend1@gmail.com, friend2@yahoo.com")
    print("3. Save and restart the monitor")
    print("=" * 60)

if __name__ == "__main__":
    test_multiple_emails()