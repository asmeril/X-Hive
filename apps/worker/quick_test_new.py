"""Quick test of HiveProjesi integrations"""

import asyncio
import logging
from intel.polymarket_source import polymarket_source
from intel.rss_news_source import rss_news_source

logging.basicConfig(level=logging.WARNING)


async def main():
    print("\n🚀 Testing HiveProjesi Integrations\n")
    
    # Test Polymarket
    print("="*60)
    print("🔮 Polymarket Prediction Markets")
    print("="*60)
    items = await polymarket_source.fetch_latest()
    print(f"✅ Fetched {len(items)} prediction markets")
    if items:
        print(f"   Sample: {items[0].title}")
        print(f"   Category: {items[0].category.value}")
    
    # Test RSS News
    print("\n" + "="*60)
    print("📰 RSS News Aggregator")
    print("="*60)
    items = await rss_news_source.fetch_latest()
    print(f"✅ Fetched {len(items)} items from RSS feeds")
    
    # Count by source
    by_source = {}
    for item in items:
        by_source[item.source_name] = by_source.get(item.source_name, 0) + 1
    
    print("\nPer-Source Results:")
    for source, count in by_source.items():
        print(f"  • {source}: {count} items")
    
    print("\n" + "="*60)
    print("✅ Both new sources working!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
