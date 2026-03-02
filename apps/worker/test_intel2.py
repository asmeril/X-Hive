"""
Minimal intel kaynak testi - sadece gerekli modülleri yükler
"""
import asyncio, sys, io, os
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Tüm logları kapat
import logging
logging.disable(logging.CRITICAL)

sys.path.insert(0, ".")

results = {}

async def main():
    # --- HackerNews ---
    try:
        from intel.hackernews_source import HackerNewsSource
        hn = HackerNewsSource(limit=5)
        items = await hn.fetch_latest()
        results["HackerNews"] = (True, len(items), [i.title[:60] for i in items[:2]])
    except Exception as e:
        results["HackerNews"] = (False, 0, str(e))

    # --- GitHub ---
    try:
        from intel.github_source import GitHubTrendingSource
        gh = GitHubTrendingSource(language="python", max_repos=5)
        items = await gh.fetch_latest()
        results["GitHub"] = (True, len(items), [i.title[:60] for i in items[:2]])
    except Exception as e:
        results["GitHub"] = (False, 0, str(e))

    # --- ProductHunt ---
    try:
        from intel.producthunt_source import ProductHuntSource
        ph = ProductHuntSource(limit=5)
        items = await ph.fetch_latest()
        results["ProductHunt"] = (True, len(items), [i.title[:60] for i in items[:2]])
    except Exception as e:
        results["ProductHunt"] = (False, 0, str(e))

    # --- Reddit ---
    try:
        from intel.reddit_source import RedditSource
        rd = RedditSource(limit=3, use_playwright_fallback=False)
        items = await asyncio.wait_for(rd.fetch_latest(), timeout=20)
        results["Reddit"] = (True, len(items), [i.title[:60] for i in items[:2]])
    except asyncio.TimeoutError:
        results["Reddit"] = (False, 0, "TIMEOUT (20s)")
    except Exception as e:
        results["Reddit"] = (False, 0, str(e)[:100])

    # --- Google Trends ---
    try:
        from intel.google_trends_source import GoogleTrendsSource
        gt = GoogleTrendsSource()
        items = await asyncio.wait_for(gt.fetch_latest(), timeout=15)
        results["GoogleTrends"] = (True, len(items), [i.title[:60] for i in items[:2]])
    except asyncio.TimeoutError:
        results["GoogleTrends"] = (False, 0, "TIMEOUT (15s)")
    except Exception as e:
        results["GoogleTrends"] = (False, 0, str(e)[:100])

asyncio.run(main())

print("\n" + "="*50)
print("  INTEL KAYNAK TEST SONUCLARI")
print("="*50)
for name, (ok, count, info) in results.items():
    status = "OK " if ok else "XX "
    if ok:
        print(f"  {status} {name}: {count} oge")
        for t in info:
            print(f"        - {t}")
    else:
        print(f"  {status} {name}: HATA - {info}")
print("="*50)
