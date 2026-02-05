"""
Content Aggregator for X-Hive

Combines all intel sources (RSS, Telegram, GitHub) into unified feed.
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

logger = logging.getLogger(__name__)


class ContentAggregator:
    """
    Aggregates content from all intel sources.
    
    Combines RSS, Telegram, and GitHub sources into unified feed.
    Handles deduplication, filtering, and sorting.
    
    Features:
    - Multi-source fetching (concurrent)
    - Automatic deduplication by URL
    - Relevance and recency filtering
    - Category-based grouping
    - Engagement scoring
    - Comprehensive statistics
    """
    
    def __init__(
        self,
        use_rss: bool = True,
        use_telegram: bool = False,  # Default off until channels configured
        use_github: bool = True,
        min_relevance: float = 0.5,
        max_items: int = 50
    ):
        """
        Initialize content aggregator.
        
        Args:
            use_rss: Enable RSS sources
            use_telegram: Enable Telegram sources
            use_github: Enable GitHub sources
            min_relevance: Minimum relevance score (0-1)
            max_items: Maximum items to return
        """
        
        self.use_rss = use_rss
        self.use_telegram = use_telegram
        self.use_github = use_github
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
        
        logger.info(f"✅ ContentAggregator initialized with {len(self.sources)} sources")
    
    async def fetch_all(self) -> List[ContentItem]:
        """
        Fetch content from all enabled sources.
        
        Returns:
            List of ContentItem objects (deduplicated, filtered, sorted)
        """
        
        logger.info(f"📡 Fetching content from {len(self.sources)} sources...")
        
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
                logger.error(f"❌ Source {self.sources[i].get_source_name()} failed: {result}")
                continue
            
            if isinstance(result, list):
                all_items.extend(result)
        
        logger.info(f"📊 Collected {len(all_items)} items from all sources")
        
        # Process items
        processed = self._process_items(all_items)
        
        logger.info(f"✅ Returning {len(processed)} processed items")
        
        return processed
    
    async def _fetch_source_safe(self, source: BaseContentSource) -> List[ContentItem]:
        """
        Safely fetch from a source with error handling.
        
        Args:
            source: Content source
        
        Returns:
            List of ContentItem objects (or empty on error)
        """
        
        try:
            items = await source.fetch_with_tracking()
            logger.info(f"✅ {source.get_source_name()}: {len(items)} items")
            return items
        
        except Exception as e:
            logger.error(f"❌ {source.get_source_name()} failed: {e}")
            return []
    
    def _process_items(self, items: List[ContentItem]) -> List[ContentItem]:
        """
        Process items: deduplicate, filter, sort.
        
        Args:
            items: Raw items
        
        Returns:
            Processed items
        """
        
        # Step 1: Deduplicate by URL
        items = deduplicate_by_url(items)
        logger.debug(f"After deduplication: {len(items)} items")
        
        # Step 2: Filter by relevance score
        items = [item for item in items if item.relevance_score >= self.min_relevance]
        logger.debug(f"After relevance filter: {len(items)} items")
        
        # Step 3: Filter recent (last 7 days)
        cutoff = datetime.now() - timedelta(days=7)
        
        # Filter items with valid dates
        filtered_items = []
        for item in items:
            # Check published_at if available
            if item.published_at:
                try:
                    # Handle timezone-aware datetimes
                    if item.published_at.tzinfo is not None:
                        cutoff_aware = cutoff.replace(tzinfo=item.published_at.tzinfo)
                        if item.published_at > cutoff_aware:
                            filtered_items.append(item)
                    elif item.published_at > cutoff:
                        filtered_items.append(item)
                except:
                    # If comparison fails, include the item
                    filtered_items.append(item)
            # Fallback to collected_at
            elif item.collected_at and item.collected_at > cutoff:
                filtered_items.append(item)
            else:
                # Include items without dates (GitHub trending, etc.)
                filtered_items.append(item)
        
        items = filtered_items
        logger.debug(f"After recency filter: {len(items)} items")
        
        # Step 4: Sort by combined score (relevance 60%, engagement 40%)
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
        
        Args:
            items: Content items
        
        Returns:
            Dictionary mapping category to items
        """
        
        grouped = defaultdict(list)
        
        for item in items:
            grouped[item.category].append(item)
        
        return dict(grouped)
    
    def get_top_items(self, items: List[ContentItem], n: int = 10) -> List[ContentItem]:
        """
        Get top N items by combined score.
        
        Args:
            items: Content items
            n: Number of items
        
        Returns:
            Top N items
        """
        
        return sorted(
            items,
            key=lambda x: (x.relevance_score * 0.6 + x.engagement_score * 0.4),
            reverse=True
        )[:n]
    
    def get_ai_ml_items(self, items: List[ContentItem]) -> List[ContentItem]:
        """
        Get only AI/ML related items.
        
        Args:
            items: Content items
        
        Returns:
            AI/ML items sorted by score
        """
        
        ai_items = [item for item in items if item.category == ContentCategory.AI_ML]
        
        return sorted(
            ai_items,
            key=lambda x: (x.relevance_score * 0.6 + x.engagement_score * 0.4),
            reverse=True
        )
    
    def get_stats(self, items: List[ContentItem]) -> Dict:
        """
        Get aggregation statistics.
        
        Args:
            items: Content items
        
        Returns:
            Statistics dictionary
        """
        
        categories = defaultdict(int)
        sources = defaultdict(int)
        
        for item in items:
            categories[item.category] += 1
            sources[item.source_type] += 1
        
        return {
            'total_items': len(items),
            'categories': dict(categories),
            'sources': dict(sources),
            'avg_relevance': sum(i.relevance_score for i in items) / len(items) if items else 0,
            'avg_engagement': sum(i.engagement_score for i in items) / len(items) if items else 0,
            'ai_ml_count': sum(1 for i in items if i.category == ContentCategory.AI_ML)
        }
    
    async def fetch_ai_content(self) -> List[ContentItem]:
        """
        Fetch only AI/ML focused content (convenience method).
        
        Returns:
            AI/ML content items
        """
        
        all_items = await self.fetch_all()
        return self.get_ai_ml_items(all_items)
    
    async def fetch_top_stories(self, n: int = 10) -> List[ContentItem]:
        """
        Fetch top N stories from all sources.
        
        Args:
            n: Number of stories
        
        Returns:
            Top N stories
        """
        
        all_items = await self.fetch_all()
        return self.get_top_items(all_items, n)


# Global instance
aggregator = ContentAggregator(
    use_rss=True,
    use_telegram=False,  # Enable after configuring channels
    use_github=True,
    min_relevance=0.5,
    max_items=50
)


# Test example
async def test_aggregator():
    """Test content aggregator"""
    
    print("=" * 80)
    print("🧪 CONTENT AGGREGATOR TEST")
    print("=" * 80)
    
    agg = ContentAggregator(
        use_rss=True,
        use_telegram=False,
        use_github=True,
        min_relevance=0.5,
        max_items=30
    )
    
    print("\n[1] Fetching from all sources...")
    items = await agg.fetch_all()
    
    print(f"\n✅ Fetched {len(items)} items total")
    
    # Statistics
    print("\n" + "=" * 80)
    print("📊 STATISTICS")
    print("=" * 80)
    
    stats = agg.get_stats(items)
    print(f"\nTotal items: {stats['total_items']}")
    print(f"AI/ML items: {stats['ai_ml_count']}")
    print(f"Avg relevance: {stats['avg_relevance']:.2f}")
    print(f"Avg engagement: {stats['avg_engagement']:.2f}")
    
    print("\nCategories:")
    for category, count in stats['categories'].items():
        print(f"   {category.name}: {count}")
    
    print("\nSources:")
    for source, count in stats['sources'].items():
        print(f"   {source}: {count}")
    
    # Top 10 stories
    print("\n" + "=" * 80)
    print("🔥 TOP 10 STORIES")
    print("=" * 80)
    
    top_items = agg.get_top_items(items, 10)
    
    for idx, item in enumerate(top_items, 1):
        score = item.relevance_score * 0.6 + item.engagement_score * 0.4
        print(f"\n{idx}. {item.title[:80]}")
        print(f"   Source: {item.source_name} ({item.source_type})")
        print(f"   Category: {item.category.name}")
        print(f"   Score: {score:.2f} (R:{item.relevance_score:.2f} E:{item.engagement_score:.2f})")
        print(f"   URL: {item.url}")
    
    # AI/ML content
    print("\n" + "=" * 80)
    print("🤖 AI/ML CONTENT")
    print("=" * 80)
    
    ai_items = agg.get_ai_ml_items(items)
    print(f"\nFound {len(ai_items)} AI/ML items")
    
    for idx, item in enumerate(ai_items[:5], 1):
        print(f"\n{idx}. {item.title[:80]}")
        print(f"   Source: {item.source_name}")
    
    print("\n" + "=" * 80)
    print("✅ AGGREGATOR TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_aggregator())
