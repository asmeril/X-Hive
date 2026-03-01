"""
Substack Newsletter Aggregator

Scrapes popular tech/AI/startup newsletters via RSS feeds.
"""

import asyncio
import aiohttp
import feedparser
import logging
from typing import List, Optional
from datetime import datetime, timezone

from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory
)

logger = logging.getLogger(__name__)


class SubstackScraper(BaseContentSource):
    """
    Substack newsletter aggregator.
    
    Scrapes popular tech/AI/startup newsletters via RSS feeds.
    """
    
    # Popular tech/AI Substack newsletters
    NEWSLETTERS = {
        # AI/ML
        'www.importai.com': ContentCategory.AI_ML,
        'ai.plainenglish.io': ContentCategory.AI_ML,  # Replaced thealgorithmicbridge (403)
        
        # Tech/Programming
        'newsletter.pragmaticengineer.com': ContentCategory.TECH_PROGRAMMING,
        'blog.bytebytego.com': ContentCategory.TECH_PROGRAMMING,
        
        # Startup/Business
        'www.lennysnewsletter.com': ContentCategory.STARTUP_BUSINESS,
        'www.every.to': ContentCategory.STARTUP_BUSINESS,  # Fixed: added www subdomain (was 404)
    }
    
    def __init__(
        self,
        newsletters: Optional[dict] = None,
        posts_per_newsletter: int = 3
    ):
        """
        Initialize Substack scraper.
        
        Args:
            newsletters: Custom newsletter -> category mapping
            posts_per_newsletter: Posts to fetch per newsletter
        """
        super().__init__()
        
        self.newsletters = newsletters or self.NEWSLETTERS
        self.posts_per_newsletter = posts_per_newsletter
        
        logger.info(f"✅ SubstackScraper initialized ({len(self.newsletters)} newsletters)")
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "Substack"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch latest posts from Substack newsletters (parallel)"""
        
        # Fetch all newsletters in parallel for faster execution
        async def fetch_newsletter(domain: str, category: ContentCategory) -> List[ContentItem]:
            """Fetch a single newsletter's posts"""
            newsletter_items = []
            try:
                feed_url = f"https://{domain}/feed"
                feed = await self._fetch_feed(feed_url)
                
                for entry in feed.entries[:self.posts_per_newsletter]:
                    try:
                        # Parse published date with timezone
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        else:
                            published_at = datetime.now(timezone.utc)
                        
                        item = ContentItem(
                            title=entry.title,
                            url=entry.link,
                            source_type='substack',
                            source_name=f"Substack - {domain}",
                            published_at=published_at,
                            category=category,
                            description=entry.summary[:500] if hasattr(entry, 'summary') else None,
                            author=entry.author if hasattr(entry, 'author') else None
                        )
                        
                        item.relevance_score = 0.7  # Newsletters are curated
                        item.engagement_score = 0.6
                        
                        newsletter_items.append(item)
                    except Exception as e:
                        logger.debug(f"Error parsing entry from {domain}: {e}")
                        continue
                
                logger.debug(f"Fetched {len(newsletter_items)} posts from {domain}")
            except Exception as e:
                logger.error(f"❌ Error fetching {domain}: {e}")
            
            return newsletter_items
        
        # Fetch all newsletters in parallel
        tasks = [
            fetch_newsletter(domain, category) 
            for domain, category in self.newsletters.items()
        ]
        
        newsletter_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        items = []
        for result in newsletter_results:
            if isinstance(result, list):
                items.extend(result)
            elif isinstance(result, Exception):
                logger.debug(f"Newsletter fetch failed: {result}")
        
        logger.info(f"✅ Substack: Fetched {len(items)} posts from {len(self.newsletters)} newsletters")
        return items
    
    async def _fetch_feed(self, url: str):
        """Fetch and parse RSS feed with retry"""
        
        for attempt in range(2):  # Try twice
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url, 
                        timeout=aiohttp.ClientTimeout(total=15)  # Increased to 15s
                    ) as response:
                        if response.status != 200:
                            raise Exception(f"HTTP {response.status}")
                        
                        content = await response.text()
                        return feedparser.parse(content)
            
            except asyncio.TimeoutError:
                if attempt == 0:
                    logger.debug(f"Timeout on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception(f"Timeout after {attempt + 1} attempts")
            
            except Exception as e:
                if attempt == 0:
                    logger.debug(f"Error on attempt {attempt + 1}: {e}, retrying...")
                    await asyncio.sleep(1)
                    continue
                else:
                    raise


# Global instance
substack_scraper = SubstackScraper()
