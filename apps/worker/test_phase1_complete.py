"""
Phase 1 Complete Test Suite

Tests all 5 working content sources from Phase 1.
"""

import asyncio
import logging
from datetime import datetime

from intel.hackernews_source import hackernews_source
from intel.twitter_trends_source import twitter_trends_source
from intel.reddit_source import reddit_source
from intel.substack_scraper import substack_scraper
from intel.polymarket_source import polymarket_source
from intel.rss_news_source import rss_news_source

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_all_sources():
    """Test all Phase 1 working sources"""
    
    print("\n" + "="*80)
    print("[TEST] PHASE 1 COMPLETE TEST - ALL WORKING SOURCES")
    print("="*80 + "\n")
    
    sources = [
        (hackernews_source, "Hacker News"),
        (twitter_trends_source, "Twitter/X Trends"),
        (reddit_source, "Reddit"),
        (substack_scraper, "Substack"),
        (polymarket_source, "Polymarket"),
        (rss_news_source, "RSS News"),
    ]
    
    results = {}
    total_items = 0
    
    for source, name in sources:
        print(f"\n{'='*80}")
        print(f"[TEST] Testing: {name}")
        print(f"{'='*80}\n")
        
        try:
            items = await source.fetch_latest()
            results[name] = {
                'status': '[OK] PASS',
                'count': len(items),
                'error': None
            }
            total_items += len(items)
            
            print(f"[OK] {name}: Fetched {len(items)} items")
            
            # Show sample
            if items:
                sample = items[0]
                print(f"   Sample: {sample.title[:60]}...")
                print(f"   Category: {sample.category.value}")
                print(f"   URL: {sample.url[:60]}...")
        
        except Exception as e:
            results[name] = {
                'status': '[ERROR] FAIL',
                'count': 0,
                'error': str(e)
            }
            print(f"[ERROR] {name}: Error - {e}")
    
    # Summary
    print("\n" + "="*80)
    print("[SUMMARY] PHASE 1 TEST SUMMARY")
    print("="*80 + "\n")
    
    passed = sum(1 for r in results.values() if '[OK]' in r['status'])
    total = len(sources)
    
    print(f"Sources Tested: {total}")
    print(f"Successful: {passed}/{total}")
    print(f"Total Items Fetched: {total_items}")
    print()
    
    print("Per-Source Results:")
    print("-" * 80)
    for name, result in results.items():
        print(f"{name:20s} {result['status']:15s} {result['count']:5d} items")
        if result['error']:
            print(f"  Error: {result['error']}")
    
    print("\n" + "="*80)
    
    if passed == total:
        print("[OK] ALL PHASE 1 SOURCES WORKING!")
    else:
        print(f"[WARN] {total - passed} source(s) failed")
    
    print("="*80 + "\n")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_all_sources())
