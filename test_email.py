#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
from working_email_notifier import EmailNotifier
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_email_setup():
    """Test email configuration and send a test email"""

    print("=" * 60)
    print("Apple Stock Monitor - Email Configuration Test")
    print("=" * 60)

    # Load environment variables
    load_dotenv()

    # Check current configuration
    email_from = os.getenv('EMAIL_FROM')
    email_password = os.getenv('EMAIL_PASSWORD')
    email_to = os.getenv('EMAIL_TO', 'fruitcc@gmail.com')
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = os.getenv('SMTP_PORT', '587')

    print("\nCurrent Configuration:")
    print(f"  FROM: {email_from if email_from else '❌ Not set'}")
    print(f"  PASSWORD: {'✅ Set' if email_password else '❌ Not set'}")
    print(f"  TO: {email_to}")
    print(f"  SMTP Server: {smtp_server}")
    print(f"  SMTP Port: {smtp_port}")

    if not email_from or not email_password:
        print("\n❌ Email configuration incomplete!")
        print("\nTo set up email notifications:")
        print("1. Edit the .env file")
        print("2. Add your email credentials:")
        print("   EMAIL_FROM=your_email@gmail.com")
        print("   EMAIL_PASSWORD=your_app_password")
        print("\nFor Gmail:")
        print("  1. Enable 2-Factor Authentication")
        print("  2. Generate an App Password at:")
        print("     https://myaccount.google.com/apppasswords")
        print("  3. Use the 16-character app password (not your regular password)")
        return

    # Test connection
    print("\n📧 Testing email connection...")
    notifier = EmailNotifier()

    success, message = notifier.test_connection()

    if success:
        print(f"✅ {message}")

        # Ask if user wants to send test email
        print("\nWould you like to send a test notification email?")
        response = input("Enter 'yes' to send test email: ").strip().lower()

        if response == 'yes':
            print(f"\n📤 Sending test email to {email_to}...")

            # Send test notification
            success = notifier.send_pickup_alert(
                store_name="心斎橋",
                product_name="iPhone 17 Pro Max 256GB (TEST MESSAGE)",
                product_url="https://www.apple.com/jp/shop/buy-iphone/",
                status="TEST - This is a test notification"
            )

            if success:
                print(f"✅ Test email sent successfully to {email_to}!")
                print("   Check your inbox (and spam folder) for the notification.")
            else:
                print("❌ Failed to send test email. Check the error messages above.")
    else:
        print(f"❌ Connection test failed: {message}")
        print("\nTroubleshooting:")
        print("1. For Gmail, make sure you're using an App Password")
        print("2. Check that 2-Factor Authentication is enabled")
        print("3. Verify your SMTP settings are correct")
        print("4. Try regenerating your app password")


if __name__ == "__main__":
    test_email_setup()