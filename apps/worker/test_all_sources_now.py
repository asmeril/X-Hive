"""Test ALL sources RIGHT NOW - no assumptions"""

import asyncio
import logging
import sys
from datetime import datetime

# Silence logs
logging.basicConfig(level=logging.ERROR)

async def test_source(name, fetch_func):
    """Test a single source"""
    try:
        start = datetime.now()
        items = await fetch_func()
        elapsed = (datetime.now() - start).total_seconds()
        
        if items and len(items) > 0:
            print(f"✅ {name:25s} {len(items):3d} items ({elapsed:.1f}s)")
            return True, len(items)
        else:
            print(f"❌ {name:25s}   0 items ({elapsed:.1f}s)")
            return False, 0
    except Exception as e:
        print(f"❌ {name:25s} ERROR: {str(e)[:50]}")
        return False, 0

async def main():
    print("\n" + "="*70)
    print("TESTING ALL SOURCES - RIGHT NOW")
    print("="*70 + "\n")
    
    results = []
    
    # Test each source
    try:
        from intel.hackernews_source import hackernews_source
        result = await test_source("Hacker News", hackernews_source.fetch_latest)
        results.append(result)
    except Exception as e:
        print(f"❌ Hacker News           IMPORT ERROR: {e}")
        results.append((False, 0))
    
    try:
        from intel.arxiv_source import arxiv_source
        result = await test_source("ArXiv", arxiv_source.fetch_latest)
        results.append(result)
    except Exception as e:
        print(f"❌ ArXiv                 IMPORT ERROR: {e}")
        results.append((False, 0))
    
    try:
        from intel.producthunt_source import producthunt_source
        result = await test_source("Product Hunt", producthunt_source.fetch_latest)
        results.append(result)
    except Exception as e:
        print(f"❌ Product Hunt          IMPORT ERROR: {e}")
        results.append((False, 0))
    
    try:
        from intel.substack_scraper import substack_scraper
        result = await test_source("Substack", substack_scraper.fetch_latest)
        results.append(result)
    except Exception as e:
        print(f"❌ Substack              IMPORT ERROR: {e}")
        results.append((False, 0))
    
    try:
        from intel.huggingface_source import huggingface_source
        result = await test_source("HuggingFace", huggingface_source.fetch_latest)
        results.append(result)
    except Exception as e:
        print(f"❌ HuggingFace           IMPORT ERROR: {e}")
        results.append((False, 0))
    
    try:
        from intel.github_source import github_source
        result = await test_source("GitHub Trending", github_source.fetch_latest)
        results.append(result)
    except Exception as e:
        print(f"❌ GitHub Trending       IMPORT ERROR: {e}")
        results.append((False, 0))
    
    try:
        from intel.twitter_trends_source import twitter_trends_source
        result = await test_source("Twitter Trends", twitter_trends_source.fetch_latest)
        results.append(result)
    except Exception as e:
        print(f"❌ Twitter Trends        IMPORT ERROR: {e}")
        results.append((False, 0))
    
    try:
        from intel.reddit_source import reddit_source
        result = await test_source("Reddit", reddit_source.fetch_latest)
        results.append(result)
    except Exception as e:
        print(f"❌ Reddit                IMPORT ERROR: {e}")
        results.append((False, 0))
    
    try:
        from intel.polymarket_source import polymarket_source
        result = await test_source("Polymarket", polymarket_source.fetch_latest)
        results.append(result)
    except Exception as e:
        print(f"❌ Polymarket            IMPORT ERROR: {e}")
        results.append((False, 0))
    
    try:
        from intel.rss_news_source import rss_news_source
        result = await test_source("RSS News", rss_news_source.fetch_latest)
        results.append(result)
    except Exception as e:
        print(f"❌ RSS News              IMPORT ERROR: {e}")
        results.append((False, 0))
    
    # Summary
    print("\n" + "="*70)
    working = sum(1 for success, _ in results if success)
    total_items = sum(count for _, count in results)
    print(f"SUMMARY: {working}/{len(results)} sources working, {total_items} total items")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
