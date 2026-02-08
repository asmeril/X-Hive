"""
Substack Newsletter Aggregator

Scrapes popular tech/AI/startup newsletters via RSS feeds.
"""

import aiohttp
import feedparser
import logging
from typing import List, Optional
from datetime import datetime

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
        'thealgorithmicbridge.substack.com': ContentCategory.AI_ML,
        
        # Tech/Programming
        'newsletter.pragmaticengineer.com': ContentCategory.TECH_PROGRAMMING,
        'blog.bytebytego.com': ContentCategory.TECH_PROGRAMMING,
        
        # Startup/Business
        'www.lennysnewsletter.com': ContentCategory.STARTUP_BUSINESS,
        'every.to': ContentCategory.STARTUP_BUSINESS,
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
        """Fetch latest posts from Substack newsletters"""
        
        items = []
        
        for domain, category in self.newsletters.items():
            try:
                # Substack RSS feed URL
                feed_url = f"https://{domain}/feed"
                
                # Fetch RSS feed
                feed = await self._fetch_feed(feed_url)
                
                # Parse entries
                for entry in feed.entries[:self.posts_per_newsletter]:
                    try:
                        item = ContentItem(
                            title=entry.title,
                            url=entry.link,
                            source_type='substack',
                            source_name=f"Substack - {domain}",
                            published_at=datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now(),
                            category=category,
                            description=entry.summary[:500] if hasattr(entry, 'summary') else None,
                            author=entry.author if hasattr(entry, 'author') else None
                        )
                        
                        item.relevance_score = 0.7  # Newsletters are curated
                        item.engagement_score = 0.6
                        
                        items.append(item)
                    
                    except Exception as e:
                        logger.debug(f"Error parsing entry: {e}")
                        continue
                
                logger.debug(f"Fetched {len([i for i in items if domain in i.source_name])} posts from {domain}")
            
            except Exception as e:
                logger.error(f"❌ Error fetching {domain}: {e}")
                continue
        
        logger.info(f"✅ Substack: Fetched {len(items)} posts from {len(self.newsletters)} newsletters")
        return items
    
    async def _fetch_feed(self, url: str):
        """Fetch and parse RSS feed"""
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                content = await response.text()
                return feedparser.parse(content)


# Global instance
substack_scraper = SubstackScraper()
