# Batch 1 Sources Test Guide

## Overview

Comprehensive test suite for X-Hive Phase 1 Batch 1 API-based content sources.

**Sources Tested:**
1. Reddit (PRAW API) - 20 subreddits
2. Hacker News (Official API) - Top/new/best stories
3. ArXiv (Research API) - AI/ML/Science papers
4. Product Hunt (GraphQL API) - Daily products
5. Google Trends (pytrends) - Trending searches

## Quick Start

### Run All Tests

```bash
cd apps/worker
python test_batch1_sources.py
```

### Expected Output

```
✅ BATCH 1: ALL TESTS PASSED!
- All 5 sources working
- Total items fetched: ~150+
- Category distribution balanced
- Quality metrics above threshold
```

## Test Components

### 1. Source Fetching
- Tests each source's `fetch_latest()` method
- Measures execution time
- Validates item count

### 2. Category Distribution
- Analyzes category breakdown per source
- Compares to target distribution
- Shows visual bar charts

### 3. Quality Metrics
- Average relevance score (0.0-1.0)
- Average engagement score (0.0-1.0)
- Min/max ranges

### 4. Data Validation
- Checks required fields (title, url, category)
- Validates URLs (http/https)
- Verifies category validity

### 5. Summary Report
- Per-source results table
- Overall category distribution
- Target vs actual comparison
- Distribution balance assessment

## Success Criteria

### All Tests Pass When:
✅ All 5 sources successfully fetch data  
✅ Total items >= 100  
✅ Average relevance score >= 0.6  
✅ Average engagement score >= 0.4  
✅ All categories have valid values  
✅ All URLs are properly formatted  
✅ Category distribution within ±15% of targets  

### Warning Status When:
⚠️ 3-4 sources working  
⚠️ Some categories off by 10-15%  
⚠️ Scores slightly below optimal  

### Failure Status When:
❌ 2 or fewer sources working  
❌ Total items < 50  
❌ Data validation errors  

## Troubleshooting

### Reddit Source Fails
**Error:** `ValueError: Reddit credentials not found`

**Solution:**
```bash
# Set in .env:
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=X-Hive/1.0

# Get credentials from: https://www.reddit.com/prefs/apps
```

### Product Hunt Fails
**Error:** `ValueError: Product Hunt API token not found`

**Solution:**
```bash
# Set in .env (optional, can work without):
PRODUCTHUNT_API_TOKEN=your_token

# Or remove the source temporarily
```

### Google Trends Fails
**Error:** `pytrends` data unavailable

**Solution:**
```bash
# This is usually temporary (rate limiting)
# Retry in a few minutes
# Google Trends is optional for Phase 1
```

### ArXiv Rate Limited
**Error:** `ConnectionError: Rate limit exceeded`

**Solution:**
```bash
# Reduce max_results or add delay between requests
# Temporarily skip if testing other sources
```

### Hacker News Slow
**Error:** Takes longer than 5 seconds

**Solution:**
```bash
# This is normal (fetches 30 items + details)
# Network dependent - try again
```

## Output Interpretation

### Test Results Table
```
Reddit               ✅ PASS  45 items  0.68      0.72      2.1s
Hacker News         ✅ PASS  30 items  0.72      0.65      3.2s
ArXiv               ✅ PASS  25 items  0.80      0.60      4.1s
Product Hunt        ✅ PASS  20 items  0.75      0.68      1.9s
Google Trends       ✅ PASS  20 items  0.70      0.70      2.0s
```

### Category Distribution
```
ai_ml              : 45 (27.0%)     █████░░░░
tech_programming   : 32 (19.3%)     ████░░░░░
startup_business   : 27 (16.3%)     ███░░░░░░
... (etc)
```

### Target vs Actual
```
ai_ml                : Target 30.0%   | Actual 27.0%   | Diff  -3.0% ✅
tech_programming     : Target 20.0%   | Actual 19.3%   | Diff  -0.7% ✅
startup_business     : Target 15.0%   | Actual 16.3%   | Diff  +1.3% ✅
```

## Advanced Usage

### Run Single Source Test
```python
import asyncio
from intel.reddit_source import reddit_source

async def test():
    items = await reddit_source.fetch_latest()
    print(f"Fetched {len(items)} items")

asyncio.run(test())
```

### Debug Logging
```bash
# Enable DEBUG logging
LOG_LEVEL=DEBUG python test_batch1_sources.py
```

### Test with Custom Limits
```bash
# Modify fetch limits in source files
# e.g., reddit_source.limit = 5  # Faster testing
```

## Performance Benchmarks

### Expected Times
- Redis: 1-2 seconds (20 subreddits)
- Hacker News: 2-3 seconds (30 stories)
- ArXiv: 3-5 seconds (8 categories)
- Product Hunt: 1-2 seconds (20 products)
- Google Trends: 1-2 seconds (20 trends)

**Total Time:** ~8-14 seconds

### Optimization Tips
- Run tests during low-traffic hours
- Increase request timeouts if network slow
- Consider parallel source fetching
- Cache results between test runs

## Integration Testing

### Test with Aggregator
```python
from intel.aggregator import ContentAggregator

async def test():
    agg = ContentAggregator([
        reddit_source,
        hackernews_source,
        arxiv_source,
        producthunt_source,
        google_trends_source,
    ])
    
    items = await agg.aggregate()
    print(f"Aggregated {len(items)} unique items")
```

### Test with Category Balancer
```python
from intel.base_source import get_category_distribution, get_category_balance_score

async def test():
    items = await fetch_all()
    dist = get_category_distribution(items)
    balance = get_category_balance_score(items)
    
    print(f"Balance Score: {balance:.2f}/1.0")
```

## Exit Codes

```
0   ✅ All tests passed
1   ⚠️  Some sources failed (action required)
2   ❌ Critical failure (review all sources)
130 ⚠️  Interrupted by user (Ctrl+C)
```

## Next Phase

After Batch 1 validation:
- **Batch 2:** Twitter/X Hybrid Sources
- **Batch 3:** Web Scraping Sources
- **Batch 4:** Advanced API Sources

## Support

For issues:
1. Review error messages in test output
2. Check `.env` file for missing credentials
3. Verify internet connectivity
4. Review source implementation files
5. Check `docs/PHASE1-SOURCES.md` for details

---

**Created:** 2026-02-07  
**Status:** Ready for testing  
**Maintained by:** X-Hive Development Team
