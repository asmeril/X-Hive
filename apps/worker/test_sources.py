"""
Test script for all API-based content sources
"""

import asyncio
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_all_sources():
    """Test all content sources"""
    
    print("\n" + "="*60)
    print("🧪 TESTING ALL API-BASED CONTENT SOURCES")
    print("="*60 + "\n")
    
    # Test Reddit
    print("📍 Testing Reddit Source...")
    try:
        from intel.reddit_source import reddit_source
        print("  ✅ Reddit source initialized")
        # Reddit source uses synchronous API, skip in async context
    except Exception as e:
        print(f"  ❌ Reddit error: {e}")
    
    # Test Hacker News
    print("\n📍 Testing Hacker News Source...")
    try:
        from intel.hackernews_source import hackernews_source
        items = await hackernews_source.fetch_latest()
        print(f"  ✅ Fetched {len(items)} HN stories")
        if items:
            print(f"     First story: {items[0].title[:60]}...")
            print(f"     Category: {items[0].category}")
            print(f"     Relevance: {items[0].relevance_score:.2f}")
    except Exception as e:
        print(f"  ❌ HN error: {e}")
    
    # Test ArXiv
    print("\n📍 Testing ArXiv Source...")
    try:
        from intel.arxiv_source import arxiv_source
        items = await arxiv_source.fetch_latest()
        print(f"  ✅ Fetched {len(items)} ArXiv papers")
        if items:
            print(f"     First paper: {items[0].title[:60]}...")
            print(f"     Category: {items[0].category}")
            print(f"     Authors: {items[0].author}")
    except Exception as e:
        print(f"  ❌ ArXiv error: {e}")
    
    # Test Product Hunt
    print("\n📍 Testing Product Hunt Source...")
    try:
        from intel.producthunt_source import producthunt_source
        items = await producthunt_source.fetch_latest()
        print(f"  ✅ Fetched {len(items)} PH products")
        if items:
            print(f"     First product: {items[0].title}")
            print(f"     Category: {items[0].category}")
            print(f"     Votes: {items[0].relevance_score:.2f}")
    except Exception as e:
        print(f"  ❌ Product Hunt error: {e}")
    
    # Test Google Trends
    print("\n📍 Testing Google Trends Source...")
    try:
        from intel.google_trends_source import google_trends_source
        items = await google_trends_source.fetch_latest()
        print(f"  ✅ Fetched {len(items)} Google Trends")
        if items:
            print(f"     First trend: {items[0].title}")
            print(f"     Category: {items[0].category}")
            print(f"     Relevance: {items[0].relevance_score:.2f}")
    except Exception as e:
        print(f"  ❌ Google Trends error: {e}")
    
    print("\n" + "="*60)
    print("✅ Source testing completed!")
    print("="*60 + "\n")


async def test_category_distribution():
    """Test category distribution system"""
    
    print("\n" + "="*60)
    print("📊 TESTING CATEGORY DISTRIBUTION SYSTEM")
    print("="*60 + "\n")
    
    from intel.base_source import (
        ContentItem,
        ContentCategory,
        CATEGORY_TARGETS,
        get_category_distribution,
        get_category_balance_score,
        group_by_category
    )
    
    # Create sample items with various categories
    items = [
        ContentItem(
            title="AI News 1",
            url="http://example.com/1",
            source_type="test",
            source_name="Test",
            category=ContentCategory.AI_ML
        ),
        ContentItem(
            title="Python Tutorial",
            url="http://example.com/2",
            source_type="test",
            source_name="Test",
            category=ContentCategory.TECH_PROGRAMMING
        ),
        ContentItem(
            title="Startup Funding",
            url="http://example.com/3",
            source_type="test",
            source_name="Test",
            category=ContentCategory.STARTUP_BUSINESS
        ),
        ContentItem(
            title="Game Release",
            url="http://example.com/4",
            source_type="test",
            source_name="Test",
            category=ContentCategory.GAMING_ENTERTAINMENT
        ),
        ContentItem(
            title="Bitcoin News",
            url="http://example.com/5",
            source_type="test",
            source_name="Test",
            category=ContentCategory.CRYPTO_WEB3
        ),
    ]
    
    # Test category targets
    print("📌 Category Targets:")
    for category, target in CATEGORY_TARGETS.items():
        print(f"  {category.value:.<30} {target*100:>5.1f}%")
    
    # Test category distribution
    dist = get_category_distribution(items)
    print("\n📌 Current Distribution (5 items):")
    for category, percentage in dist.items():
        target = CATEGORY_TARGETS[category]
        status = "✅" if percentage > 0 else "⚠️"
        print(f"  {status} {category.value:.<30} {percentage*100:>5.1f}% (target: {target*100:>5.1f}%)")
    
    # Test balance score
    balance = get_category_balance_score(items)
    print(f"\n📊 Balance Score: {balance:.2f}/1.0")
    print(f"   {'🟢 Good' if balance > 0.8 else '🟡 Fair' if balance > 0.6 else '🔴 Poor'}")
    
    # Test grouping
    grouped = group_by_category(items)
    print("\n📌 Items by Category:")
    for category, category_items in grouped.items():
        if category_items:
            print(f"  {category.value:.<30} {len(category_items)} items")
    
    print("\n" + "="*60)
    print("✅ Category testing completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_all_sources())
    asyncio.run(test_category_distribution())
