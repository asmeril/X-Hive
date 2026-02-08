"""
Medium Article Aggregator

Scrapes trending tech/AI/startup articles.
Uses cookies to bypass paywall if available.
"""

import aiohttp
from bs4 import BeautifulSoup
import logging
from typing import List, Optional
from datetime import datetime
import re

from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory
)
from .cookie_manager import get_cookie_manager

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
        articles_per_topic: int = 5
    ):
        """
        Initialize Medium scraper.
        
        Args:
            topics: Custom topic -> category mapping
            articles_per_topic: Articles to fetch per topic
        """
        super().__init__()
        
        self.cookie_manager = get_cookie_manager()
        self.topics = topics or self.TOPICS
        self.articles_per_topic = articles_per_topic
        
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
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {topic}")
                    return items
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find article links (Medium uses h2/h3 for titles)
                article_links = soup.find_all('a', href=re.compile(r'medium\.com/.*'))
                
                seen_urls = set()
                
                for link in article_links[:self.articles_per_topic * 3]:  # Get more, filter duplicates
                    try:
                        url = link['href']
                        
                        # Skip if already seen
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)
                        
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
                        if not url.startswith('http'):
                            url = 'https://medium.com' + url
                        
                        # Create item
                        item = ContentItem(
                            title=title,
                            url=url,
                            source_type='medium',
                            source_name=f"Medium - {topic}",
                            published_at=datetime.now(),
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


# Global instance
medium_scraper = MediumScraper()
