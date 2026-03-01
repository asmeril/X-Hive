"""Simple sequential test - no timeouts"""

import asyncio
import logging

logging.basicConfig(level=logging.WARNING)

async def test(name, source):
    try:
        print(f"Testing {name}...", end=" ", flush=True)
        items = await source.fetch_latest()
        print(f"✅ {len(items):3d} items")
        return len(items)
    except Exception as e:
        print(f"❌ ERROR: {str(e)[:50]}")
        return 0

async def main():
    print("\n" + "="*60)
    print("X-HIVE SOURCES - SIMPLE TEST")
    print("="*60 + "\n")
    
    total = 0
    
    from intel.hackernews_source import hackernews_source
    total += await test("Hacker News", hackernews_source)
    
    from intel.producthunt_source import producthunt_source
    total += await test("Product Hunt", producthunt_source)
    
    from intel.huggingface_source import huggingface_source
    total += await test("HuggingFace", huggingface_source)
    
    from intel.github_source import github_source
    total += await test("GitHub", github_source)
    
    from intel.polymarket_source import polymarket_source
    total += await test("Polymarket", polymarket_source)
    
    from intel.rss_news_source import rss_news_source
    total += await test("RSS News", rss_news_source)
    
    from intel.substack_scraper import substack_scraper
    total += await test("Substack", substack_scraper)
    
    print("\n--- ArXiv (slow, ~5s) ---")
    from intel.arxiv_source import arxiv_source
    total += await test("ArXiv", arxiv_source)
    
    print("\n--- Twitter Trends (very slow, ~30s) ---")
    from intel.twitter_trends_source import twitter_trends_source
    total += await test("Twitter Trends", twitter_trends_source)
    
    print("\n" + "="*60)
    print(f"TOTAL: {total} items from 9 sources")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
