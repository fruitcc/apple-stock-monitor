#!/usr/bin/env python3

from dotenv import load_dotenv
from working_email_notifier import EmailNotifier
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_test():
    """Send a test email notification"""

    # Load environment variables
    load_dotenv()

    # Initialize email notifier
    notifier = EmailNotifier()

    print("=" * 60)
    print("Sending Test Email Notification")
    print("=" * 60)

    print("\n📧 Sending test notification email...")

    # Send test notification as if AirPods are available
    success = notifier.send_pickup_alert(
        store_name="心斎橋",
        product_name="AirPods Pro 3 (TEST NOTIFICATION)",
        product_url="https://www.apple.com/jp/shop/buy-airpods/airpods-pro-3",
        status="受け取れる日 本日 (Available for pickup TODAY)"
    )

    if success:
        print("\n✅ Test email sent successfully to fruitcc@gmail.com!")
        print("📬 Check your inbox (and spam folder if needed)")
        print("\nThe email includes:")
        print("  - HTML formatted message with Apple styling")
        print("  - Store location (心斎橋)")
        print("  - Product availability status")
        print("  - Direct link to Apple Store")
    else:
        print("\n❌ Failed to send test email")
        print("Check the error message above for details")

if __name__ == "__main__":
    send_test()