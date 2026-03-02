"""Sistem bütünlük testi - tüm kaynaklar ve Twitter API"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

results = {}

async def test_all():
    # 1. Gemini AI
    print("=== 1. AI (Gemini) ===")
    try:
        from ai_content_generator import AIContentGenerator
        ai = AIContentGenerator()
        post = await ai.generate_post("Python ve yapay zeka trendleri", style="professional")
        print(f"  OK -> {post[:120]}")
        results["ai_gemini"] = "OK"
    except Exception as e:
        print(f"  FAIL: {e}")
        results["ai_gemini"] = str(e)[:80]

    # 2. HackerNews
    print("\n=== 2. HackerNews ===")
    try:
        from intel.hackernews_source import HackerNewsSource
        hn = HackerNewsSource()
        items = await hn.fetch_latest()
        print(f"  OK -> {len(items)} haber")
        for i in items[:2]:
            print(f"    - {i.title[:70]}")
        results["hackernews"] = "OK"
    except Exception as e:
        print(f"  FAIL: {e}")
        results["hackernews"] = str(e)[:80]

    # 3. Google Trends
    print("\n=== 3. Google Trends ===")
    try:
        from intel.google_trends_source import GoogleTrendsSource
        gt = GoogleTrendsSource()
        items = await gt.fetch_latest()
        print(f"  OK -> {len(items)} trend")
        for i in items[:2]:
            print(f"    - {i.title[:70]}")
        results["google_trends"] = "OK"
    except Exception as e:
        print(f"  FAIL: {e}")
        results["google_trends"] = str(e)[:80]

    # 4. Reddit
    print("\n=== 4. Reddit ===")
    try:
        from intel.reddit_source import RedditSource
        rd = RedditSource()
        items = await rd.fetch_latest()
        print(f"  OK -> {len(items)} post")
        for i in items[:2]:
            print(f"    - {i.title[:70]}")
        results["reddit"] = "OK"
    except Exception as e:
        print(f"  FAIL: {e}")
        results["reddit"] = str(e)[:80]

    # 5. GitHub Trending
    print("\n=== 5. GitHub Trending ===")
    try:
        from intel.github_source import GitHubTrendingSource
        gh = GitHubTrendingSource()
        items = await gh.fetch_latest()
        print(f"  OK -> {len(items)} repo")
        for i in items[:2]:
            print(f"    - {i.title[:70]}")
        results["github"] = "OK"
    except Exception as e:
        print(f"  FAIL: {e}")
        results["github"] = str(e)[:80]

    # 6. ProductHunt
    print("\n=== 6. ProductHunt ===")
    try:
        from intel.producthunt_source import ProductHuntSource
        ph = ProductHuntSource()
        items = await ph.fetch_latest()
        print(f"  OK -> {len(items)} ürün")
        for i in items[:2]:
            print(f"    - {i.title[:70]}")
        results["producthunt"] = "OK"
    except Exception as e:
        print(f"  FAIL: {e}")
        results["producthunt"] = str(e)[:80]

    # 7. Twitter API bağlantısı (tweet atmadan)
    print("\n=== 7. Twitter API ===")
    try:
        import tweepy
        client = tweepy.Client(
            bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
            consumer_key=os.getenv("TWITTER_API_KEY"),
            consumer_secret=os.getenv("TWITTER_API_SECRET"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
        )
        me = client.get_me()
        print(f"  OK -> Kullanıcı: {me.data}")
        results["twitter_api"] = "OK"
    except Exception as e:
        print(f"  FAIL: {e}")
        results["twitter_api"] = str(e)[:80]

    # ÖZET
    print("\n" + "="*55)
    print("ÖZET:")
    ok = [k for k, v in results.items() if v == "OK"]
    fail = [k for k, v in results.items() if v != "OK"]
    for k in ok:
        print(f"  ✅ {k}")
    for k in fail:
        print(f"  ❌ {k}: {results[k]}")
    print(f"\nToplam: {len(ok)}/{len(results)} çalışıyor")

asyncio.run(test_all())
