"""
Test script for Twitter source.

Tests cookie-based scraping and Nitter fallback.
"""

import asyncio
import logging

from intel.twitter_source import twitter_source

logging.basicConfig(level=logging.INFO)


async def test_twitter_source():
    """Test Twitter source"""
    
    print("\n" + "="*80)
    print("[TWITTER] TESTING TWITTER SOURCE")
    print("="*80 + "\n")
    
    # Fetch tweets
    items = await twitter_source.fetch_latest()
    
    print(f"\n[OK] Fetched {len(items)} tweets\n")
    
    # Show samples
    print("[INFO] Sample tweets:\n")
    for i, item in enumerate(items[:5], 1):
        print(f"{i}. @{item.author}: {item.title}")
        print(f"   Category: {item.category.value}")
        print(f"   Engagement: {item.engagement_score:.2f}")
        print(f"   URL: {item.url}")
        print()


if __name__ == "__main__":
    asyncio.run(test_twitter_source())
