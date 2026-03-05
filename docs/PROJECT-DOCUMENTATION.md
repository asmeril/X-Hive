# X-HIVE v2.0 PROJECT DOCUMENTATION

## 📚 Complete Documentation Index

### Strategic Planning Documents

#### 1. **ROADMAP-v2.md** - Project Roadmap
- **Purpose:** High-level project vision and timeline
- **Contents:**
  - Overall progress metrics (4 phases)
  - 12 content sources with status
  - Dynamic influencer system (Phase 2)
  - Category distribution targets
  - Desktop app features
  - Week-by-week timeline
  - Dependency list
  - Cost breakdown (~$2/month)
  - Success metrics

**Status:** 📊 REFERENCE DOCUMENT

---

#### 2. **ARCHITECTURE-v2.md** - System Architecture
- **Purpose:** Technical system design and data flows
- **Contents:**
  - System overview diagram
  - Module architecture
  - 4 core subsystems:
    - Content Sources (12 sources)
    - Influencer System (auto-discovery)
    - Category Distribution (balanced content)
    - Desktop App (Tauri + React)
  - Data models (ContentItem, Influencer, Queue items)
  - REST API endpoints specification
  - Storage architecture (JSON → PostgreSQL)
  - Configuration management
  - Deployment procedures
  - Security measures
  - Monitoring strategy

**Status:** 📊 REFERENCE DOCUMENT

---

#### 3. **PHASE1-SOURCES.md** - Phase 1 Implementation Guide
- **Purpose:** Detailed implementation instructions for content sources
- **Contents:**
  - Implementation checklist (4 batches)
  - Batch 1: API-Based Sources (5 ✅ Done)
    - Reddit (PRAW) ✅
    - Hacker News (API) ✅
    - ArXiv (API) ✅
    - Product Hunt (API) ✅
    - Google Trends (pytrends) ✅
  - Batch 2: Twitter/X (Hybrid)
    - Twitter Scraper (Nitter)
    - Twitter Poster (existing)
  - Batch 3: Scraping Sources
    - Substack (RSS)
    - Medium (Web scraping)
    - Perplexity (Discover page)
  - Batch 4: Advanced Sources
    - YouTube (Data API)
    - Discord (Bot API)
    - GitHub Discussions (GraphQL)
  - Testing procedures
  - QA checklist
  - Integration guide
  - Progress tracking

**Status:** 📋 IMPLEMENTATION GUIDE

---

## 🎯 Quick Reference

### Current Progress

```
Overall Completion:      [████████░░] 40%
├─ Phase 1 Sources:       [████████░░] 42% (5/12 done)
├─ Phase 2 Influencers:   [██░░░░░░░░] 0%
├─ Phase 3 Distribution:  [█░░░░░░░░░] 0%
└─ Phase 4 Desktop App:   [░░░░░░░░░░] 0%
```

### Implemented (✅)
1. ContentCategory Enum (8 categories)
2. CATEGORY_TARGETS (distribution weights)
3. Reddit Source
4. Hacker News Source
5. ArXiv Source
6. Product Hunt Source
7. Google Trends Source
8. Base Source Infrastructure
9. Category Distribution Utilities

### In Progress (⏳)
- Twitter Scraper (Nitter)
- Full integration testing
- Category balance verification

### Planned (📋)
- Batch 3 sources (Substack, Medium, Perplexity)
- Batch 4 sources (YouTube, Discord, GitHub)
- Influencer discovery system
- Desktop application

---

## 📁 Repository Structure

```
X-Hive/
├── docs/                          # Documentation (you are here)
│   ├── ROADMAP-v2.md             # Overall roadmap ← START HERE
│   ├── ARCHITECTURE-v2.md        # System design
│   ├── PHASE1-SOURCES.md         # Implementation details
│   └── ...
│
├── apps/worker/
│   ├── intel/                     # Content intelligence
│   │   ├── base_source.py        # Base class + utilities
│   │   ├── aggregator.py         # Main orchestrator
│   │   ├── reddit_source.py      # ✅ Reddit (PRAW)
│   │   ├── hackernews_source.py  # ✅ Hacker News
│   │   ├── arxiv_source.py       # ✅ ArXiv
│   │   ├── producthunt_source.py # ✅ Product Hunt
│   │   ├── google_trends_source.py # ✅ Google Trends
│   │   ├── twitter_scraper.py    # 📋 (Nitter)
│   │   ├── substack_scraper.py   # 📋
│   │   ├── medium_scraper.py     # 📋
│   │   ├── youtube_source.py     # 📋
│   │   ├── discord_source.py     # 📋
│   │   ├── github_discussions.py # 📋
│   │   ├── perplexity_source.py  # 📋
│   │   └── ai_processor.py       # Gemini processing
│   │
│   ├── approval/                  # Approval system
│   │   ├── approval_queue.py
│   │   └── telegram_notifier.py
│   │
│   ├── scheduling/                # Scheduling
│   │   └── post_scheduler.py
│   │
│   ├── posting/                   # Twitter posting
│   │   ├── twitter_poster.py
│   │   └── auto_poster.py
│   │
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # Configuration
│   └── test_sources.py           # Integration tests
│
└── data/
    ├── approval_queue.json
    ├── post_schedule.json
    ├── influencers.json           # 📋 (Phase 2)
    └── content_cache.json
```

---

## 🚀 Getting Started

### For New Contributors

1. **Start with:** `docs/ROADMAP-v2.md`
   - Understand the 4 phases
   - See what's already done
   - Find your task in the timeline

2. **Then read:** `docs/ARCHITECTURE-v2.md`
   - Understand system structure
   - Learn the data models
   - See how components connect

3. **Finally:** `docs/PHASE1-SOURCES.md`
   - Pick an unimplemented source
   - Follow the implementation guide
   - Add testing

### For Implementation

Each source follows the same pattern:

```python
# 1. Extend BaseContentSource
class NewSource(BaseContentSource):
    def get_source_name(self) -> str:
        return "Source Name"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch content from API/web"""
        items = []
        # ... implementation ...
        return items

# 2. Create instance
new_source = NewSource()

# 3. Add to requirements.txt
# (e.g., praw, arxiv, etc.)

# 4. Add to .env (if needed)
# REDDIT_CLIENT_ID=...

# 5. Test
python test_sources.py
```

---

## 💡 Key Concepts

### ContentCategory
8 content categories with target distribution:
- 🤖 AI/ML (30%)
- 💻 Tech/Programming (20%)
- 🚀 Startup/Business (15%)
- 🎮 Gaming/Entertainment (10%)
- 💰 Crypto/Web3 (10%)
- 📱 Mobile/Apps (5%)
- 🔒 Security/Privacy (5%)
- 🌍 Science (5%)

### Content Pipeline
```
Source → ContentItem → Aggregator → Deduplication 
→ Categorization → AI Processing → Approval Queue 
→ Scheduler → Twitter API
```

### Four Phases
1. **Phase 1:** 12 Content Sources (IN PROGRESS)
2. **Phase 2:** Dynamic Influencer System (PLANNED)
3. **Phase 3:** Category Distribution Balancing (PLANNED)
4. **Phase 4:** Desktop Management App (PLANNED)

---

## 📊 Status Summary

| Component | Status | Progress | Owner |
|-----------|--------|----------|-------|
| Content Sources | ⏳ In Progress | 42% | Phase 1 |
| Influencer System | 📋 Planned | 0% | Phase 2 |
| Category Balance | 📋 Planned | 0% | Phase 3 |
| Desktop App | 📋 Planned | 0% | Phase 4 |
| Documentation | ✅ Done | 100% | Complete |
| Testing | ⏳ In Progress | 40% | Ongoing |

---

## 🔧 Technical Stack

- **Language:** Python 3.11
- **Content Sources:** PRAW, aiohttp, BeautifulSoup4, feedparser
- **AI:** Google Gemini 2.5
- **Twitter:** tweepy (OAuth1a)
- **Telegram:** python-telegram-bot
- **Desktop:** Tauri + React + TypeScript (future)
- **Storage:** JSON (current) → PostgreSQL (future)

---

## 📞 Important Links

- **GitHub Repo:** X-Hive (asmeril/X-Hive)
- **Current Branch:** main
- **Approval Bot:** Telegram (@X_Hive_Approval_Bot)
- **Twitter Account:** @X_Hive_Pro

---

## ❓ FAQ

### Q: What's the fastest path to get running?
A: Follow PHASE1-SOURCES.md, implement Batch 1 (API sources) first - they're easiest and cost nothing.

### Q: How much does this cost?
A: ~$2/month for Twitter API (pay-as-you-go). Everything else is free.

### Q: Can I implement sources in parallel?
A: Yes! Each source is independent. Pick one from PHASE1-SOURCES.md and implement it.

### Q: What's the quality target?
A: 90% HIGH quality tweets, 3 per day, 50+ likes average, balanced across 8 categories.

### Q: When's Phase 2?
A: After Phase 1 completes (~1 week). Then Influencer System with auto-discovery.

---

## 📝 Document Versioning

- **v2.0:** Complete system redesign (current)
- **v1.0:** Basic approval + scheduling system
- **Created:** 2026-02-07

---

**Last Updated:** 2026-02-07 
**Next Review:** 2026-02-14 (1 week)
