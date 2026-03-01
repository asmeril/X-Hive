"""
Playwright Helper for Browser Automation

Bypasses Cloudflare and other anti-bot systems using real browser.
"""

import asyncio
from playwright.async_api import async_playwright, Browser, Page
import logging
from typing import Optional, Dict
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class PlaywrightHelper:
    """Helper for browser automation with Playwright"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
    
    async def start(self):
        """Start Playwright browser"""
        if self.browser:
            return
        
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            logger.info("✅ Playwright browser started")
        except Exception as e:
            logger.error(f"❌ Error starting Playwright: {e}")
    
    async def stop(self):
        """Stop Playwright browser"""
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
    
    async def fetch_with_cookies(
        self,
        url: str,
        cookies_file: str,
        timeout: int = 60000  # Increased to 60 seconds
    ) -> Optional[str]:
        """
        Fetch page HTML with cookies loaded.
        
        Args:
            url: Page URL
            cookies_file: Path to cookies JSON file
            timeout: Navigation timeout in milliseconds
        
        Returns:
            Page HTML or None
        """
        await self.start()
        
        if not self.browser:
            return None
        
        context = None
        page = None
        
        try:
            context = await self.browser.new_context()
            
            # Load cookies from JSON
            cookies_path = Path(__file__).parent.parent / 'cookies' / cookies_file
            if cookies_path.exists():
                with open(cookies_path, 'r') as f:
                    cookies = json.load(f)
                
                # Convert EditThisCookie format to Playwright format
                playwright_cookies = []
                for cookie in cookies:
                    playwright_cookie = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie.get('domain', ''),
                        'path': cookie.get('path', '/'),
                        'secure': cookie.get('secure', False),
                        'httpOnly': cookie.get('httpOnly', False),
                    }
                    
                    if 'expirationDate' in cookie:
                        playwright_cookie['expires'] = cookie['expirationDate']
                    
                    playwright_cookies.append(playwright_cookie)
                
                await context.add_cookies(playwright_cookies)
                logger.debug(f"✅ Loaded {len(playwright_cookies)} cookies")
            
            # Create page and navigate
            page = await context.new_page()
            
            # Navigate with timeout (using domcontentloaded instead of networkidle for faster response)
            await page.goto(url, wait_until='domcontentloaded', timeout=timeout)
            
            # Wait a bit for dynamic content
            await page.wait_for_timeout(2000)
            
            # Get HTML
            html = await page.content()
            
            return html
        
        except Exception as e:
            logger.error(f"❌ Playwright fetch error: {e}")
            return None
        
        finally:
            # Clean up
            if page:
                try:
                    await page.close()
                except:
                    pass
            if context:
                try:
                    await context.close()
                except:
                    pass
    
    async def fetch_simple(
        self,
        url: str,
        wait_time: int = 3,
        timeout: int = 60000
    ) -> Optional[str]:
        """
        Simple fetch without cookies (for public pages).
        
        Args:
            url: Page URL
            wait_time: Wait time in seconds after page load
            timeout: Navigation timeout in milliseconds
        
        Returns:
            Page HTML or None
        """
        await self.start()
        
        if not self.browser:
            return None
        
        context = None
        page = None
        
        try:
            context = await self.browser.new_context()
            page = await context.new_page()
            
            # Navigate
            await page.goto(url, timeout=timeout, wait_until='domcontentloaded')
            
            # Wait for dynamic content
            await page.wait_for_timeout(wait_time * 1000)
            
            # Get HTML
            html = await page.content()
            
            logger.debug(f"Fetched {len(html)} bytes from {url}")
            return html
        
        except Exception as e:
            logger.error(f"❌ Playwright simple fetch error: {e}")
            return None
        
        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass
            if context:
                try:
                    await context.close()
                except:
                    pass


# Global instance
_playwright_helper = None


async def get_playwright_helper() -> PlaywrightHelper:
    """Get global Playwright helper instance"""
    global _playwright_helper
    
    if _playwright_helper is None:
        _playwright_helper = PlaywrightHelper()
        await _playwright_helper.start()
    
    return _playwright_helper
