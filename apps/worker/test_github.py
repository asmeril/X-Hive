#!/usr/bin/env python3
"""
Test GitHub Trending Source
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
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from intel.github_source import github_trending_source, github_ai_source
from collections import Counter


async def main():
    """Test GitHub Trending scraper"""
    
    print("=" * 80)
    print("🧪 GITHUB TRENDING SOURCE TEST")
    print("=" * 80)
    
    # Test 1: General trending repos
    print("\n[TEST 1] GitHub Trending - Daily (All AI Languages)")
    print("-" * 80)
    
    items = await github_trending_source.fetch_latest()
    
    print(f"\n✅ Fetched {len(items)} trending repositories\n")
    
    if items:
        print("📊 Top 5 Trending Repos:")
        print("-" * 80)
        
        for idx, item in enumerate(items[:5], 1):
            print(f"\n{idx}. {item.title[:100]}")
            print(f"   URL: {item.url}")
            print(f"   Category: {item.category.name}")
            print(f"   Language: {item.metadata.get('language', 'N/A')}")
            print(f"   ⭐ Today: {item.metadata.get('stars_today', 0):,}")
            print(f"   ⭐ Total: {item.metadata.get('total_stars', 0):,}")
            print(f"   🍴 Forks: {item.metadata.get('forks', 0):,}")
            print(f"   📊 Relevance: {item.relevance_score:.2f}")
            print(f"   💬 Engagement: {item.engagement_score:.2f}")
        
        # Category breakdown
        print("\n" + "=" * 80)
        print("📊 CATEGORY BREAKDOWN")
        print("=" * 80)
        
        categories = Counter(item.category for item in items)
        for category, count in categories.most_common():
            print(f"   {category.name}: {count}")
        
        # Language breakdown
        print("\n" + "=" * 80)
        print("📊 LANGUAGE BREAKDOWN")
        print("=" * 80)
        
        languages = Counter(item.metadata.get('language', 'Unknown') for item in items)
        for lang, count in languages.most_common(10):
            print(f"   {lang}: {count}")
    
    # Test 2: Python AI repos
    print("\n" + "=" * 80)
    print("[TEST 2] GitHub Trending - Python (Weekly)")
    print("=" * 80)
    
    ai_items = await github_ai_source.fetch_latest()
    
    print(f"\n✅ Fetched {len(ai_items)} Python repositories\n")
    
    if ai_items:
        print("🐍 Top Python Repos:")
        print("-" * 80)
        
        for idx, item in enumerate(ai_items[:3], 1):
            print(f"\n{idx}. {item.metadata.get('repo_name', 'N/A')}")
            print(f"   {item.description[:150]}...")
            print(f"   ⭐ {item.metadata.get('total_stars', 0):,} stars")
            print(f"   Category: {item.category.name}")
    
    # Statistics
    print("\n" + "=" * 80)
    print("📈 SOURCE STATISTICS")
    print("=" * 80)
    
    stats = github_trending_source.get_stats()
    print(f"   Total fetches: {stats['fetch_count']}")
    print(f"   Errors: {stats['error_count']}")
    print(f"   Last fetch: {stats['last_fetch']}")
    
    # Health check
    print("\n[3] Running health check...")
    is_healthy = await github_trending_source.health_check()
    print(f"   GitHub Trending accessible: {'✅ Yes' if is_healthy else '❌ No'}")
    
    print("\n" + "=" * 80)
    print("✅ GITHUB TRENDING TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
