"""Quick test with timeout - see what actually works"""

import asyncio
import logging

logging.basicConfig(level=logging.ERROR)

async def test_with_timeout(name, coro, timeout=10):
    """Test with timeout"""
    try:
        items = await asyncio.wait_for(coro, timeout=timeout)
        count = len(items) if items else 0
        if count > 0:
            print(f"✅ {name:20s} {count:3d} items")
            return True
        else:
            print(f"❌ {name:20s}   0 items")
            return False
    except asyncio.TimeoutError:
        print(f"⏱️  {name:20s} TIMEOUT ({timeout}s)")
        return False
    except Exception as e:
        print(f"❌ {name:20s} {str(e)[:40]}")
        return False

async def main():
    print("\n=== QUICK SOURCE TEST (10s timeout each) ===\n")
    
    working = 0
    
    # Fast API sources
    try:
        from intel.hackernews_source import hackernews_source
        if await test_with_timeout("Hacker News", hackernews_source.fetch_latest()): working += 1
    except: pass
    
    try:
        from intel.producthunt_source import producthunt_source
        if await test_with_timeout("Product Hunt", producthunt_source.fetch_latest()): working += 1
    except: pass
    
    try:
        from intel.huggingface_source import huggingface_source
        if await test_with_timeout("HuggingFace", huggingface_source.fetch_latest()): working += 1
    except: pass
    
    try:
        from intel.github_source import github_source
        if await test_with_timeout("GitHub", github_source.fetch_latest()): working += 1
    except: pass
    
    try:
        from intel.polymarket_source import polymarket_source
        if await test_with_timeout("Polymarket", polymarket_source.fetch_latest()): working += 1
    except: pass
    
    try:
        from intel.rss_news_source import rss_news_source
        if await test_with_timeout("RSS News", rss_news_source.fetch_latest()): working += 1
    except: pass
    
    try:
        from intel.substack_scraper import substack_scraper
        if await test_with_timeout("Substack", substack_scraper.fetch_latest()): working += 1
    except: pass
    
    print(f"\n=== RESULT: {working}/7 sources working ===\n")

if __name__ == "__main__":
    asyncio.run(main())
