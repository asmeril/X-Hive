"""
Content Aggregator for X-Hive

Combines all intel sources into unified feed.
Handles deduplication, filtering, sorting, and statistics.
"""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory,
    ContentQuality,
    filter_by_keywords,
    filter_by_quality,
    deduplicate_by_url,
    sort_by_relevance
)
from .rss_source import tech_news_source, ai_news_source
from .telegram_source import telegram_source
from .github_source import github_trending_source, github_ai_source
from .reddit_source import reddit_source
from .hackernews_source import hackernews_source
from .arxiv_source import arxiv_source
from .producthunt_source import producthunt_source
from .google_trends_source import google_trends_source
from .huggingface_source import huggingface_source
from .polymarket_source import polymarket_source
from .rss_news_source import rss_news_source
from .twitter_trends_source import twitter_trends_source

logger = logging.getLogger(__name__)


class ContentAggregator:
    """
    Aggregates content from all intel sources.
    
    Features:
    - Multi-source fetching (concurrent)
    - Automatic deduplication by URL
    - Relevance and recency filtering
    - Category-based grouping
    - Engagement scoring
    """
    
    def __init__(
        self,
        use_rss: bool = True,
        use_telegram: bool = False,
        use_github: bool = True,
        use_reddit: bool = False,  # Disabled due to timeout issues
        use_hackernews: bool = True,
        use_arxiv: bool = True,
        use_producthunt: bool = False,  # Disabled due to timeout issues
        use_google_trends: bool = False,  # Disabled due to timeout issues
        use_huggingface: bool = False,  # Disabled due to timeout issues
        use_polymarket: bool = False,  # Disabled due to timeout issues
        use_rss_news: bool = False,  # Disabled due to connection issues
        use_twitter_trends: bool = False,
        min_relevance: float = 0.5,
        max_items: int = 50
    ):
        """
        Initialize content aggregator.
        """
        
        self.use_rss = use_rss
        self.use_telegram = use_telegram
        self.use_github = use_github
        self.use_reddit = use_reddit
        self.use_hackernews = use_hackernews
        self.use_arxiv = use_arxiv
        self.use_producthunt = use_producthunt
        self.use_google_trends = use_google_trends
        self.use_huggingface = use_huggingface
        self.use_polymarket = use_polymarket
        self.use_rss_news = use_rss_news
        self.use_twitter_trends = use_twitter_trends
        self.min_relevance = min_relevance
        self.max_items = max_items
        
        # Sources
        self.sources: List[BaseContentSource] = []
        
        if use_rss:
            self.sources.extend([tech_news_source, ai_news_source])
        
        if use_telegram and telegram_source:
            self.sources.append(telegram_source)
        
        if use_github:
            self.sources.extend([github_trending_source, github_ai_source])
        
        if use_reddit:
            self.sources.append(reddit_source)
        
        if use_hackernews:
            self.sources.append(hackernews_source)
        
        if use_arxiv:
            self.sources.append(arxiv_source)
        
        if use_producthunt:
            self.sources.append(producthunt_source)
        
        if use_google_trends:
            self.sources.append(google_trends_source)
        
        if use_huggingface:
            self.sources.append(huggingface_source)
        
        if use_polymarket:
            self.sources.append(polymarket_source)
        
        if use_rss_news:
            self.sources.append(rss_news_source)
        
        if use_twitter_trends:
            self.sources.append(twitter_trends_source)
        
        logger.info(f"ContentAggregator initialized with {len(self.sources)} sources")
    
    async def fetch_all(self) -> List[ContentItem]:
        """
        Fetch content from all enabled sources.
        """
        
        logger.info(f"Fetching content from {len(self.sources)} sources...")
        
        all_items = []
        
        # Fetch from all sources concurrently
        tasks = []
        
        for source in self.sources:
            task = self._fetch_source_safe(source)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Source {self.sources[i].get_source_name()} failed: {result}")
                continue
            
            if isinstance(result, list):
                all_items.extend(result)
        
        logger.info(f"Collected {len(all_items)} items from all sources")
        
        # Process items
        processed = self._process_items(all_items)
        
        logger.info(f"Returning {len(processed)} processed items")
        
        return processed
    
    async def _fetch_source_safe(self, source: BaseContentSource) -> List[ContentItem]:
        """
        Safely fetch from a source with error handling and timeout.
        """
        
        try:
            # Add timeout to prevent hanging
            items = await asyncio.wait_for(
                source.fetch_with_tracking(), 
                timeout=30.0  # 30 second timeout per source
            )
            logger.info(f"{source.get_source_name()}: {len(items)} items")
            return items
        
        except asyncio.TimeoutError:
            logger.warning(f"{source.get_source_name()}: Timeout after 30s")
            return []
        
        except Exception as e:
            logger.error(f"{source.get_source_name()} failed: {e}")
            return []
    
    def _process_items(self, items: List[ContentItem]) -> List[ContentItem]:
        """
        Process items: deduplicate, filter, sort.
        """
        
        # Step 1: Deduplicate by URL
        items = deduplicate_by_url(items)
        logger.debug(f"After deduplication: {len(items)} items")
        
        # Step 2: Filter by relevance score
        items = [item for item in items if item.relevance_score >= self.min_relevance]
        logger.debug(f"After relevance filter: {len(items)} items")
        
        # Step 3: Filter recent (last 7 days)
        from datetime import timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        
        def safe_datetime_compare(dt, cutoff):
            """Safely compare datetime, handling timezone differences."""
            if dt is None:
                return False
            if dt.tzinfo is None:
                # Make naive datetime timezone-aware (assume UTC)
                dt = dt.replace(tzinfo=timezone.utc)
            return dt > cutoff
        
        filtered_items = []
        for item in items:
            if safe_datetime_compare(item.published_at, cutoff):
                filtered_items.append(item)
            elif safe_datetime_compare(item.collected_at, cutoff):
                filtered_items.append(item)
            else:
                filtered_items.append(item)  # Include items without dates
        
        items = filtered_items
        logger.debug(f"After recency filter: {len(items)} items")
        
        # Step 4: Sort by combined score
        items = sorted(
            items,
            key=lambda x: (x.relevance_score * 0.6 + x.engagement_score * 0.4),
            reverse=True
        )
        
        # Step 5: Limit results
        items = items[:self.max_items]
        
        return items
    
    def get_by_category(self, items: List[ContentItem]) -> Dict[ContentCategory, List[ContentItem]]:
        """
        Group items by category.
        """
        
        grouped = defaultdict(list)
        
        for item in items:
            grouped[item.category].append(item)
        
        return dict(grouped)
    
    def get_top_items(self, items: List[ContentItem], n: int = 10) -> List[ContentItem]:
        """
        Get top N items by combined score.
        """
        
        return sorted(
            items,
            key=lambda x: (x.relevance_score * 0.6 + x.engagement_score * 0.4),
            reverse=True
        )[:n]


# Global aggregator instance
aggregator = ContentAggregator(
    use_rss=True,
    use_telegram=False,
    use_github=True,
    use_reddit=True,
    use_hackernews=True,
    use_arxiv=True,
    use_producthunt=True,
    use_google_trends=True,
    use_huggingface=True,
    use_polymarket=True,
    use_rss_news=True,
    use_twitter_trends=False,
    min_relevance=0.5,
    max_items=50
)
