# PHASE 1: CONTENT SOURCES - IMPLEMENTATION GUIDE

## Overview

Implement 12 diverse content sources with balanced category distribution.

---

## 🍪 PREREQUISITE: Cookie Extraction

**Before implementing sources, extract authentication cookies:**

### Step 1: Install Playwright

```bash
cd apps/worker
pip install playwright
playwright install chromium
```

### Step 2: Run Cookie Extractor

```bash
python tools/cookie_extractor.py
```

### Step 3: Select Platforms

Recommended for Phase 1:

- ✅ Reddit (required)
- ✅ Twitter/X (critical - saves $150/mo)
- ⚠️ Medium (optional but useful)
- ⚠️ Substack (optional)

**Time required:** ~10-15 minutes

### Step 4: Verify Cookies

Check `.env` file contains:

```bash
REDDIT_COOKIE=...
TWITTER_COOKIE=...
TWITTER_CT0=...
MEDIUM_COOKIE=...
```

### Step 5: Test Cookies

```bash
python -c "
from intel.cookie_manager import get_cookie_manager
cm = get_cookie_manager()
print('Reddit:', '✅' if cm.validate_cookie('reddit') else '❌')
print('Twitter:', '✅' if cm.validate_cookie('twitter') else '❌')
"
```

**Expected output:**

```
✅ Cookies loaded: reddit, twitter
Reddit: ✅
Twitter: ✅
```

**Now proceed with Batch 1 implementation.**

---

## Source Implementation Checklist

### Batch 1: API-Based (Easy) ✅

#### Reddit (Cookie Scraping)
- [x] Create `reddit_source.py`
- [x] Configure 20 subreddits across categories
- [x] Implement cookie-based scraping
- [x] Test fetching
- [x] Auto-categorization working

**Status:** ✅ DONE

**Method:** BeautifulSoup scraping with cookie authentication

**Subreddits:**
```
AI/ML: r/MachineLearning, r/artificial, r/singularity, r/datascience
Tech: r/programming, r/Python, r/webdev, r/technology
Startup: r/startups, r/Entrepreneur
Crypto: r/CryptoCurrency, r/ethereum, r/Bitcoin
Gaming: r/gaming, r/gamedev
Mobile: r/AndroidApps, r/iOSProgramming
Security: r/cybersecurity, r/netsec
Science: r/science, r/Physics
```

#### Hacker News (Official API)
- [x] Create `hackernews_source.py`
- [x] Implement top/new/show stories
- [x] Auto-categorization logic
- [x] Test fetching

**Status:** ✅ DONE

**Features:**
- Fetches top, new, best, ask, show stories
- Async HTTP requests with aiohttp
- Intelligent categorization based on keywords
- Relevance/engagement scoring

#### ArXiv (Official API)
- [x] Create `arxiv_source.py`
- [x] Configure categories (cs.AI, cs.LG, cs.CV, cs.CL, etc.)
- [x] Test paper fetching

**Status:** ✅ DONE

**Categories Covered:**
```
cs.AI       → AI_ML
cs.LG       → AI_ML
cs.CV       → AI_ML
cs.CL       → AI_ML
cs.CR       → SECURITY_PRIVACY
cs.SE       → TECH_PROGRAMMING
physics     → SCIENCE
math        → SCIENCE
```

#### Product Hunt (Official API)
- [x] Create `producthunt_source.py`
- [x] Add API token to `.env`
- [x] Test product fetching

**Status:** ✅ DONE

**Features:**
- GraphQL API queries
- Topic-based categorization
- Vote count scoring
- Comment count engagement

#### Google Trends (pytrends)
- [x] Create `google_trends_source.py`
- [x] Configure geo (TR + Global)
- [x] Test trend fetching

**Status:** ✅ DONE

**Features:**
- Fetches trending searches by country
- Keyword-based categorization
- Decay scoring by position
- Default Turkey (TR) geo

---

### Batch 2: Twitter/X (Cookie + Nitter) 🐦

**NEW APPROACH:** Cookie-based scraping

#### Cookie Manager Integration
- [ ] Update `cookie_manager.py` with Twitter headers
- [ ] Test cookie authentication
- [ ] Validate cookies work

**Status:** 📋 PLANNED

#### Twitter Scraper (Cookie-based)
- [ ] Create `twitter_scraper.py`
- [ ] Implement cookie-based scraping
- [ ] Fallback to Nitter if cookies fail
- [ ] Integrate with influencer database (Phase 2)
- [ ] Test viral tweet fetching
- [ ] Test influencer timeline fetching
- [ ] Test trending topics

**Status:** 📋 PLANNED

**Features:**
- **Primary:** Cookie-based authenticated scraping
- **Fallback:** Nitter public instance
- Extract author, likes, retweets, replies
- Find influencers via viral tweets
- Categorize based on content
- Real-time trend discovery

**Cost Analysis:**
- **OLD:** Reading ($150/mo) + Posting ($2/mo) = $152/mo
- **NEW:** Reading ($0 - cookies) + Posting ($2/mo) = $2/mo
- **SAVINGS:** $150/month

**Implementation Notes:**
```python
# Cookie-based (primary)
headers = {
    'Cookie': f'auth_token={auth_token}; ct0={ct0}',
    'x-csrf-token': ct0,
    # ... other headers
}

# Nitter (fallback)
# Instances: nitter.net, nitter.1d4.us
# Fetch timeline/search results
# Extract top tweets by engagement
```

#### Twitter Poster (API)
- [x] Already exists: `posting/twitter_poster.py`
- [x] Verify pay-as-you-go works ($0.02/tweet)
- [x] Keep using official API for posting

**Status:** ✅ DONE

**Features:**
- tweepy integration
- OAuth1a authentication
- Post, delete, get tweet operations
- Error handling with retries

**Rationale:** Keep API for posting (reliable, cheap), use cookies for reading (free)

---

### Batch 3: Scraping (Medium) 🕷️

#### Substack (RSS Scraping)
- [ ] Create `substack_scraper.py`
- [ ] Identify top tech newsletters
- [ ] Parse RSS feeds
- [ ] Extract article metadata
- [ ] Test fetching

**Status:** 📋 PLANNED

**Top Newsletters to Track:**
```
- The Pragmatic Engineer
- ByteByteGo
- The AI Enthusiast
- Astral Codex Ten
- Lesswrong
```

**Implementation:**
```python
# Use feedparser for RSS
# Extract title, URL, author, published_at
# Auto-categorize based on content
# Handle pagination
```

#### Medium (Web Scraping)
- [ ] Create `medium_scraper.py`
- [ ] Scrape trending tech stories
- [ ] Extract article metadata
- [ ] Tag-based categorization
- [ ] Test fetching

**Status:** 📋 PLANNED

**Implementation:**
```python
# Use BeautifulSoup + Playwright
# Scrape trending/tech sections
# Extract title, author, clap count
# Handle paywall content gracefully
```

#### Perplexity Discover
- [ ] Create `perplexity_source.py`
- [ ] Scrape discover page
- [ ] Extract trending queries
- [ ] Auto-categorization
- [ ] Test fetching

**Status:** 📋 PLANNED

**Implementation:**
```python
# Scrape perplexity.ai/discover
# Extract trending topics
# Get reference articles
# Auto-categorize based on keywords
```

---

### Batch 4: Advanced (Complex) 🚀

#### YouTube
- [ ] Create `youtube_source.py`
- [ ] Configure channels list
- [ ] Add API key to `.env`
- [ ] Fetch video metadata
- [ ] Test video fetching

**Status:** 📋 PLANNED

**Top Channels:**
```
Tech/AI:
- 3Blue1Brown
- Yannic Kilcher
- Karpathy (Tesla AI)
- Andrej Karpathy

Programming:
- Fireship
- Tech with Tim
- Code Aesthetic

Startup:
- Y Combinator
- Paul Graham
```

**Implementation:**
```python
# Use google-api-client
# Fetch video metadata
# Extract description, view count, likes
# Categorize based on channel/title
```

#### Discord
- [ ] Create `discord_source.py`
- [ ] Create bot application
- [ ] Join target servers
- [ ] Fetch recent messages
- [ ] Test message fetching

**Status:** 📋 PLANNED

**Target Servers:**
```
- Artificial Intelligence / ML communities
- Programming communities
- Startup/Founder communities
- Crypto communities
```

**Implementation:**
```python
# Use discord.py
# Fetch messages from channels
# Extract author, content, reactions
# Categorize based on server/channel
```

#### GitHub Discussions (GraphQL API)
- [ ] Create `github_discussions.py`
- [ ] Implement GraphQL queries
- [ ] Add token to `.env`
- [ ] Fetch popular discussions
- [ ] Test discussion fetching

**Status:** 📋 PLANNED

**Implementation:**
```python
# Use GitHub GraphQL API
# Query trending discussions
# Filter by topic/category
# Extract title, body, reactions
```

---

## Testing Each Source

### Individual Source Testing

For each source, run:

```bash
python -m pytest tests/intel/test_reddit_source.py -v
python -m pytest tests/intel/test_hackernews_source.py -v
python -m pytest tests/intel/test_arxiv_source.py -v
python -m pytest tests/intel/test_producthunt_source.py -v
python -m pytest tests/intel/test_google_trends_source.py -v
# ... etc
```

### Expected Output:

```
✅ Fetched 50 items from Reddit
📊 Category distribution:
   AI_ML: 15 (30%)
   TECH_PROGRAMMING: 10 (20%)
   STARTUP_BUSINESS: 8 (16%)
   GAMING_ENTERTAINMENT: 6 (12%)
   CRYPTO_WEB3: 5 (10%)
   MOBILE_APPS: 3 (6%)
   SECURITY_PRIVACY: 2 (4%)
   SCIENCE: 1 (2%)

⭐ Average quality score: 0.75
⭐ Average engagement score: 0.68
🔗 Found 45 unique URLs
```

### Integration Testing

```bash
# Test full aggregation with all sources
python -m pytest tests/intel/test_aggregator.py -v

# Test category distribution
python -m pytest tests/intel/test_category_distribution.py -v

# Test deduplication
python -m pytest tests/intel/test_deduplication.py -v
```

---

## SUCCESS METRICS

### Cost Efficiency
- ✅ Target: <$5/month total cost
- **Current: $2/month** (Twitter API posting only)
- **Saved: $150/month** vs API-only approach
- **Status: ✅ ACHIEVED**

### Content Quality
- ⏳ 90% of generated tweets rated HIGH quality
- ⏳ Category distribution within ±5% of targets
- 📋 200+ active influencers in database

### Automation
- 📋 3 tweets posted daily automatically
- 📋 90% approval rate (10% rejection)
- ⏳ Zero manual source configuration after setup

### Cookie Stability
- 📋 Cookies last >30 days without refresh
- 📋 <5% cookie expiration rate per month
- 📋 Auto-detection of expired cookies

---

## Quality Assurance

### Per-Source Checklist

- [ ] **Credentials:** All API keys/cookies configured in `.env`
- [ ] **Rate Limiting:** Respects API rate limits
- [ ] **Error Handling:** Graceful failures, proper logging
- [ ] **Categorization:** Correct category assignment
- [ ] **Data Quality:** No malformed or incomplete items
- [ ] **Performance:** Fetches complete within 30 seconds
- [ ] **Deduplication:** No duplicate URLs
- [ ] **Freshness:** Only recent content (< 7 days old)
- [ ] **Cookie Management:** Handles expired cookies gracefully

### Category Distribution Test

After implementing all sources, verify:

```python
from intel.base_source import get_category_distribution, CATEGORY_TARGETS

items = aggregate_all_sources()
actual = get_category_distribution(items)
targets = CATEGORY_TARGETS

for category, target in targets.items():
    actual_pct = actual[category]
    difference = abs(actual_pct - target)
    
    if difference <= 0.05:
        print(f"✅ {category}: {actual_pct:.1%} (target: {target:.1%})")
    else:
        print(f"⚠️  {category}: {actual_pct:.1%} (target: {target:.1%}) - Adjust weights")
```

---

## Integration with Aggregator

After all sources implemented, update `aggregator.py`:

```python
from intel import (
    reddit_source,
    hackernews_source,
    arxiv_source,
    producthunt_source,
    google_trends_source,
    # ... other sources
)

class ContentAggregator:
    def __init__(self):
        self.sources = [
            reddit_source,
            hackernews_source,
            arxiv_source,
            producthunt_source,
            google_trends_source,
            # ... add all sources
        ]
    
    async def aggregate(self):
        """Fetch from all sources and aggregate"""
        all_items = []
        
        for source in self.sources:
            try:
                items = await source.fetch_latest()
                all_items.extend(items)
                logger.info(f"✅ {source.get_source_name()}: {len(items)} items")
            except Exception as e:
                logger.error(f"❌ {source.get_source_name()}: {e}")
        
        # Deduplicate
        all_items = deduplicate_by_url(all_items)
        
        # Verify category distribution
        dist = get_category_distribution(all_items)
        balance = get_category_balance_score(all_items)
        
        logger.info(f"📊 Category Balance Score: {balance:.2f}")
        
        return all_items
```

---

## Implementation Order

### Priority 1 (This Week): ✅
1. Reddit ✅
2. Hacker News ✅
3. ArXiv ✅
4. Product Hunt ✅
5. Google Trends ✅

### Priority 2 (Next Week): 📋
6. Twitter Scraper (Nitter)
7. Substack (RSS)
8. Medium (Scraping)
9. YouTube (API)

### Priority 3 (Future): 📋
10. Perplexity (Scraping)
11. Discord (Bot API)
12. GitHub (GraphQL)

---

## Progress Tracking

```
✅ = Implemented + Tested
⏳ = In Progress
📋 = Planned
❌ = Blocked/Cancelled
```

Current: **5/12 sources implemented (42%)**

---

## Next Phase

After Phase 1 completion → **PHASE 2: DYNAMIC INFLUENCER SYSTEM**

See: [docs/PHASE2-INFLUENCERS.md] (coming soon)
