#!/usr/bin/env python3

import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class EmailNotifier:
    def __init__(self):
        """Initialize email notifier with environment variables"""
        load_dotenv()

        self.email_from = os.getenv('EMAIL_FROM')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_to = os.getenv('EMAIL_TO', 'fruitcc@gmail.com')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))

        self.last_notification_time = None
        self.min_notification_interval = 300  # 5 minutes

        # Check if credentials are configured
        self.is_configured = bool(self.email_from and self.email_password)

        if not self.is_configured:
            logger.warning("Email credentials not configured. Notifications will be logged only.")
            logger.info("To enable email, set EMAIL_FROM and EMAIL_PASSWORD in .env file")

    def send_pickup_alert(self, store_name, product_name, product_url, status):
        """Send email when product is available for pickup"""

        if not self.is_configured:
            logger.info("=" * 60)
            logger.info("📧 EMAIL SIMULATION (not configured)")
            logger.info(f"To: {self.email_to}")
            logger.info(f"Subject: Apple {store_name} - Product Available!")
            logger.info(f"Product: {product_name}")
            logger.info(f"Store: Apple {store_name}")
            logger.info(f"Status: {status}")
            logger.info("=" * 60)
            return True

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'🎉 Apple {store_name} - Pickup Available!'
            msg['From'] = self.email_from
            msg['To'] = self.email_to

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # HTML version
            html_body = f"""
            <html>
                <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; background-color: #f5f5f7;">
                    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h1 style="color: #1d1d1f; font-size: 28px; margin-bottom: 20px;">
                            🎉 Pickup Available at Apple {store_name}!
                        </h1>

                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h2 style="margin: 0; font-size: 20px;">Product Available Now!</h2>
                            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.95;">
                                {product_name}
                            </p>
                        </div>

                        <div style="background-color: #f5f5f7; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="color: #1d1d1f; margin-top: 0; font-size: 18px;">📍 Store Details</h3>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px 0; color: #6e6e73;">Store:</td>
                                    <td style="padding: 8px 0; color: #1d1d1f; font-weight: 600;">Apple {store_name}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #6e6e73;">Status:</td>
                                    <td style="padding: 8px 0; color: #00c853; font-weight: 600;">{status}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #6e6e73;">Time:</td>
                                    <td style="padding: 8px 0; color: #1d1d1f;">{timestamp}</td>
                                </tr>
                            </table>
                        </div>

                        <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px;">
                            <p style="margin: 0; color: #856404;">
                                <strong>⚡ Act Fast!</strong> High-demand products can go out of stock quickly.
                                Reserve for pickup now to secure your product.
                            </p>
                        </div>

                        <div style="text-align: center; margin-top: 30px;">
                            <a href="{product_url}" style="display: inline-block; background: #0071e3; color: white;
                               padding: 14px 32px; text-decoration: none; border-radius: 980px; font-weight: 500;
                               font-size: 16px;">
                                Go to Apple Store →
                            </a>
                        </div>

                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #d2d2d7;">

                        <div style="text-align: center; color: #6e6e73; font-size: 12px;">
                            <p>This is an automated notification from Apple Stock Monitor</p>
                            <p style="margin-top: 5px;">Monitoring stores: 心斎橋 & 梅田</p>
                        </div>
                    </div>
                </body>
            </html>
            """

            # Plain text version
            text_body = f"""
🎉 PICKUP AVAILABLE at Apple {store_name}!

Product: {product_name}
Store: Apple {store_name}
Status: {status}
Time: {timestamp}

⚡ Act fast! Reserve for pickup now:
{product_url}

---
Automated notification from Apple Stock Monitor
Monitoring: 心斎橋 & 梅田 stores
            """

            # Attach parts
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')

            msg.attach(text_part)
            msg.attach(html_part)

            # Send email
            context = ssl.create_default_context()

            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls(context=context)
                server.login(self.email_from, self.email_password)
                server.send_message(msg)

            logger.info(f"✅ Email sent successfully to {self.email_to}")
            self.last_notification_time = datetime.now()
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("❌ Email authentication failed. Check your EMAIL_FROM and EMAIL_PASSWORD in .env")
            logger.error("For Gmail, you need an App Password, not your regular password")
            return False

        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {e}")
            return False

        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False

    def test_connection(self):
        """Test email configuration"""
        if not self.is_configured:
            return False, "Email not configured. Set EMAIL_FROM and EMAIL_PASSWORD in .env"

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls(context=context)
                server.login(self.email_from, self.email_password)
            return True, "Email configuration is valid!"
        except Exception as e:
            return False, str(e)