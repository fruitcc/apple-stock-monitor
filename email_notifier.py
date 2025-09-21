import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class EmailNotifier:
    def __init__(self, smtp_server: str, smtp_port: int, email_from: str,
                 email_password: str, email_to: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_from = email_from
        self.email_password = email_password
        self.email_to = email_to
        self.last_notification_time = None
        self.min_notification_interval = 300  # 5 minutes between notifications

    def _should_send_notification(self) -> bool:
        """Check if enough time has passed since last notification"""
        if self.last_notification_time is None:
            return True

        time_since_last = (datetime.now() - self.last_notification_time).total_seconds()
        return time_since_last >= self.min_notification_interval

    def send_stock_alert(self, product_url: str, stock_info: Dict[str, Any]) -> bool:
        """Send email notification when product is in stock"""

        if not self._should_send_notification():
            logger.info("Skipping notification - too soon since last alert")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = '🎉 Apple Product In Stock Alert!'
            msg['From'] = self.email_from
            msg['To'] = self.email_to

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #0071e3;">Apple Product Stock Alert! 🎉</h2>
                    <p style="font-size: 16px;">Good news! The Apple product you're monitoring is now in stock!</p>

                    <div style="background-color: #f5f5f7; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p><strong>Product URL:</strong></p>
                        <a href="{product_url}" style="color: #0071e3; text-decoration: none; font-size: 14px;">
                            {product_url}
                        </a>
                    </div>

                    <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #2e7d32;">Stock Details:</h3>
                        <ul>
                            <li><strong>Status:</strong> In Stock ✅</li>
                            <li><strong>Detection Method:</strong> {stock_info.get('method', 'Unknown')}</li>
                            <li><strong>Indicator:</strong> {stock_info.get('details', {}).get('indicator', 'N/A')}</li>
                            <li><strong>Timestamp:</strong> {timestamp}</li>
                        </ul>
                    </div>

                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p style="color: #856404; margin: 0;">
                            <strong>⚡ Act fast!</strong> Apple products can go out of stock quickly.
                        </p>
                    </div>

                    <div style="text-align: center; margin-top: 30px;">
                        <a href="{product_url}" style="background-color: #0071e3; color: white; padding: 12px 30px;
                           text-decoration: none; border-radius: 20px; font-weight: bold;">
                            Go to Product Page
                        </a>
                    </div>

                    <hr style="margin-top: 40px; border: none; border-top: 1px solid #d2d2d7;">
                    <p style="font-size: 12px; color: #86868b; text-align: center;">
                        This is an automated notification from Apple Stock Monitor
                    </p>
                </body>
            </html>
            """

            text_body = f"""
            Apple Product Stock Alert!

            Good news! The Apple product you're monitoring is now in stock!

            Product URL: {product_url}

            Stock Details:
            - Status: In Stock ✅
            - Detection Method: {stock_info.get('method', 'Unknown')}
            - Indicator: {stock_info.get('details', {}).get('indicator', 'N/A')}
            - Timestamp: {timestamp}

            Act fast! Apple products can go out of stock quickly.

            ---
            This is an automated notification from Apple Stock Monitor
            """

            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')

            msg.attach(text_part)
            msg.attach(html_part)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)

            self.last_notification_time = datetime.now()
            logger.info(f"Stock alert email sent successfully to {self.email_to}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_error_notification(self, error_message: str) -> bool:
        """Send email notification for critical errors"""
        try:
            msg = MIMEMultipart()
            msg['Subject'] = '⚠️ Apple Stock Monitor Error'
            msg['From'] = self.email_from
            msg['To'] = self.email_to

            body = f"""
            Apple Stock Monitor Error Report

            An error occurred while monitoring Apple products:

            Error: {error_message}
            Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

            The monitor will continue running and retry.

            ---
            This is an automated error notification
            """

            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)

            logger.info("Error notification email sent")
            return True

        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
            return False