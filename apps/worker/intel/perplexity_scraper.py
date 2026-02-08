"""
Perplexity Discover Aggregator

Scrapes trending topics from Perplexity Discover page.
"""

import aiohttp
from bs4 import BeautifulSoup
import logging
from typing import List
from datetime import datetime

from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory
)

logger = logging.getLogger(__name__)


class PerplexityScraper(BaseContentSource):
    """
    Perplexity Discover aggregator.
    
    Scrapes trending topics from Perplexity Discover page.
    """
    
    DISCOVER_URL = "https://www.perplexity.ai/discover"
    
    def __init__(self, limit: int = 20):
        """
        Initialize Perplexity scraper.
        
        Args:
            limit: Max items to fetch
        """
        super().__init__()
        self.limit = limit
        
        logger.info("✅ PerplexityScraper initialized")
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "Perplexity"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch trending topics from Perplexity Discover"""
        
        items = []
        
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36'
            )
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.DISCOVER_URL, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status != 200:
                        logger.error(f"HTTP {response.status} from Perplexity")
                        return items
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find links (Perplexity structure varies, use generic approach)
                    links = soup.find_all('a', href=True)
                    
                    seen_titles = set()
                    
                    for link in links:
                        if len(items) >= self.limit:
                            break
                        
                        try:
                            title = link.get_text(strip=True)
                            
                            if not title or len(title) < 10:
                                continue
                            
                            if title in seen_titles:
                                continue
                            seen_titles.add(title)
                            
                            url = link['href']
                            if not url.startswith('http'):
                                url = 'https://www.perplexity.ai' + url
                            
                            # Auto-categorize
                            category = self.categorize_by_keywords(title)
                            
                            item = ContentItem(
                                title=title,
                                url=url,
                                source_type='perplexity',
                                source_name='Perplexity Discover',
                                published_at=datetime.now(),
                                category=category,
                                description=None
                            )
                            
                            item.relevance_score = 0.7
                            item.engagement_score = 0.65
                            
                            items.append(item)
                        
                        except Exception as e:
                            logger.debug(f"Error parsing link: {e}")
                            continue
            
            logger.info(f"✅ Perplexity: Fetched {len(items)} items")
        
        except Exception as e:
            logger.error(f"❌ Error fetching Perplexity: {e}")
        
        return items


# Global instance
perplexity_scraper = PerplexityScraper()
