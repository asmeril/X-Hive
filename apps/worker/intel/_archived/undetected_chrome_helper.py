"""
Undetected ChromeDriver Helper

Bypasses Cloudflare and bot detection using undetected-chromedriver.
More reliable than Playwright for heavy anti-bot sites (Medium, Twitter, etc.)
"""

import logging
import time
from typing import Optional, List, Dict
from pathlib import Path

try:
    import undetected_chromedriver as uc
    HAS_UC = True
except ImportError:
    HAS_UC = False
    uc = None

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)


class UndetectedChromeHelper:
    """
    Helper for undetected Chrome automation.
    
    More effective than Playwright for sites with strong anti-bot protection.
    Used by XiDeAI successfully for Twitter, Medium scraping.
    """
    
    def __init__(self):
        self.driver = None
        
        if not HAS_UC:
            logger.warning("⚠️  undetected-chromedriver not installed. Run: pip install undetected-chromedriver")
    
    def start(self, headless: bool = True, version_main: Optional[int] = None):
        """
        Start undetected Chrome browser.
        
        Args:
            headless: Run in headless mode
            version_main: Chrome version (None = auto-detect)
        """
        if not HAS_UC:
            raise RuntimeError("undetected-chromedriver not installed")
        
        if self.driver:
            return
        
        try:
            options = uc.ChromeOptions()
            
            if headless:
                options.add_argument("--headless=new")
            
            # Anti-detection
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
            
            # Performance
            options.page_load_strategy = 'eager'
            
            # Try to create driver (matching XiDeAI pattern exactly)
            try:
                self.driver = uc.Chrome(
                    options=options,
                    version_main=version_main,
                    headless=headless
                )
            except Exception as e:
                if "version" in str(e).lower():
                    logger.warning(f"⚠️  Version mismatch, forcing v145... {e}")
                    # CRITICAL: Recreate options (cannot reuse after failure)
                    options = uc.ChromeOptions()
                    if headless:
                        options.add_argument("--headless=new")
                    options.add_argument("--disable-blink-features=AutomationControlled")
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--window-size=1920,1080")
                    options.page_load_strategy = 'eager'
                    
                    self.driver = uc.Chrome(
                        options=options,
                        version_main=145,
                        headless=headless
                    )
                else:
                    raise e
            
            # Set timeouts
            try:
                self.driver.set_page_load_timeout(30)
            except:
                pass
            
            logger.info("✅ Undetected Chrome started successfully")
            
        except Exception as e:
            logger.error(f"❌ Error starting undetected Chrome: {e}")
            raise
    
    def stop(self):
        """Stop Chrome browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            logger.info("✅ Undetected Chrome stopped")
    
    def fetch_with_cookies(
        self,
        url: str,
        cookies: List[Dict],
        wait_time: int = 3
    ) -> Optional[str]:
        """
        Fetch page HTML with cookies.
        
        Args:
            url: Page URL
            cookies: List of cookie dicts (Playwright format)
            wait_time: Wait time in seconds after page load
        
        Returns:
            Page HTML or None
        """
        if not self.driver:
            self.start()
        
        try:
            # Go to domain first (needed for cookie setting)
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain_url = f"{parsed.scheme}://{parsed.netloc}"
            
            self.driver.get(domain_url)
            time.sleep(1)
            
            # Add cookies
            for cookie in cookies:
                try:
                    # Convert to Selenium format
                    selenium_cookie = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie.get('domain', ''),
                        'path': cookie.get('path', '/'),
                        'secure': cookie.get('secure', False),
                        'httpOnly': cookie.get('httpOnly', False),
                    }
                    
                    if 'expires' in cookie and cookie['expires'] != -1:
                        selenium_cookie['expiry'] = int(cookie['expires'])
                    
                    self.driver.add_cookie(selenium_cookie)
                except Exception as e:
                    logger.debug(f"Cookie add failed: {e}")
                    continue
            
            # Navigate to actual URL
            self.driver.get(url)
            time.sleep(wait_time)
            
            # Get page source
            html = self.driver.page_source
            
            return html
            
        except Exception as e:
            logger.error(f"❌ Error fetching with cookies: {e}")
            return None
    
    def fetch_simple(self, url: str, wait_time: int = 3) -> Optional[str]:
        """
        Simple fetch without cookies.
        
        Args:
            url: Page URL
            wait_time: Wait time in seconds
        
        Returns:
            Page HTML or None
        """
        if not self.driver:
            self.start()
        
        try:
            self.driver.get(url)
            time.sleep(wait_time)
            return self.driver.page_source
        except Exception as e:
            logger.error(f"❌ Error fetching: {e}")
            return None
    
    def wait_for_element(
        self,
        selector: str,
        by: str = By.CSS_SELECTOR,
        timeout: int = 10
    ):
        """
        Wait for element to appear.
        
        Args:
            selector: Element selector
            by: Selector type (CSS_SELECTOR, XPATH, etc.)
            timeout: Wait timeout in seconds
        
        Returns:
            WebElement or None
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except Exception as e:
            logger.debug(f"Element not found: {selector} - {e}")
            return None
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


# Singleton instance
_helper_instance = None


def get_undetected_chrome() -> UndetectedChromeHelper:
    """Get global undetected Chrome helper instance"""
    global _helper_instance
    
    if _helper_instance is None:
        _helper_instance = UndetectedChromeHelper()
    
    return _helper_instance
