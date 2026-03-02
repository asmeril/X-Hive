"""
Intel kaynaklarını hızlı test eder - HTTP üzerinden
"""
import asyncio
import sys
import io
import json

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import logging
logging.basicConfig(level=logging.WARNING)  # Sadece hataları göster

sys.path.insert(0, ".")


async def test_source(name, coro):
    try:
        items = await coro
        if items:
            print(f"  OK  {name}: {len(items)} oge")
            for i in items[:2]:
                title = getattr(i, "title", str(i))[:70]
                print(f"       - {title}")
        else:
            print(f"  !!  {name}: 0 oge geldi")
    except Exception as e:
        print(f"  XX  {name}: HATA - {e}")


async def main():
    print("\n=== INTEL KAYNAK TESTI ===\n")

    # HackerNews
    from intel.hackernews_source import HackerNewsSource
    hn = HackerNewsSource(limit=5)
    await test_source("HackerNews", hn.fetch_latest(limit=5))

    # GitHub
    from intel.github_source import GitHubTrendingSource
    gh = GitHubTrendingSource(language="python", max_repos=5)
    await test_source("GitHub Trending", gh.fetch_latest(limit=5))

    # ProductHunt
    from intel.producthunt_source import ProductHuntSource
    ph = ProductHuntSource(limit=5)
    await test_source("ProductHunt", ph.fetch_latest(limit=5))

    # Reddit
    from intel.reddit_source import RedditSource
    rd = RedditSource(limit=5)
    await test_source("Reddit", rd.fetch_latest(limit=5))

    # Google Trends
    from intel.google_trends_source import GoogleTrendsSource
    gt = GoogleTrendsSource()
    await test_source("Google Trends", gt.fetch_latest(limit=5))

    print("\n=== TAMAMLANDI ===\n")


if __name__ == "__main__":
    asyncio.run(main())
