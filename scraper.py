import time
import random
import logging
from typing import Optional, Dict, Any
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from fake_useragent import UserAgent
import cloudscraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AppleStockChecker:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.ua = UserAgent()
        self.scraper = cloudscraper.create_scraper()

    def _setup_chrome_driver(self):
        """Setup undetected Chrome driver with anti-detection measures"""
        try:
            options = uc.ChromeOptions()

            options.add_argument(f'user-agent={self.ua.random}')

            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')

            try:
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
            except:
                pass

            if self.headless:
                options.add_argument('--headless=new')

            options.add_argument('--window-size=1920,1080')

            prefs = {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False
            }
            options.add_experimental_option("prefs", prefs)

            self.driver = uc.Chrome(options=options, version_main=None)

            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    window.chrome = {
                        runtime: {}
                    };
                    Object.defineProperty(navigator, 'permissions', {
                        get: () => ({
                            query: () => Promise.resolve({ state: 'granted' })
                        })
                    });
                """
            })

            logger.info("Chrome driver setup successful")
            return True

        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            return False

    def _add_random_delay(self, min_delay: float = 0.5, max_delay: float = 2.0):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def check_stock_selenium(self, url: str) -> Dict[str, Any]:
        """Check stock using Selenium with anti-detection"""
        result = {
            'in_stock': False,
            'method': 'selenium',
            'error': None,
            'details': {}
        }

        try:
            if not self.driver:
                if not self._setup_chrome_driver():
                    result['error'] = "Failed to setup driver"
                    return result

            logger.info(f"Loading page: {url}")
            self.driver.get(url)

            self._add_random_delay(3, 5)

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);")
            self._add_random_delay(1, 2)

            wait = WebDriverWait(self.driver, 15)

            stock_indicators = [
                (By.XPATH, "//button[contains(text(), 'カートに追加')]"),
                (By.XPATH, "//button[contains(text(), 'Add to Bag')]"),
                (By.XPATH, "//button[contains(@class, 'add-to-cart')]"),
                (By.XPATH, "//button[contains(@data-autom, 'add-to-cart')]"),
                (By.XPATH, "//span[contains(text(), '在庫あり')]"),
                (By.XPATH, "//span[contains(text(), 'In Stock')]"),
                (By.XPATH, "//div[@data-autom='fulfillment-check-availability']"),
            ]

            out_of_stock_indicators = [
                (By.XPATH, "//*[contains(text(), '在庫切れ')]"),
                (By.XPATH, "//*[contains(text(), 'Out of Stock')]"),
                (By.XPATH, "//*[contains(text(), '現在ご利用いただけません')]"),
                (By.XPATH, "//*[contains(text(), 'Currently Unavailable')]"),
                (By.XPATH, "//*[contains(text(), '入荷待ち')]"),
            ]

            for selector_type, selector in out_of_stock_indicators:
                try:
                    element = self.driver.find_element(selector_type, selector)
                    if element and element.is_displayed():
                        logger.info(f"Out of stock indicator found: {element.text}")
                        result['details']['indicator'] = element.text
                        return result
                except:
                    continue

            for selector_type, selector in stock_indicators:
                try:
                    element = wait.until(EC.presence_of_element_located((selector_type, selector)))
                    if element:
                        is_enabled = element.is_enabled() if element.tag_name == 'button' else True
                        is_displayed = element.is_displayed()

                        if is_displayed and is_enabled:
                            logger.info(f"Stock indicator found: {selector}")
                            result['in_stock'] = True
                            result['details']['indicator'] = selector
                            result['details']['element_text'] = element.text[:100] if element.text else "N/A"
                            return result
                except TimeoutException:
                    continue
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")
                    continue

            page_source_lower = self.driver.page_source.lower()
            if 'add to bag' in page_source_lower or 'カートに追加' in page_source_lower:
                if '在庫切れ' not in page_source_lower and 'out of stock' not in page_source_lower:
                    result['in_stock'] = True
                    result['details']['indicator'] = "Add to cart text found in page"

            logger.info("No definitive stock indicators found")

        except WebDriverException as e:
            logger.error(f"WebDriver error: {e}")
            result['error'] = str(e)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            result['error'] = str(e)

        return result

    def check_stock_cloudscraper(self, url: str) -> Dict[str, Any]:
        """Fallback method using cloudscraper for simpler checks"""
        result = {
            'in_stock': False,
            'method': 'cloudscraper',
            'error': None,
            'details': {}
        }

        try:
            response = self.scraper.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text.lower()

                if ('add to bag' in content or 'カートに追加' in content) and \
                   ('out of stock' not in content and '在庫切れ' not in content):
                    result['in_stock'] = True
                    result['details']['indicator'] = "Add to cart found via cloudscraper"

            else:
                result['error'] = f"HTTP {response.status_code}"

        except Exception as e:
            logger.error(f"Cloudscraper error: {e}")
            result['error'] = str(e)

        return result

    def check_stock(self, url: str) -> Dict[str, Any]:
        """Main method to check stock availability"""
        result = self.check_stock_selenium(url)

        if result['error'] and 'cloudflare' in str(result['error']).lower():
            logger.info("Cloudflare detected, trying cloudscraper")
            result = self.check_stock_cloudscraper(url)

        return result

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Driver closed successfully")
            except Exception as e:
                logger.error(f"Error closing driver: {e}")