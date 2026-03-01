"""
Medium Article Aggregator

Scrapes trending tech/AI/startup articles.
Uses cookies to bypass paywall if available.
Falls back to Playwright for Cloudflare bypass.
"""

import aiohttp
from bs4 import BeautifulSoup
import logging
from typing import List, Optional
from datetime import datetime, timezone
import re

from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory
)
from .cookie_manager import get_cookie_manager
from .undetected_chrome_helper import get_undetected_chrome

logger = logging.getLogger(__name__)


class MediumScraper(BaseContentSource):
    """
    Medium article aggregator.
    
    Scrapes trending tech/AI/startup articles.
    Uses cookies to bypass paywall if available.
    """
    
    TOPICS = {
        'artificial-intelligence': ContentCategory.AI_ML,
        'machine-learning': ContentCategory.AI_ML,
        'programming': ContentCategory.TECH_PROGRAMMING,
        'software-development': ContentCategory.TECH_PROGRAMMING,
        'startup': ContentCategory.STARTUP_BUSINESS,
        'entrepreneurship': ContentCategory.STARTUP_BUSINESS,
        'cryptocurrency': ContentCategory.CRYPTO_WEB3,
    }
    
    def __init__(
        self,
        topics: Optional[dict] = None,
        articles_per_topic: int = 5,
        use_undetected_chrome: bool = True
    ):
        """
        Initialize Medium scraper.
        
        Args:
            topics: Custom topic -> category mapping
            articles_per_topic: Articles to fetch per topic
            use_undetected_chrome: Use undetected Chrome on 403
        """
        super().__init__()
        
        self.cookie_manager = get_cookie_manager()
        self.chrome_helper = None  # Lazy initialization
        self.topics = topics or self.TOPICS
        self.articles_per_topic = articles_per_topic
        self.use_undetected_chrome = use_undetected_chrome
        
        has_cookie = self.cookie_manager.validate_cookie('medium')
        
        logger.info(
            f"✅ MediumScraper initialized "
            f"({len(self.topics)} topics, "
            f"{'with' if has_cookie else 'without'} cookie)"
        )
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "Medium"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch trending articles from Medium"""
        
        items = []
        
        for topic, category in self.topics.items():
            try:
                articles = await self._fetch_topic_articles(topic, category)
                items.extend(articles)
                logger.debug(f"Fetched {len(articles)} articles from {topic}")
            
            except Exception as e:
                logger.error(f"❌ Error fetching {topic}: {e}")
                continue
        
        logger.info(f"✅ Medium: Fetched {len(items)} articles from {len(self.topics)} topics")
        return items
    
    async def _fetch_topic_articles(
        self,
        topic: str,
        category: ContentCategory
    ) -> List[ContentItem]:
        """Fetch articles for a topic"""
        
        url = f"https://medium.com/tag/{topic}"
        # Try JSON cookies first, fall back to .env
        headers = self.cookie_manager.get_headers_for_site('medium')
        
        items = []
        html = None
        
        # Try regular request first
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                
                if response.status == 403:
                    if self.use_undetected_chrome:
                        logger.info(f"📡 403 for {topic} - trying undetected Chrome...")
                        html = await self._fetch_with_undetected_chrome(url)
                        if not html:
                            logger.warning(f"⚠️  Undetected Chrome failed for {topic}")
                            return items
                    else:
                        logger.warning(f"⚠️  403 for {topic} - undetected Chrome disabled")
                        return items
                
                elif response.status == 200:
                    html = await response.text()
                
                else:
                    logger.warning(f"HTTP {response.status} for {topic}")
                    return items
        
        # Parse HTML (from either aiohttp or Playwright)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find article links (Medium uses h2/h3 for titles)
            article_links = soup.find_all('a', href=re.compile(r'medium\.com/.*'))
            
            seen_urls = set()
            
            for link in article_links[:self.articles_per_topic * 3]:  # Get more, filter duplicates
                try:
                    article_url = link['href']
                    
                    # Skip if already seen
                    if article_url in seen_urls:
                        continue
                    seen_urls.add(article_url)
                    
                    # Get title (usually in h2 or h3)
                    title_elem = link.find(['h2', 'h3'])
                    if not title_elem:
                        # Try parent elements
                        parent = link.parent
                        if parent:
                            title_elem = parent.find(['h2', 'h3'])
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    if not title or len(title) < 10:
                        continue
                    
                    # Ensure full URL
                    if not article_url.startswith('http'):
                        article_url = 'https://medium.com' + article_url
                    
                    # Create item
                    item = ContentItem(
                        title=title,
                        url=article_url,
                        source_type='medium',
                        source_name=f"Medium - {topic}",
                        published_at=datetime.now(timezone.utc),
                        category=category,
                        description=None
                    )
                    
                    item.relevance_score = 0.65
                    item.engagement_score = 0.6
                    
                    items.append(item)
                    
                    if len(items) >= self.articles_per_topic:
                        break
                
                except Exception as e:
                    logger.debug(f"Error parsing article: {e}")
                    continue
        
        return items
    
    async def _fetch_with_undetected_chrome(self, url: str) -> Optional[str]:
        """
        Fetch page using undetected Chrome (bypasses Cloudflare).
        Runs in executor since undetected Chrome is synchronous.
        
        Args:
            url: URL to fetch
        
        Returns:
            HTML content or None
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def _fetch_sync():
            """Synchronous fetch for thread executor"""
            try:
                import time as time_module
                start = time_module.time()
                
                # Lazy initialize Chrome helper
                if not self.chrome_helper:
                    logger.info("Initializing Chrome helper...")
                    self.chrome_helper = get_undetected_chrome()
                    self.chrome_helper.start(headless=True)
                    logger.info(f"Chrome started in {time_module.time() - start:.1f}s")
                
                # Get cookies
                playwright_cookies = self.cookie_manager.cookie_loader.get_playwright_cookies('medium')
                logger.info(f"Loaded {len(playwright_cookies)} Medium cookies")
                
                # Fetch with cookies
                fetch_start = time_module.time()
                html = self.chrome_helper.fetch_with_cookies(
                    url=url,
                    cookies=playwright_cookies,
                    wait_time=5
                )
                logger.info(f"Fetch completed in {time_module.time() - fetch_start:.1f}s")
                
                return html
                
            except Exception as e:
                logger.error(f"❌ Undetected Chrome error: {e}")
                return None
        
        # Run in thread executor with timeout
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            try:
                html = await asyncio.wait_for(
                    loop.run_in_executor(executor, _fetch_sync),
                    timeout=60  # 60 seconds max
                )
            except asyncio.TimeoutError:
                logger.error("❌ Undetected Chrome fetch timed out after 60s")
                return None
        
        return html


# Global instance
medium_scraper = MediumScraper()
