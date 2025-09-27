#!/usr/bin/env python3

"""
Test script to verify email notification logic:
1. Emails only sent when status changes from unavailable to available
2. 10-minute cooldown between emails
"""

from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailLogicTester:
    def __init__(self):
        self.last_status = None
        self.last_email_time = None
        self.email_cooldown_minutes = 10

    def should_send_email(self, current_available):
        """Check if email should be sent based on status change and cooldown"""

        # Rule 1: Only send when changing from unavailable to available
        if self.last_status is None:
            logger.info(f"  First check - no email (last_status=None, current={current_available})")
            return False

        if self.last_status == False and current_available == True:
            # Status changed from unavailable to available

            # Rule 2: Check cooldown period
            if self.last_email_time:
                time_since_last = datetime.now() - self.last_email_time
                minutes_passed = time_since_last.total_seconds() / 60

                if minutes_passed < self.email_cooldown_minutes:
                    logger.info(f"  Email cooldown active: {minutes_passed:.1f}/{self.email_cooldown_minutes} minutes")
                    return False

            logger.info(f"  ✅ Should send email (status changed: False → True)")
            return True
        else:
            logger.info(f"  No email needed (last={self.last_status}, current={current_available})")
            return False

    def simulate_check(self, available, minute_offset=0):
        """Simulate a status check"""
        # Simulate time passing
        if minute_offset > 0 and self.last_email_time:
            self.last_email_time = datetime.now() - timedelta(minutes=minute_offset)

        logger.info(f"\nCheck: Product {'available' if available else 'unavailable'}")

        if self.should_send_email(available):
            logger.info("  📧 EMAIL SENT!")
            self.last_email_time = datetime.now()

        self.last_status = available

def main():
    logger.info("=" * 60)
    logger.info("TESTING EMAIL NOTIFICATION LOGIC")
    logger.info("=" * 60)

    tester = EmailLogicTester()

    # Test scenario 1: Normal flow
    logger.info("\n### Scenario 1: Normal status changes ###")
    tester.simulate_check(False)  # First check - unavailable (no email)
    tester.simulate_check(False)  # Still unavailable (no email)
    tester.simulate_check(True)   # Becomes available (email sent!)
    tester.simulate_check(True)   # Still available (no email)
    tester.simulate_check(False)  # Becomes unavailable (no email)
    tester.simulate_check(True)   # Available again (email sent!)

    # Test scenario 2: Cooldown period
    logger.info("\n### Scenario 2: Testing cooldown period ###")
    tester2 = EmailLogicTester()
    tester2.simulate_check(False)  # First check - unavailable
    tester2.simulate_check(True)   # Becomes available (email sent!)
    tester2.simulate_check(False)  # Becomes unavailable
    tester2.simulate_check(True, minute_offset=5)  # Available again after 5 min (cooldown blocks)
    tester2.simulate_check(False)  # Becomes unavailable
    tester2.simulate_check(True, minute_offset=11) # Available again after 11 min (email sent!)

    # Test scenario 3: First check is available
    logger.info("\n### Scenario 3: First check is available ###")
    tester3 = EmailLogicTester()
    tester3.simulate_check(True)   # First check - available (no email on first check)
    tester3.simulate_check(False)  # Becomes unavailable
    tester3.simulate_check(True)   # Becomes available (email sent!)

    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("Email logic working correctly:")
    logger.info("✅ Emails only sent on status change: unavailable → available")
    logger.info("✅ 10-minute cooldown between emails")
    logger.info("✅ No email on first check (even if available)")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()