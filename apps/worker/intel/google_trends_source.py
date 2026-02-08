"""
Google Trends Content Source

Fetches trending searches from Google Trends.
"""

from pytrends.request import TrendReq
import logging
from typing import List, Optional
from datetime import datetime
from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory,
    ContentSourceError,
    CATEGORY_TARGETS
)
from .cookie_manager import get_cookie_manager

logger = logging.getLogger(__name__)


class GoogleTrendsSource(BaseContentSource):
    """
    Google Trends aggregator.
    
    Fetches trending searches.
    """
    
    def __init__(
        self,
        geo: str = 'TR',  # Turkey
        limit: int = 20
    ):
        super().__init__()
        self.cookie_manager = get_cookie_manager()
        self.pytrends = TrendReq(hl='en-US', tz=360)
        self.geo = geo
        self.limit = limit
        
        logger.info(f"✅ GoogleTrendsSource initialized (geo={geo}, limit={limit})")
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "Google Trends"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch trending searches"""
        
        items = []
        
        try:
            # Get trending searches
            trending = self.pytrends.trending_searches(pn=self.geo.lower())
            
            for idx, keyword in enumerate(trending[0][:self.limit]):
                # Create ContentItem
                item = ContentItem(
                    title=f"Trending: {keyword}",
                    url=f"https://trends.google.com/trends/explore?q={keyword}&geo={self.geo}",
                    source_type='google_trends',
                    source_name=f"Google Trends ({self.geo})",
                    published_at=datetime.now(),
                    description=f"Trending search query: {keyword}"
                )
                
                # Categorize based on keyword
                item.category = self._categorize_trend(keyword)
                
                # Scores (trends are relevant by definition)
                item.relevance_score = max(0.5, 1.0 - (idx * 0.02))  # Decay by position
                item.engagement_score = 0.7
                
                items.append(item)
            
            logger.info(f"✅ Fetched {len(items)} trends from Google Trends")
        
        except Exception as e:
            logger.error(f"❌ Error fetching Google Trends: {e}")
        
        return items
    
    def _categorize_trend(self, keyword: str) -> ContentCategory:
        """Categorize trend based on keyword"""
        kw_lower = keyword.lower()
        
        if any(term in kw_lower for term in ['ai', 'chatgpt', 'gemini', 'llm']):
            return ContentCategory.AI_ML
        
        if any(term in kw_lower for term in ['crypto', 'bitcoin', 'ethereum']):
            return ContentCategory.CRYPTO_WEB3
        
        if any(term in kw_lower for term in ['game', 'gaming', 'ps5', 'xbox']):
            return ContentCategory.GAMING_ENTERTAINMENT
        
        if any(term in kw_lower for term in ['app', 'iphone', 'android']):
            return ContentCategory.MOBILE_APPS
        
        if any(term in kw_lower for term in ['hack', 'breach', 'security']):
            return ContentCategory.SECURITY_PRIVACY
        
        # Default
        return ContentCategory.TECH_PROGRAMMING


# Export
google_trends_source = GoogleTrendsSource()
