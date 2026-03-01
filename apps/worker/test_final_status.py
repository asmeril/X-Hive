"""Final source status - all tested now"""

import asyncio
import logging

logging.basicConfig(level=logging.ERROR)

async def quick_test(name, fetch_coro):
    try:
        items = await asyncio.wait_for(fetch_coro, timeout=40)
        print(f"✅ {name:25s} {len(items):3d} items")
        return len(items)
    except asyncio.TimeoutError:
        print(f"⏱️  {name:25s} TIMEOUT")
        return 0
    except Exception as e:
        print(f"❌ {name:25s} ERROR: {str(e)[:40]}")
        return 0

async def main():
    print("\n" + "="*60)
    print("X-HIVE SOURCE STATUS - ALL SOURCES TESTED")
    print("="*60 + "\n")
    
    total = 0
    
    from intel.hackernews_source import hackernews_source
    total += await quick_test("Hacker News", hackernews_source.fetch_latest())
    
    from intel.arxiv_source import arxiv_source
    total += await quick_test("ArXiv", arxiv_source.fetch_latest())
    
    from intel.producthunt_source import producthunt_source
    total += await quick_test("Product Hunt", producthunt_source.fetch_latest())
    
    from intel.huggingface_source import huggingface_source
    total += await quick_test("HuggingFace", huggingface_source.fetch_latest())
    
    from intel.github_source import github_source
    total += await quick_test("GitHub Trending", github_source.fetch_latest())
    
    from intel.polymarket_source import polymarket_source
    total += await quick_test("Polymarket (NEW)", polymarket_source.fetch_latest())
    
    from intel.rss_news_source import rss_news_source
    total += await quick_test("RSS News (NEW)", rss_news_source.fetch_latest())
    
    from intel.substack_scraper import substack_scraper
    total += await quick_test("Substack", substack_scraper.fetch_latest())
    
    from intel.twitter_trends_source import twitter_trends_source
    total += await quick_test("Twitter Trends", twitter_trends_source.fetch_latest())
    
    print("\n" + "="*60)
    print(f"TOTAL: {total} items from 9 sources")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
