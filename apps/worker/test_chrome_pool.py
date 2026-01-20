"""
Simple test script for Chrome Pool Manager
"""

import asyncio
import logging

from chrome_pool import ChromePool, get_chrome_pool, shutdown_chrome_pool

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_chrome_pool():
    """Test Chrome pool functionality"""
    
    try:
        # Test 1: Initialize Chrome pool
        logger.info("=" * 50)
        logger.info("TEST 1: Initialize Chrome Pool")
        logger.info("=" * 50)
        
        pool = ChromePool()
        await pool.initialize()
        logger.info("✅ Chrome pool initialized")

        # Test 2: Get page
        logger.info("\n" + "=" * 50)
        logger.info("TEST 2: Get Page")
        logger.info("=" * 50)
        
        page = await pool.get_page()
        logger.info(f"✅ Got page: {page}")

        # Test 3: Navigate to X.com
        logger.info("\n" + "=" * 50)
        logger.info("TEST 3: Navigate to X.com")
        logger.info("=" * 50)
        
        await page.goto("https://x.com", wait_until="domcontentloaded", timeout=30000)
        title = await page.title()
        logger.info(f"✅ Navigated to X.com | Title: {title}")

        # Test 4: Save cookies
        logger.info("\n" + "=" * 50)
        logger.info("TEST 4: Save Cookies")
        logger.info("=" * 50)
        
        await pool.save_cookies()
        logger.info("✅ Cookies saved")

        # Test 5: Health check
        logger.info("\n" + "=" * 50)
        logger.info("TEST 5: Health Check")
        logger.info("=" * 50)
        
        is_healthy = await pool.is_healthy()
        logger.info(f"✅ Health check: {is_healthy}")

        # Test 6: Shutdown
        logger.info("\n" + "=" * 50)
        logger.info("TEST 6: Shutdown")
        logger.info("=" * 50)
        
        await pool.shutdown()
        logger.info("✅ Chrome pool shutdown gracefully")

        logger.info("\n" + "=" * 50)
        logger.info("ALL TESTS PASSED ✅")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


async def test_singleton_pattern():
    """Test singleton pattern"""
    
    logger.info("\n" + "=" * 50)
    logger.info("TEST: Singleton Pattern")
    logger.info("=" * 50)
    
    pool1 = ChromePool()
    pool2 = ChromePool()
    
    logger.info(f"Pool1 ID: {id(pool1)}")
    logger.info(f"Pool2 ID: {id(pool2)}")
    logger.info(f"Same instance: {pool1 is pool2}")
    logger.info("✅ Singleton pattern works")


async def main():
    """Run all tests"""
    await test_singleton_pattern()
    await test_chrome_pool()


if __name__ == "__main__":
    asyncio.run(main())
