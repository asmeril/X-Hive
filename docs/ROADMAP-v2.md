# X-HIVE v2.0 ROADMAP

## Mission
Autonomous Twitter content engine with:
- 12 diverse content sources
- 8 content categories
- Dynamic influencer discovery
- AI-powered Turkish tweet generation
- Desktop approval interface

## Overall Progress

```
Phase 1: Content Sources        [████████░░] 80% (In Progress)
Phase 2: Influencer System      [██░░░░░░░░] 20% (Planning)
Phase 3: Category Distribution  [█░░░░░░░░░] 10% (Planning)
Phase 4: Desktop App            [░░░░░░░░░░] 0% (Not Started)
```

---

## COOKIE AUTHENTICATION STRATEGY 🍪

**Decision:** Use cookie-based authentication instead of APIs where possible

### Why Cookies?

**Cost Savings:**
- Twitter API (reading): $150/month → **$0 with cookies**
- Reddit API: Restricted/slow approval → **Instant with cookies**
- Medium: Paywall → **Bypass with cookies**

**Total Savings: ~$150/month = $1,800/year**

### Cookie Management

#### 1. Auto Cookie Extractor Tool

**Tool:** `apps/worker/tools/cookie_extractor.py`

**Features:**
- Interactive browser sessions (Playwright)
- User logs in manually (secure)
- Cookies extracted automatically
- Saved to .env automatically
- Supports 8 platforms simultaneously

**Time Required:** ~15 minutes for all platforms

#### 2. Cookie Manager Module

**Module:** `apps/worker/intel/cookie_manager.py`

**Features:**
- Centralized cookie storage
- Platform-specific headers
- Cookie validation
- Easy integration with sources

#### 3. Supported Platforms

| Platform | Cookie Name | Status | Priority | Benefit |
|----------|-------------|--------|----------|---------|
| Reddit | `reddit_session` | ✅ Implemented | HIGH | Bypass 403, no rate limits |
| Twitter/X | `auth_token`, `ct0` | ⏳ Next | **CRITICAL** | Save $150/mo API costs |
| Medium | `sid` | 📋 Planned | MEDIUM | Paywall bypass |
| LinkedIn | `li_at` | 📋 Planned | LOW | Auth scraping |
| YouTube | `SAPISID` | 📋 Planned | LOW | Alternative to API |
| GitHub | `user_session` | 📋 Planned | LOW | Higher rate limits |
| Product Hunt | `_producthunt_session` | 📋 Planned | LOW | Alternative to API |
| Substack | `substack.sid` | 📋 Planned | MEDIUM | Newsletter access |

### Implementation Status

- [x] Cookie manager module designed
- [x] Auto cookie extractor tool designed
- [x] Reddit source updated to use cookies
- [ ] Cookie extractor tool implemented
- [ ] Twitter source with cookies (Batch 2)
- [ ] Medium source with cookies (Batch 3)
- [ ] Other platforms as needed

---

## PHASE 1: CONTENT SOURCES (12 Sources)

**Goal:** Aggregate content from 12 diverse sources

**Cost:** ~$2/month (Twitter API pay-as-you-go posting only)

### Sources:

| # | Source | Type | Status | Cost | Notes |
|---|--------|------|--------|------|-------|
| A | Twitter/X | **Cookie scraping + API** | ⏳ In Progress | **$2/mo** | **Cookies for reading, API for posting** |
| B | Reddit | **Cookie scraping** | ✅ Ready | **$0** | **reddit_session cookie** |
| C | Hacker News | API | ✅ Ready | $0 | Public API |
| D | YouTube | API | ⏳ In Progress | $0 | Free tier (10k quota/day) |
| E | ~~LinkedIn~~ | ~~Scraping~~ | ❌ Cancelled | - | Deferred to later |
| F | Product Hunt | API/Cookie | ⏳ In Progress | $0 | API primary, cookie backup |
| G | Substack | **Cookie scraping** | 📋 Planned | **$0** | **RSS + cookie auth** |
| H | Medium | **Cookie scraping** | 📋 Planned | **$0** | **sid cookie for paywall** |
| I | ArXiv | API | ✅ Ready | $0 | Public API |
| J | Discord | Bot API | 📋 Planned | $0 | Bot token |
| K | Perplexity | Web Scraping | 📋 Planned | $0 | Public discover page |
| L | Google Trends | API | ✅ Ready | $0 | pytrends |
| M | GitHub Discussions | GraphQL API | 📋 Planned | $0 | Free tier (5k req/hour) |

**Progress:**
- ✅ Base infrastructure updated (ContentCategory enum)
- ✅ Twitter API credentials configured ($5 credit)
- ✅ Implemented: Reddit, HN, ArXiv, Product Hunt, Google Trends
- 📋 Remaining: Substack, Medium, Discord, Perplexity, GitHub

---

## PHASE 2: DYNAMIC INFLUENCER SYSTEM

**Goal:** Self-updating influencer database with auto-discovery

**Why:** Hardcoded influencer lists become stale. Need dynamic discovery.

### Components:

#### 2.1 Influencer Database
```python
# data/influencers.json
{
  "username": {
    "followers": 1000000,
    "engagement_rate": 0.05,
    "category": "ai_ml",
    "relevance_score": 0.85,
    "is_active": true,
    "is_monitored": true
  }
}
```
**Status:** 📋 Planned

#### 2.2 Auto-Discovery Algorithms

| Algorithm | Description | Status |
|-----------|-------------|--------|
| Viral Tweet Discovery | Find authors of viral tweets (10k+ likes) | 📋 Planned |
| Trending Topics | Discover influencers from trending topics | 📋 Planned |
| Category Search | Find influencers by category keywords | 📋 Planned |
| Turkish Discovery | Discover Turkish tech influencers | 📋 Planned |

**Status:** 📋 Planned

#### 2.3 Auto-Refresh Service
- Weekly database refresh
- Update metrics for existing influencers
- Discover new influencers
- Mark inactive accounts
- Category rebalancing

**Status:** 📋 Planned

#### Seed Influencers (Starting Point):

**Global:**
- AI/ML: @sama, @ylecun, @karpathy, @goodfellow_ian
- Tech: @elonmusk, @satyanadella, @sundarpichai
- Crypto: @naval, @VitalikButerin, @cz_binance

**Turkish:**
- Tech: @fatihacet, @mrtcnylmz
- (Auto-discover more)

**Target:** 200+ influencers across all categories

---

## PHASE 3: CATEGORY DISTRIBUTION

**Goal:** Balanced content across 8 categories

### Target Distribution:

| Category | Target % | Tweets/Month | Sources |
|----------|----------|--------------|---------|
| 🤖 AI/ML | 30% | 27 | Twitter, Reddit, ArXiv, HN |
| 💻 Tech/Programming | 20% | 18 | HN, Reddit, GitHub, Medium |
| 🚀 Startup/Business | 15% | 14 | Product Hunt, HN, Twitter |
| 🎮 Gaming/Entertainment | 10% | 9 | Reddit, YouTube, Twitter |
| 💰 Crypto/Web3 | 10% | 9 | Twitter, Reddit, Medium |
| 📱 Mobile/Apps | 5% | 5 | Product Hunt, Reddit |
| 🔒 Security/Privacy | 5% | 5 | Reddit, ArXiv, HN |
| 🌍 Science | 5% | 5 | ArXiv, Reddit, Google Trends |
| **Total** | **100%** | **90 tweets/month (3/day)** | |

### Implementation:
- Content Aggregator filters by category
- AI Processor ensures distribution targets
- Scheduler balances daily posts
- Analytics track actual distribution

**Status:** 📋 Planned

---

## PHASE 4: DESKTOP APPLICATION

**Goal:** Tauri + React desktop app for management

**Tech Stack:** Tauri (Rust) + React + TypeScript

### Features:

#### 4.1 Dashboard
- Real-time worker status
- Queue statistics (pending/approved/scheduled)
- Category distribution chart
- Daily posting calendar

**Status:** 📋 Not Started

#### 4.2 Approval Interface
- Review pending tweets
- Approve/Reject/Edit buttons
- Preview with formatting
- Schedule override

**Status:** 📋 Not Started

#### 4.3 Source Management
- Enable/disable sources
- Configure source settings
- View source statistics
- Health monitoring

**Status:** 📋 Not Started

#### 4.4 Influencer Management
- Browse influencer database
- Search/filter by category
- Enable/disable monitoring
- View influencer stats
- Manual add/remove

**Status:** 📋 Not Started

#### 4.5 Analytics
- Tweet performance (likes, RTs)
- Best posting times
- Category performance
- Source effectiveness

**Status:** 📋 Not Started

---

## TIMELINE

### Week 1: Content Sources ⏳ (Current)
- ✅ Day 1: Project roadmap & documentation
- ✅ Day 2: Base infrastructure (ContentCategory, etc)
- ⏳ **Day 3: Cookie extraction tool + Reddit cookies** ← **CURRENT**
- 📋 Day 4: API-based sources (HN, ArXiv, PH, Trends)
- 📋 Day 5: Twitter/X with cookies + Nitter
- 📋 Day 6: Scraping sources (Medium, Substack, Perplexity)
- 📋 Day 7: Advanced sources (YouTube, Discord, GitHub)

### Week 2: Influencer System 📋
- Day 1-2: Influencer database schema + CRUD
- Day 3-4: Auto-discovery algorithms
- Day 5-6: Refresh service + scoring
- Day 7: Testing + seed data population

### Week 3: Category Distribution 📋
- Day 1-2: Category-aware aggregator
- Day 3-4: Distribution balancing logic
- Day 5-6: Scheduler updates
- Day 7: Testing + analytics

### Week 4: Desktop App 📋
- Day 1-3: Dashboard + approval interface
- Day 4-5: Source management
- Day 6-7: Influencer management + analytics

---

## DEPENDENCIES

### Python Packages (requirements.txt):
```
# Existing
tweepy
python-telegram-bot
google-generativeai
feedparser
playwright

# New - Phase 1
praw              # Reddit API
arxiv             # ArXiv API
pytrends          # Google Trends
aiohttp           # Async HTTP
beautifulsoup4    # Web scraping
discord.py        # Discord API
yt-dlp            # YouTube
lxml              # HTML parsing
```

### Environment Variables (.env):
```
# Twitter/X
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_TOKEN_SECRET=...

# Reddit
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=X-Hive/1.0

# Product Hunt
PRODUCTHUNT_API_TOKEN=...

# YouTube
YOUTUBE_API_KEY=...

# GitHub
GITHUB_TOKEN=...

# Discord
DISCORD_BOT_TOKEN=...
```

---

## COST BREAKDOWN

### Without Cookies (Old Approach)
| Service | Monthly Cost |
|---------|--------------|
| Twitter API (reading) | $150 |
| Twitter API (posting) | $2 |
| Reddit API | $0 (restricted) |
| Other APIs | $0 |
| **TOTAL** | **$152/month** |

### With Cookies (New Approach) ✅
| Service | Monthly Cost |
|---------|--------------|
| Twitter cookies (reading) | **$0** |
| Twitter API (posting only) | $2 |
| Reddit cookies | **$0** |
| Medium cookies | **$0** |
| Other APIs | $0 |
| **TOTAL** | **$2/month** |

**💰 Savings: $150/month = $1,800/year**

---

## SUCCESS METRICS

### Cost Efficiency
- ✅ Target: <$5/month total cost
- ✅ Current: $2/month (Twitter API posting only)
- ✅ Saved: $150/month vs API-only approach
- **Status: ✅ ACHIEVED**

### Content Quality
- 90% of generated tweets rated HIGH quality
- Category distribution within ±5% of targets
- 200+ active influencers in database

### Automation
- 3 tweets posted daily automatically
- 90% approval rate (10% rejection)
- Zero manual source configuration after setup

### Cookie Stability
- Cookies last >30 days without refresh
- <5% cookie expiration rate per month
- Auto-detection of expired cookies

### Engagement
- Average 50+ likes per tweet
- 10+ retweets per tweet
- Growing follower count

---

## CURRENT STATUS: PHASE 1 IN PROGRESS

### Next Steps:
- ✅ Create this roadmap document
- ⏳ Implement Reddit, HN, ArXiv, Product Hunt, Google Trends sources
- ⏳ Implement Twitter Nitter scraper
- 📋 Implement remaining sources
- 📋 Begin Phase 2: Influencer system

### Estimated Completion:
- Phase 1: 1 week
- Phase 2: 1 week
- Phase 3: 1 week
- Phase 4: 1 week
- **Total: 4 weeks to full v2.0 release**
