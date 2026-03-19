#!/usr/bin/env python3
"""
Intel Source Isolation Test
Tests each intel source individually to find which one is crashing the backend.
"""

import asyncio
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_github():
    """Test GitHub source"""
    print("\n" + "="*60)
    print("Testing: GitHub Trending")
    print("="*60)
    try:
        from intel.github_source import GitHubTrendingSource
        github = GitHubTrendingSource(language="python", max_repos=3)
        start = datetime.now()
        items = await asyncio.wait_for(github.fetch_latest(), timeout=30.0)
        elapsed = (datetime.now() - start).total_seconds()
        print(f"✅ GitHub: {len(items)} items in {elapsed:.1f}s")
        return True
    except asyncio.TimeoutError:
        print("❌ GitHub: TIMEOUT after 30s")
        return False
    except Exception as e:
        print(f"❌ GitHub: ERROR - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_google_trends():
    """Test Google Trends source"""
    print("\n" + "="*60)
    print("Testing: Google Trends")
    print("="*60)
    try:
        from intel.google_trends_source import GoogleTrendsSource
        trends = GoogleTrendsSource()
        start = datetime.now()
        items = await asyncio.wait_for(trends.fetch_latest(), timeout=30.0)
        elapsed = (datetime.now() - start).total_seconds()
        print(f"✅ Google Trends: {len(items)} items in {elapsed:.1f}s")
        return True
    except asyncio.TimeoutError:
        print("❌ Google Trends: TIMEOUT after 30s")
        return False
    except Exception as e:
        print(f"❌ Google Trends: ERROR - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_hackernews():
    """Test HackerNews source"""
    print("\n" + "="*60)
    print("Testing: HackerNews")
    print("="*60)
    try:
        from intel.hackernews_source import HackerNewsSource
        hn = HackerNewsSource(limit=3)
        start = datetime.now()
        items = await asyncio.wait_for(hn.fetch_latest(), timeout=20.0)
        elapsed = (datetime.now() - start).total_seconds()
        print(f"✅ HackerNews: {len(items)} items in {elapsed:.1f}s")
        return True
    except asyncio.TimeoutError:
        print("❌ HackerNews: TIMEOUT after 20s")
        return False
    except Exception as e:
        print(f"❌ HackerNews: ERROR - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_reddit():
    """Test Reddit source"""
    print("\n" + "="*60)
    print("Testing: Reddit")
    print("="*60)
    try:
        from intel.reddit_source import RedditSource
        reddit = RedditSource(limit=5)
        start = datetime.now()
        items = await asyncio.wait_for(reddit.fetch_latest(), timeout=45.0)
        elapsed = (datetime.now() - start).total_seconds()
        print(f"✅ Reddit: {len(items)} items in {elapsed:.1f}s")
        return True
    except asyncio.TimeoutError:
        print("❌ Reddit: TIMEOUT after 45s")
        return False
    except Exception as e:
        print(f"❌ Reddit: ERROR - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_producthunt():
    """Test ProductHunt source"""
    print("\n" + "="*60)
    print("Testing: ProductHunt")
    print("="*60)
    try:
        from intel.producthunt_source import ProductHuntSource
        ph = ProductHuntSource(limit=10)
        start = datetime.now()
        items = await asyncio.wait_for(ph.fetch_latest(), timeout=20.0)
        elapsed = (datetime.now() - start).total_seconds()
        print(f"✅ ProductHunt: {len(items)} items in {elapsed:.1f}s")
        return True
    except asyncio.TimeoutError:
        print("❌ ProductHunt: TIMEOUT after 20s")
        return False
    except Exception as e:
        print(f"❌ ProductHunt: ERROR - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_substack():
    """Test Substack source"""
    print("\n" + "="*60)
    print("Testing: Substack")
    print("="*60)
    try:
        from intel.substack_scraper import SubstackScraper
        sub = SubstackScraper()
        start = datetime.now()
        items = await asyncio.wait_for(sub.fetch_latest(), timeout=15.0)
        elapsed = (datetime.now() - start).total_seconds()
        print(f"✅ Substack: {len(items)} items in {elapsed:.1f}s")
        return True
    except asyncio.TimeoutError:
        print("❌ Substack: TIMEOUT after 15s")
        return False
    except Exception as e:
        print(f"❌ Substack: ERROR - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_telegram():
    """Test Telegram source"""
    print("\n" + "="*60)
    print("Testing: Telegram")
    print("="*60)
    try:
        from intel.telegram_source import TelegramChannelSource
        tg = TelegramChannelSource()
        start = datetime.now()
        items = await asyncio.wait_for(tg.fetch_latest(limit=5), timeout=30.0)
        elapsed = (datetime.now() - start).total_seconds()
        print(f"✅ Telegram: {len(items)} items in {elapsed:.1f}s")
        return True
    except asyncio.TimeoutError:
        print("❌ Telegram: TIMEOUT after 30s")
        return False
    except Exception as e:
        print(f"❌ Telegram: ERROR - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ai_generation():
    """Test AI content generation"""
    print("\n" + "="*60)
    print("Testing: AI Content Generation")
    print("="*60)
    try:
        from ai_content_generator import AIContentGenerator
        from approval.approval_queue import ContentItem
        
        ai = AIContentGenerator()
        
        # Create test content item
        test_item = ContentItem(
            title="Test: AI Can Now Generate Better Code",
            url="https://example.com/test",
            source="test_source",
            description="A test article about AI code generation"
        )
        
        start = datetime.now()
        tweet = await asyncio.wait_for(
            ai.generate_tweet_from_content(test_item),
            timeout=30.0
        )
        elapsed = (datetime.now() - start).total_seconds()
        print(f"✅ AI Generation: Tweet generated in {elapsed:.1f}s")
        print(f"   Tweet: {tweet[:80]}...")
        return True
    except asyncio.TimeoutError:
        print("❌ AI Generation: TIMEOUT after 30s")
        return False
    except Exception as e:
        print(f"❌ AI Generation: ERROR - {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("X-HIVE INTEL SOURCE ISOLATION TEST")
    print("="*60)
    
    results = {}
    
    # Test each source
    tests = [
        ("GitHub", test_github),
        ("Google Trends", test_google_trends),
        ("HackerNews", test_hackernews),
        ("Reddit", test_reddit),
        ("ProductHunt", test_producthunt),
        ("Substack", test_substack),
        ("Telegram", test_telegram),
        ("AI Generation", test_ai_generation),
    ]
    
    for name, test_func in tests:
        try:
            result = await test_func()
            results[name] = "✅ PASS" if result else "❌ FAIL"
        except Exception as e:
            results[name] = f"❌ ERROR: {e}"
            print(f"⚠️ Test wrapper caught exception: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, result in results.items():
        print(f"{name:20} {result}")
    
    passed = sum(1 for r in results.values() if "PASS" in r)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")


if __name__ == "__main__":
    asyncio.run(main())
