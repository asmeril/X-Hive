"""Test newly integrated sources from HiveProjesi"""

import asyncio
import sys
from pathlib import Path

# Add worker path
sys.path.append(str(Path(__file__).parent / "apps" / "worker"))

from intel.polymarket_source import polymarket_source
from intel.rss_news_source import rss_news_source


async def test_polymarket():
    """Test Polymarket prediction markets"""
    print("\n" + "="*60)
    print("🔮 Testing Polymarket...")
    print("="*60)
    
    try:
        items = await polymarket_source.fetch_latest()
        print(f"\n✅ Fetched {len(items)} prediction markets\n")
        
        for item in items[:5]:
            print(f"📊 {item.title}")
            print(f"   URL: {item.url}")
            print(f"   Category: {item.category}")
            print(f"   Relevance: {item.relevance_score:.2f}")
            if item.description:
                print(f"   Description: {item.description[:100]}...")
            print()
    
    except Exception as e:
        print(f"❌ Polymarket error: {e}")
        import traceback
        traceback.print_exc()


async def test_rss_news():
    """Test RSS News aggregator"""
    print("\n" + "="*60)
    print("📰 Testing RSS News Aggregator...")
    print("="*60)
    
    try:
        items = await rss_news_source.fetch_latest()
        print(f"\n✅ Fetched {len(items)} items from RSS feeds\n")
        
        # Group by source
        by_source = {}
        for item in items:
            source = item.source_name
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(item)
        
        # Show summary
        for source, source_items in by_source.items():
            print(f"\n{source}: {len(source_items)} items")
            for item in source_items[:2]:
                print(f"  • {item.title[:80]}")
                print(f"    {item.url}")
    
    except Exception as e:
        print(f"❌ RSS News error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests"""
    print("\n🚀 Testing HiveProjesi Integrations")
    
    await test_polymarket()
    await test_rss_news()
    
    print("\n" + "="*60)
    print("✅ Testing Complete")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
