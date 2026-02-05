#!/usr/bin/env python3
"""
Test Content Aggregator
Combines RSS + GitHub sources (Telegram disabled for now)
"""

import asyncio
import sys
import os
import logging

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from intel.aggregator import ContentAggregator
from intel.base_source import ContentCategory


async def main():
    """Test content aggregator"""
    
    print("=" * 80)
    print("🧪 CONTENT AGGREGATOR TEST")
    print("=" * 80)
    
    # Initialize aggregator
    print("\n[1] Initializing aggregator...")
    agg = ContentAggregator(
        use_rss=True,
        use_telegram=False,  # Disabled until channels configured
        use_github=True,
        min_relevance=0.5,
        max_items=30
    )
    
    # Fetch all content
    print("\n[2] Fetching from all sources (RSS + GitHub)...")
    items = await agg.fetch_all()
    
    print(f"\n✅ Fetched {len(items)} items total")
    
    if not items:
        print("\n⚠️ No items fetched. Check sources.")
        return
    
    # Statistics
    print("\n" + "=" * 80)
    print("📊 AGGREGATION STATISTICS")
    print("=" * 80)
    
    stats = agg.get_stats(items)
    print(f"\nTotal items: {stats['total_items']}")
    print(f"AI/ML items: {stats['ai_ml_count']}")
    print(f"Average relevance: {stats['avg_relevance']:.2f}")
    print(f"Average engagement: {stats['avg_engagement']:.2f}")
    
    print("\n📂 Categories:")
    for category, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {category.name}: {count}")
    
    print("\n📡 Sources:")
    for source, count in sorted(stats['sources'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {source}: {count}")
    
    # Top 10 stories
    print("\n" + "=" * 80)
    print("🔥 TOP 10 STORIES (by combined score)")
    print("=" * 80)
    
    top_items = agg.get_top_items(items, 10)
    
    for idx, item in enumerate(top_items, 1):
        score = item.relevance_score * 0.6 + item.engagement_score * 0.4
        print(f"\n{idx}. {item.title[:100]}")
        print(f"   Source: {item.source_name} ({item.source_type})")
        print(f"   Category: {item.category.name}")
        print(f"   Score: {score:.2f} (Relevance:{item.relevance_score:.2f} Engagement:{item.engagement_score:.2f})")
        print(f"   URL: {item.url[:80]}...")
    
    # AI/ML focused content
    print("\n" + "=" * 80)
    print("🤖 AI/ML FOCUSED CONTENT")
    print("=" * 80)
    
    ai_items = agg.get_ai_ml_items(items)
    print(f"\nFound {len(ai_items)} AI/ML items\n")
    
    for idx, item in enumerate(ai_items[:5], 1):
        print(f"{idx}. {item.title[:90]}")
        print(f"   Source: {item.source_name}")
        print(f"   Score: {item.relevance_score * 0.6 + item.engagement_score * 0.4:.2f}")
        print()
    
    # Category breakdown
    print("=" * 80)
    print("📂 CONTENT BY CATEGORY")
    print("=" * 80)
    
    by_category = agg.get_by_category(items)
    
    for category in [ContentCategory.AI_ML, ContentCategory.TECH_NEWS, ContentCategory.PROGRAMMING]:
        cat_items = by_category.get(category, [])
        if cat_items:
            print(f"\n{category.name} ({len(cat_items)} items):")
            for item in cat_items[:3]:
                print(f"   • {item.title[:70]}")
    
    # Test convenience methods
    print("\n" + "=" * 80)
    print("🎯 CONVENIENCE METHODS TEST")
    print("=" * 80)
    
    print("\n[A] Fetch top 5 stories...")
    top_5 = await agg.fetch_top_stories(5)
    print(f"   ✅ Got {len(top_5)} stories")
    
    print("\n[B] Fetch AI content only...")
    ai_only = await agg.fetch_ai_content()
    print(f"   ✅ Got {len(ai_only)} AI/ML items")
    
    print("\n" + "=" * 80)
    print("✅ CONTENT AGGREGATOR TEST COMPLETE")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  • {len(items)} items collected")
    print(f"  • {len(ai_items)} AI/ML items")
    print(f"  • {len(by_category)} categories")
    print(f"  • {len(stats['sources'])} sources active")


if __name__ == "__main__":
    asyncio.run(main())
