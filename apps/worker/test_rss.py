"""
RSS Content Source Test Suite

Tests RSS feed fetching, categorization, and filtering
"""

import asyncio
import logging
from intel.rss_source import (
    RSSSource,
    tech_news_source,
    ai_news_source,
    ai_research_source
)
from intel.base_source import ContentCategory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_rss_sources():
    """Test all RSS sources"""
    
    print("\n" + "="*80)
    print("RSS CONTENT SOURCE TEST")
    print("="*80 + "\n")
    
    # Test 1: Tech News Source
    print("[TEST 1] Tech News Aggregator")
    print("-" * 80)
    
    try:
        items = await tech_news_source.fetch_with_tracking(limit=10)
        
        print(f"✅ Fetched {len(items)} items from tech news sources")
        print(f"\nSample items:")
        
        for i, item in enumerate(items[:5], 1):
            print(f"\n{i}. {item.title}")
            print(f"   Source: {item.source_name}")
            print(f"   Category: {item.category}")
            print(f"   URL: {item.url}")
            print(f"   Published: {item.published_at}")
        
        # Category breakdown
        categories = {}
        for item in items:
            categories[item.category] = categories.get(item.category, 0) + 1
        
        print(f"\n📊 Category breakdown:")
        for cat, count in categories.items():
            print(f"   {cat}: {count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: AI News Source
    print("\n[TEST 2] AI & ML News Aggregator")
    print("-" * 80)
    
    try:
        items = await ai_news_source.fetch_with_tracking(limit=15)
        
        print(f"✅ Fetched {len(items)} items from AI news sources")
        
        # Filter AI/ML only
        ai_items = [item for item in items if item.category == ContentCategory.AI_ML]
        
        print(f"🤖 AI/ML items: {len(ai_items)}/{len(items)}")
        print(f"\nTop AI/ML items:")
        
        for i, item in enumerate(ai_items[:5], 1):
            print(f"\n{i}. {item.title}")
            print(f"   Source: {item.source_name}")
            print(f"   URL: {item.url[:60]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: AI Research Source
    print("\n[TEST 3] AI Research News")
    print("-" * 80)
    
    try:
        items = await ai_research_source.fetch_with_tracking(limit=10)
        
        print(f"✅ Fetched {len(items)} items from AI research sources")
        print(f"\nLatest AI research:")
        
        for i, item in enumerate(items[:3], 1):
            print(f"\n{i}. {item.title}")
            print(f"   Source: {item.source_name}")
            print(f"   Category: {item.category}")
            print(f"   Tags: {', '.join(item.tags[:5]) if item.tags else 'None'}")
            if item.description:
                print(f"   Description: {item.description[:150]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Source Statistics
    print("\n[TEST 4] Source Statistics")
    print("-" * 80)
    
    sources = [
        ("Tech News", tech_news_source),
        ("AI News", ai_news_source),
        ("AI Research", ai_research_source)
    ]
    
    for name, source in sources:
        stats = source.get_stats()
        print(f"\n{name}:")
        print(f"   Source type: {stats['source_type']}")
        print(f"   Fetch count: {stats['fetch_count']}")
        print(f"   Error count: {stats['error_count']}")
        print(f"   Last fetch: {stats['last_fetch']}")
    
    print("\n" + "="*80)
    print("✅ ALL RSS TESTS COMPLETE")
    print("="*80 + "\n")


async def test_single_feed():
    """Test a single RSS feed"""
    
    print("\n🧪 Testing single feed...\n")
    
    # Test with a single feed dictionary
    single_feed = {
        'TechCrunch': 'https://techcrunch.com/feed/'
    }
    
    source = RSSSource(
        feed_name='TechCrunch Only',
        feeds=single_feed,
        category=None,  # Auto-categorize
        max_items=5
    )
    
    items = await source.fetch_latest(limit=5)
    
    print(f"✅ Fetched {len(items)} items\n")
    
    for i, item in enumerate(items, 1):
        print(f"{i}. [{item.category}] {item.title}")
        print(f"   URL: {item.url}")
        print(f"   Published: {item.published_at}")
        print()


async def test_categorization():
    """Test auto-categorization logic"""
    
    print("\n🧪 Testing categorization...\n")
    
    # Create source with all feeds
    source = RSSSource(
        feed_name="Categorization Test",
        max_items=3
    )
    
    items = await source.fetch_latest(limit=20)
    
    # Group by category
    by_category = {}
    for item in items:
        cat = item.category
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    print(f"✅ Fetched {len(items)} items across {len(by_category)} categories\n")
    
    for category, cat_items in by_category.items():
        print(f"📁 {category}: {len(cat_items)} items")
        for item in cat_items[:2]:
            print(f"   - {item.title[:60]}... ({item.source_name})")
        print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "single":
            asyncio.run(test_single_feed())
        elif sys.argv[1] == "categorize":
            asyncio.run(test_categorization())
        else:
            print("Usage: python test_rss.py [single|categorize]")
    else:
        asyncio.run(test_rss_sources())
