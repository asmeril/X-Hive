"""
Chrome Pool Manager for X-HIVE
Persistent Playwright browser management with cookie persistence and session warmth.
"""

import sys
import asyncio

# Windows fix for Playwright subprocess on Python 3.12+ (must be before async_playwright import)
# Python 3.12+ changed asyncio subprocess handling, requiring WindowsSelectorEventLoopPolicy
if sys.platform == "win32" and sys.version_info >= (3, 12):
    # Use WindowsSelectorEventLoopPolicy for subprocess support
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from config import settings
from human_behavior import HumanBehavior

logger = logging.getLogger(__name__)


class ChromePoolError(Exception):
    """Chrome pool operation error"""
    pass


class ChromePool:
    """
    Singleton Chrome Pool Manager for persistent WebDriver management.
    
    Features:
    - Persistent Playwright Chromium browser instance
    - Cookie persistence (load from/save to disk)
    - Session warmth (keep logged in to X.com)
    - Health monitoring & auto-restart
    - Graceful shutdown
    """

    _instance: Optional["ChromePool"] = None
    _lock = asyncio.Lock()

    def __new__(cls) -> "ChromePool":
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Chrome pool"""
        if hasattr(self, "_initialized"):
            return

        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._playwright = None
        self._initialized = True
        self._retry_count = 0
        self._max_retries = 3

        # Configuration from settings
        self.cookie_path = Path(settings.COOKIE_PATH)
        self.user_data_dir = Path(settings.BROWSER_DATA_DIR)
        self.headless = settings.CHROME_HEADLESS
        
        # STEALTH MODE: Anti-detection arguments
        self.launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-site-isolation-trials",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-infobars",
            "--window-size=1920,1080",
        ]

        logger.info("ChromePool initialized")

    async def initialize(self) -> None:
        """
        Start Chrome with persistent context.
        
        Raises:
            ChromePoolError: If browser fails to start after max retries
        """
        async with self._lock:
            if self.browser is not None:
                logger.info("Browser already running")
                return

            for attempt in range(1, self._max_retries + 1):
                try:
                    logger.info(f"Initializing Chrome (attempt {attempt}/{self._max_retries})")

                    # Start Playwright
                    self._playwright = await async_playwright().start()

                    # Create persistent user data directory
                    self.user_data_dir.mkdir(parents=True, exist_ok=True)

                    # Launch browser
                    self.browser = await self._playwright.chromium.launch(
                        headless=self.headless,
                        args=self.launch_args,
                    )

                    # STEALTH MODE: Random User-Agent and viewport
                    user_agent = HumanBehavior.get_random_user_agent()
                    viewport = HumanBehavior.get_random_viewport()

                    # Create persistent context with anti-detection
                    self.context = await self.browser.new_context(
                        user_agent=user_agent,
                        viewport=viewport,
                        locale="en-US",
                        timezone_id="America/New_York",
                        # Permissions
                        permissions=["geolocation"],
                        # Anti-fingerprinting
                        extra_http_headers={
                            "Accept-Language": "en-US,en;q=0.9",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        }
                    )
                    
                    # STEALTH MODE: Inject anti-detection scripts
                    await self.context.add_init_script("""
                        // Remove webdriver property
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        
                        // Override permissions
                        const originalQuery = window.navigator.permissions.query;
                        window.navigator.permissions.query = (parameters) => (
                            parameters.name === 'notifications' ?
                                Promise.resolve({ state: Notification.permission }) :
                                originalQuery(parameters)
                        );
                        
                        // Override plugins
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5]
                        });
                        
                        // Override languages
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en']
                        });
                        
                        // Chrome runtime
                        window.chrome = {
                            runtime: {}
                        };
                        
                        // Mock screen properties with randomization
                        Object.defineProperty(screen, 'availTop', { get: () => 0 });
                        Object.defineProperty(screen, 'availLeft', { get: () => 0 });
                    """)

                    # Load saved cookies
                    await self.load_cookies()

                    # Create page
                    self.page = await self.context.new_page()
                    
                    logger.info(f"✅ Chrome pool initialized (stealth mode, UA: {user_agent[:50]}..., viewport: {viewport})")
                    self._retry_count = 0
                    return

                except Exception as e:
                    logger.error(f"Chrome initialization failed (attempt {attempt}): {e}")
                    await self._cleanup_on_error()

                    if attempt < self._max_retries:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise ChromePoolError(
                            f"Failed to initialize Chrome after {self._max_retries} attempts: {e}"
                        )

    async def get_page(self) -> Page:
        """
        Get or create page instance.
        
        Returns:
            Page: Playwright page instance
            
        Raises:
            ChromePoolError: If page is not available
        """
        if self.page is None or self.page.is_closed():
            raise ChromePoolError("Page not available or closed")
        return self.page

    async def save_cookies(self, cookies: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Save cookies to JSON file.
        
        Args:
            cookies: List of cookies. If None, saves current context cookies.
        """
        try:
            if cookies is None and self.context:
                cookies = await self.context.cookies()

            if not cookies:
                logger.debug("No cookies to save")
                return

            self.cookie_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.cookie_path, "w") as f:
                json.dump(
                    {
                        "saved_at": datetime.now().isoformat(),
                        "cookies": cookies,
                    },
                    f,
                    indent=2,
                )

            logger.info(f"✅ Saved {len(cookies)} cookies to {self.cookie_path}")

        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")

    async def load_cookies(self) -> None:
        r"""
        Load cookies from JSON file and add to context.
        
        Cookie path: C:\XHive\data\x_cookies.json
        """
        try:
            if not self.cookie_path.exists():
                logger.debug(f"No saved cookies found at {self.cookie_path}")
                return

            with open(self.cookie_path, "r") as f:
                data = json.load(f)

            cookies = data.get("cookies", [])

            if not cookies or not self.context:
                logger.debug("No cookies to load or context not available")
                return

            await self.context.add_cookies(cookies)
            logger.info(f"✅ Loaded {len(cookies)} cookies from {self.cookie_path}")

        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")

    async def is_healthy(self) -> bool:
        """
        Check if Chrome is still responsive.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            if self.page is None or self.page.is_closed():
                logger.warning("Page is closed")
                return False

            # Simple health check: get page title
            title = await asyncio.wait_for(self.page.title(), timeout=5.0)
            logger.debug(f"Health check passed (title: {title[:50]})")
            return True

        except asyncio.TimeoutError:
            logger.error("Health check timeout")
            return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def restart(self) -> None:
        """
        Restart Chrome if crashed or unhealthy.
        
        Gracefully shuts down and reinitializes.
        """
        logger.info("🔄 Restarting Chrome pool...")
        try:
            await self.shutdown()
            await asyncio.sleep(1)
            await self.initialize()
            logger.info("✅ Chrome pool restarted successfully")
        except Exception as e:
            logger.error(f"Failed to restart Chrome: {e}")
            raise ChromePoolError(f"Restart failed: {e}")

    async def shutdown(self) -> None:
        """
        Graceful shutdown of Chrome and cleanup.
        
        Saves cookies before closing.
        """
        try:
            logger.info("Shutting down Chrome pool...")

            # Save cookies before shutdown
            if self.context:
                await self.save_cookies()

            # Close page
            if self.page and not self.page.is_closed():
                await self.page.close()
                self.page = None

            # Close context
            if self.context:
                await self.context.close()
                self.context = None

            # Close browser
            if self.browser:
                await self.browser.close()
                self.browser = None

            # Stop playwright
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

            logger.info("✅ Chrome pool shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    async def _cleanup_on_error(self) -> None:
        """Internal cleanup on error"""
        try:
            if self.page and not self.page.is_closed():
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            logger.debug(f"Cleanup error: {e}")

        self.page = None
        self.context = None
        self.browser = None
        self._playwright = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.shutdown()


# Convenience functions for module-level access
async def get_chrome_pool() -> ChromePool:
    """Get or create singleton Chrome pool"""
    pool = ChromePool()
    if pool.browser is None:
        await pool.initialize()
    return pool


async def shutdown_chrome_pool() -> None:
    """Shutdown the Chrome pool"""
    pool = ChromePool()
    await pool.shutdown()
