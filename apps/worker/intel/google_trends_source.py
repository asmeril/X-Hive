"""
Google Trends Content Source

Fetches trending searches from Google Trends.
"""

from pytrends.request import TrendReq
import asyncio
import logging
from typing import List, Optional
from datetime import datetime, timezone
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
        self.geo = geo
        self.limit = limit
        
        # Initialize pytrends with proper configuration
        try:
            self.pytrends = TrendReq(
                hl='en-US',
                tz=360,
                timeout=(10, 25),
                requests_args={'verify': True}  # Use requests_args instead of retries/backoff_factor
            )
            logger.info(f"✅ GoogleTrendsSource initialized (geo={geo}, limit={limit})")
        except Exception as e:
            logger.error(f"❌ Error initializing pytrends: {e}")
            self.pytrends = None
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "Google Trends"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch trending searches from Google Trends"""
        
        if not self.pytrends:
            logger.error("❌ Google Trends: pytrends not initialized")
            return []
        
        items = []
        
        try:
            # Fetch trending searches (synchronous call, run in executor)
            loop = asyncio.get_event_loop()
            
            try:
                trending_searches = await loop.run_in_executor(
                    None,
                    lambda: self.pytrends.trending_searches(pn=self.geo.lower())
                )
            except Exception as e:
                # Fallback to US if specific geo fails
                if self.geo != 'US':
                    logger.warning(f"⚠️  Failed for {self.geo}, trying US: {e}")
                    trending_searches = await loop.run_in_executor(
                        None,
                        lambda: self.pytrends.trending_searches(pn='united_states')
                    )
                else:
                    raise
            
            if trending_searches is None or trending_searches.empty:
                logger.warning("⚠️  No trending searches found")
                return items
            
            # Process trends
            for idx, trend in enumerate(trending_searches[0].head(self.limit)):
                if not trend or len(str(trend)) < 2:
                    continue
                
                # Create search URL
                search_url = f"https://www.google.com/search?q={str(trend).replace(' ', '+')}"
                
                # Auto-categorize
                category = self._categorize_trend(str(trend))
                
                item = ContentItem(
                    title=str(trend),
                    url=search_url,
                    source_type='google_trends',
                    source_name='Google Trends',
                    published_at=datetime.now(timezone.utc),
                    category=category,
                    description=f"Trending search: {trend}"
                )
                
                item.relevance_score = 0.8 - (idx * 0.02)  # Decay by rank
                item.engagement_score = 0.75
                
                items.append(item)
            
            logger.info(f"✅ Google Trends: Fetched {len(items)} trends")
        
        except Exception as e:
            logger.error(f"❌ Error fetching Google Trends: {e}")
        
        return items
    
    def _categorize_trend(self, trend: str) -> ContentCategory:
        """Auto-categorize trend"""
        
        trend_lower = trend.lower()
        
        if any(kw in trend_lower for kw in ['ai', 'chatgpt', 'openai', 'ml', 'robot', 'gemini', 'llm']):
            return ContentCategory.AI_ML
        elif any(kw in trend_lower for kw in ['crypto', 'bitcoin', 'ethereum', 'nft']):
            return ContentCategory.CRYPTO_WEB3
        elif any(kw in trend_lower for kw in ['game', 'gaming', 'esports', 'twitch', 'ps5', 'xbox']):
            return ContentCategory.GAMING_ENTERTAINMENT
        elif any(kw in trend_lower for kw in ['iphone', 'android', 'app', 'mobile']):
            return ContentCategory.MOBILE_APPS
        elif any(kw in trend_lower for kw in ['hack', 'breach', 'security', 'privacy']):
            return ContentCategory.SECURITY_PRIVACY
        elif any(kw in trend_lower for kw in ['startup', 'ipo', 'funding', 'vc']):
            return ContentCategory.STARTUP_BUSINESS
        elif any(kw in trend_lower for kw in ['python', 'javascript', 'code', 'developer']):
            return ContentCategory.TECH_PROGRAMMING
        else:
            return ContentCategory.GENERAL_NEWS


# Export
google_trends_source = GoogleTrendsSource()
