"""
RSS News Aggregator - Multiple Quality Sources

Aggregates news from various RSS feeds covering different domains:
- BBC World News (global perspective)
- Nature Science (research breakthroughs)
- NewAtlas (inventions/tech)
- Medical News (health/biotech)
- Defense News (geopolitics)
- AutoBlog (automotive/EV)
"""

import aiohttp
import asyncio
import feedparser
import logging
from typing import List, Dict
from datetime import datetime, timezone

from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory
)

logger = logging.getLogger(__name__)


class RSSNewsSource(BaseContentSource):
    """
    Multi-domain RSS news aggregator.
    
    Fetches from curated quality sources across multiple domains.
    """
    
    RSS_FEEDS = {
        # Global News
        'bbc_world': {
            'url': 'http://feeds.bbci.co.uk/news/world/rss.xml',
            'category': ContentCategory.NEWS,
            'name': 'BBC World News'
        },
        
        # Science
        'nature': {
            'url': 'https://www.nature.com/nature.rss',
            'category': ContentCategory.SCIENCE,
            'name': 'Nature Science'
        },
        
        # Inventions/Tech
        'newatlas': {
            'url': 'https://newatlas.com/index.rss',
            'category': ContentCategory.TECH_PROGRAMMING,
            'name': 'NewAtlas Inventions'
        },
        
        # Health/Biotech
        'medical_news': {
            'url': 'https://rss.medicalnewstoday.com/medicalnewstoday.xml',
            'category': ContentCategory.SCIENCE,
            'name': 'Medical News Today'
        },
        
        # Defense/Geopolitics
        'defense_news': {
            'url': 'https://www.defensenews.com/arc/outboundfeeds/rss/category/global/?size=10',
            'category': ContentCategory.NEWS,
            'name': 'Defense News'
        },
        
        # Automotive
        'autoblog': {
            'url': 'https://www.autoblog.com/rss.xml',
            'category': ContentCategory.TECH_PROGRAMMING,
            'name': 'AutoBlog'
        },
    }
    
    def __init__(
        self,
        feeds: Dict = None,
        items_per_feed: int = 5
    ):
        """
        Initialize RSS news source.
        
        Args:
            feeds: Custom feed configuration
            items_per_feed: Items to fetch per feed
        """
        super().__init__()
        
        self.feeds = feeds or self.RSS_FEEDS
        self.items_per_feed = items_per_feed
        
        logger.info(f"✅ RSSNewsSource initialized ({len(self.feeds)} feeds)")
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "RSS News"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch latest news from all RSS feeds (parallel)"""
        
        # Fetch all feeds in parallel
        tasks = [
            self._fetch_feed(feed_id, config)
            for feed_id, config in self.feeds.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        items = []
        for result in results:
            if isinstance(result, list):
                items.extend(result)
            elif isinstance(result, Exception):
                logger.debug(f"Feed fetch failed: {result}")
        
        logger.info(f"✅ RSS News: Fetched {len(items)} items from {len(self.feeds)} feeds")
        return items
    
    async def _fetch_feed(
        self,
        feed_id: str,
        config: Dict
    ) -> List[ContentItem]:
        """Fetch single RSS feed"""
        
        items = []
        url = config['url']
        category = config['category']
        source_name = config['name']
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    
                    if response.status != 200:
                        logger.debug(f"❌ {source_name}: HTTP {response.status}")
                        return items
                    
                    content = await response.text()
                    feed = feedparser.parse(content)
                    
                    for entry in feed.entries[:self.items_per_feed]:
                        try:
                            # Parse published date
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                            else:
                                published_at = datetime.now(timezone.utc)
                            
                            # Extract description
                            description = None
                            if hasattr(entry, 'summary'):
                                description = entry.summary[:500]
                            elif hasattr(entry, 'description'):
                                description = entry.description[:500]
                            
                            item = ContentItem(
                                title=entry.title,
                                url=entry.link,
                                source_type='rss_news',
                                source_name=source_name,
                                published_at=published_at,
                                category=category,
                                description=description
                            )
                            
                            # RSS feeds are curated/editorial
                            item.relevance_score = 0.65
                            item.engagement_score = 0.6
                            
                            items.append(item)
                        
                        except Exception as e:
                            logger.debug(f"Error parsing entry from {source_name}: {e}")
                            continue
            
            logger.debug(f"Fetched {len(items)} items from {source_name}")
        
        except Exception as e:
            logger.error(f"❌ Error fetching {source_name}: {e}")
        
        return items


# Global instance
rss_news_source = RSSNewsSource()
