#!/usr/bin/env python3
"""
Full Telegram Source Test - Fetch Real Messages
Tests message fetching from configured channels
"""

import asyncio
import sys
import os
from datetime import datetime
import logging

# Enable DEBUG logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from intel.telegram_source import telegram_source


async def main():
    """Test Telegram message fetching"""
    
    print("=" * 80)
    print("🧪 TELEGRAM MESSAGE FETCH TEST")
    print("=" * 80)
    
    if not telegram_source:
        print("❌ Telegram source not available")
        return
    
    try:
        # Initialize connection
        print("\n[1] Initializing Telegram connection...")
        await telegram_source.initialize()
        print("✅ Connected to Telegram")
        
        # Fetch latest messages (increase lookback to 7 days)
        print("\n[2] Fetching latest messages from channels (last 7 days)...")
        telegram_source.hours_lookback = 24 * 7  # 7 days
        items = await telegram_source.fetch_latest(limit=30)
        
        print(f"\n✅ Fetched {len(items)} messages")
        
        if items:
            print("\n" + "=" * 80)
            print("📨 SAMPLE MESSAGES (First 5)")
            print("=" * 80)
            
            for idx, item in enumerate(items[:5], 1):
                print(f"\n[{idx}] {item.title[:80]}")
                print(f"    Source: {item.source}")
                print(f"    Category: {item.category.name}")
                print(f"    Quality: {item.quality.name}")
                print(f"    URL: {item.url or 'N/A'}")
                print(f"    Published: {item.published_at}")
                print(f"    Relevance: {item.relevance_score:.2f}")
                print(f"    Engagement: {item.engagement_score:.2f}")
                if item.tags:
                    print(f"    Tags: {', '.join(item.tags[:5])}")
            
            # Category breakdown
            print("\n" + "=" * 80)
            print("📊 CATEGORY BREAKDOWN")
            print("=" * 80)
            
            from collections import Counter
            categories = Counter(item.category for item in items)
            for category, count in categories.most_common():
                print(f"   {category.name}: {count}")
            
            # Quality breakdown
            print("\n" + "=" * 80)
            print("📊 QUALITY BREAKDOWN")
            print("=" * 80)
            
            qualities = Counter(item.quality for item in items)
            for quality, count in qualities.most_common():
                print(f"   {quality.name}: {count}")
            
            # Source breakdown
            print("\n" + "=" * 80)
            print("📊 SOURCE BREAKDOWN")
            print("=" * 80)
            
            sources = Counter(item.source for item in items)
            for source, count in sources.most_common():
                print(f"   {source}: {count}")
        
        # Statistics
        print("\n" + "=" * 80)
        print("📈 STATISTICS")
        print("=" * 80)
        
        stats = telegram_source.get_stats()
        print(f"   Total fetches: {stats['fetch_count']}")
        print(f"   Errors: {stats['error_count']}")
        print(f"   Last fetch: {stats['last_fetch']}")
        print(f"   Last error: {stats.get('last_error') or 'None'}")
        
        # Cleanup
        print("\n[3] Disconnecting...")
        await telegram_source.disconnect()
        
        print("\n" + "=" * 80)
        print("✅ TELEGRAM FETCH TEST COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
