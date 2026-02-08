"""
Test script for Reddit source with JWT authentication
"""

import asyncio
import logging

from intel.reddit_source import reddit_source

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


async def test_reddit():
    """Test Reddit source with JWT auth"""
    
    print("\n" + "="*80)
    print("[REDDIT] TESTING REDDIT SOURCE")
    print("="*80 + "\n")
    
    try:
        items = await reddit_source.fetch_latest()
        
        print(f"\n[OK] Fetched {len(items)} posts from Reddit\n")
        
        if items:
            print("[INFO] Sample posts:\n")
            for i, item in enumerate(items[:5], 1):
                print(f"{i}. r/{item.source_name.split('- r/')[-1]}: {item.title[:60]}...")
                print(f"   Score: {item.engagement_score:.2f} | Category: {item.category.value}")
                print(f"   URL: {item.url}")
                print()
        else:
            print("[WARN] No posts fetched. Check logs for errors.")
    
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_reddit())
