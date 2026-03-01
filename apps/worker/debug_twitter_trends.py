"""
Debug script for Twitter Trends with Playwright
"""

import asyncio
import logging
import sys
import os

# Setup path
sys.path.insert(0, os.path.abspath('.'))

from intel.cookie_manager import get_cookie_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def debug_twitter_trends():
    """Debug Twitter Trends with Playwright"""
    
    logger.info("=" * 60)
    logger.info("TWITTER TRENDS DEBUG (Playwright)")
    logger.info("=" * 60)
    
    try:
        from playwright.async_api import async_playwright
        
        cookie_manager = get_cookie_manager()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # headless=False for debugging
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Load cookies
            playwright_cookies = cookie_manager.cookie_loader.get_playwright_cookies('twitter')
            if playwright_cookies:
                await context.add_cookies(playwright_cookies)
                logger.info(f"✅ Loaded {len(playwright_cookies)} cookies")
            
            page = await context.new_page()
            
            try:
                logger.info("📡 Loading Twitter trends page...")
                await page.goto('https://x.com/explore/tabs/trending', wait_until='networkidle', timeout=60000)
                await page.wait_for_timeout(5000)
                
                # Take screenshot
                await page.screenshot(path='twitter_trends_screenshot.png')
                logger.info("📸 Screenshot saved: twitter_trends_screenshot.png")
                
                # Get page text
                page_text = await page.evaluate('() => document.body.innerText')
                logger.info(f"\n📄 Page text (first 1000 chars):\n{page_text[:1000]}")
                
                # Try to find trends
                logger.info("\n🔍 Looking for trends...")
                
                # Method 1: data-testid attribute
                trends1 = await page.evaluate('''() => {
                    const elements = document.querySelectorAll('[data-testid="trend"]');
                    return Array.from(elements).map(el => el.innerText).slice(0, 5);
                }''')
                logger.info(f"Method 1 (data-testid): {len(trends1)} found")
                if trends1:
                    for trend in trends1:
                        logger.info(f"  - {trend}")
                
                # Method 2: Look for trending keywords
                trends2 = await page.evaluate('''() => {
                    const text = document.body.innerText;
                    const lines = text.split('\\n');
                    const trends = [];
                    
                    for (let i = 0; i < lines.length; i++) {
                        const line = lines[i].trim();
                        // Look for lines with hashtags or capitalized words
                        if ((line.startsWith('#') || /^[A-Z]/.test(line)) && 
                            line.length > 2 && line.length < 80 &&
                            !line.includes('Trending') &&
                            !line.includes('For you') &&
                            !line.includes('Following')) {
                            trends.push(line);
                        }
                    }
                    
                    return [...new Set(trends)].slice(0, 10);
                }''')
                logger.info(f"\nMethod 2 (text patterns): {len(trends2)} found")
                if trends2:
                    for trend in trends2:
                        logger.info(f"  - {trend}")
                
                # Method 3: Look for any article or div with text
                trends3 = await page.evaluate('''() => {
                    const articles = document.querySelectorAll('article, div[role="link"]');
                    const trends = [];
                    
                    for (const el of articles) {
                        const text = el.innerText.split('\\n')[0].trim();
                        if (text && text.length > 2 && text.length < 80) {
                            trends.push(text);
                        }
                    }
                    
                    return [...new Set(trends)].slice(0, 10);
                }''')
                logger.info(f"\nMethod 3 (articles): {len(trends3)} found")
                if trends3:
                    for trend in trends3:
                        logger.info(f"  - {trend}")
                
                # Wait for user inspection
                logger.info("\n⏸️  Browser window open for inspection. Press Ctrl+C to close...")
                await page.wait_for_timeout(60000)
            
            except KeyboardInterrupt:
                logger.info("\n🛑 User interrupted")
            except Exception as e:
                logger.error(f"❌ Error: {e}", exc_info=True)
            finally:
                await context.close()
                await browser.close()
    
    except Exception as e:
        logger.error(f"❌ Debug failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(debug_twitter_trends())
