# X-HIVE v2.0 ARCHITECTURE

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                     X-HIVE v2.0 SYSTEM                      │
│                                                             │
│  ┌─────────────┐      ┌──────────────┐     ┌─────────────┐ │
│  │   Desktop   │◄────►│    Worker    │◄───►│  Telegram   │ │
│  │  (Tauri +   │ REST │  (FastAPI +  │ Bot │     Bot     │ │
│  │   React)    │ API  │   Python)    │ API │             │ │
│  └─────────────┘      └──────────────┘     └─────────────┘ │
│                              │                              │
│                              │                              │
│                    ┌─────────▼──────────┐                   │
│                    │  Content Pipeline  │                   │
│                    └─────────┬──────────┘                   │
│                              │                              │
│         ┌────────────────────┼────────────────────┐         │
│         │                    │                    │         │
│    ┌────▼─────┐      ┌──────▼──────┐      ┌─────▼────┐    │
│    │ Content  │      │  Influencer │      │ Category │    │
│    │  Sources │      │  Discovery  │      │  Balance │    │
│    │ (12 src) │      │   System    │      │  Engine  │    │
│    └────┬─────┘      └──────┬──────┘      └─────┬────┘    │
│         │                   │                    │         │
│         └───────────────────┼────────────────────┘         │
│                             │                              │
│                    ┌────────▼─────────┐                    │
│                    │   AI Processor   │                    │
│                    │  (Gemini 2.5)    │                    │
│                    └────────┬─────────┘                    │
│                             │                              │
│                    ┌────────▼─────────┐                    │
│                    │ Approval Queue   │                    │
│                    └────────┬─────────┘                    │
│                             │                              │
│                    ┌────────▼─────────┐                    │
│                    │    Scheduler     │                    │
│                    └────────┬─────────┘                    │
│                             │                              │
│                    ┌────────▼─────────┐                    │
│                    │   Twitter API    │                    │
│                    │   (Post Tweet)   │                    │
│                    └──────────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Architecture

### 1. Content Sources (apps/worker/intel/)

**Purpose:** Aggregate content from 12 diverse sources

```
intel/
├── base_source.py              # Base class for all sources
├── aggregator.py               # Main aggregation orchestrator
│
├── twitter_scraper.py          # Nitter + Twitter API
├── reddit_source.py            # PRAW API
├── hackernews_source.py        # HN API
├── youtube_source.py           # YouTube Data API
├── producthunt_source.py       # Product Hunt API
├── arxiv_source.py             # ArXiv API
├── google_trends_source.py     # pytrends
├── github_discussions.py       # GitHub GraphQL
├── substack_scraper.py         # RSS scraping
├── medium_scraper.py           # Web scraping
├── discord_source.py           # discord.py
└── perplexity_source.py        # Web scraping
```

**Data Flow:**
```
Source → ContentItem → Aggregator → Deduplication → Category Classification → AI Processing
```

---

### 2. Influencer System (apps/worker/intel/influencer/)

**Purpose:** Dynamic influencer discovery and management

```
influencer/
├── influencer_db.py            # Database + models
├── discovery.py                # Auto-discovery algorithms
├── scoring.py                  # Relevance/quality scoring
└── refresh_service.py          # Periodic refresh
```

**Influencer Model:**
```python
@dataclass
class Influencer:
    username: str
    twitter_id: str
    followers_count: int
    engagement_rate: float
    primary_category: ContentCategory
    relevance_score: float
    activity_score: float
    quality_score: float
    is_active: bool
    is_monitored: bool
```

**Discovery Algorithms:**
- Viral Tweet Discovery - Find authors of viral content (10k+ likes)
- Trending Topic Discovery - Extract influencers from trending topics
- Category Search - Find influencers by category keywords
- Turkish Discovery - Discover Turkish tech influencers

---

### 3. Category Distribution (apps/worker/intel/category/)

**Purpose:** Ensure balanced content across 8 categories

```
category/
├── categorizer.py              # Auto-categorization
├── balancer.py                 # Distribution balancing
└── config.py                   # Category targets
```

**Category Targets:**
```python
CATEGORY_TARGETS = {
    ContentCategory.AI_ML: 0.30,              # 30%
    ContentCategory.TECH_PROGRAMMING: 0.20,   # 20%
    ContentCategory.STARTUP_BUSINESS: 0.15,   # 15%
    ContentCategory.GAMING_ENTERTAINMENT: 0.10, # 10%
    ContentCategory.CRYPTO_WEB3: 0.10,        # 10%
    ContentCategory.MOBILE_APPS: 0.05,        # 5%
    ContentCategory.SECURITY_PRIVACY: 0.05,   # 5%
    ContentCategory.SCIENCE: 0.05,            # 5%
}
```

---

### 4. Desktop App (apps/desktop/)

**Tech Stack:** Tauri + React + TypeScript

```
desktop/
├── src/
│   ├── components/
│   │   ├── Dashboard.tsx
│   │   ├── ApprovalInterface.tsx
│   │   ├── SourceManager.tsx
│   │   ├── InfluencerManager.tsx
│   │   └── Analytics.tsx
│   ├── api/
│   │   └── workerApi.ts         # REST API client
│   └── App.tsx
└── src-tauri/
    └── src/
        └── main.rs               # Tauri backend
```

---

## Data Models

### ContentItem
```python
@dataclass
class ContentItem:
    title: str
    url: str
    source_type: str
    source_name: str
    published_at: datetime
    category: ContentCategory
    relevance_score: float
    engagement_score: float
    description: Optional[str]
    author: Optional[str]
    ai_summary: Optional[str]
    suggested_tweet: Optional[str]
```

### Influencer
```python
@dataclass
class Influencer:
    username: str
    twitter_id: str
    followers_count: int
    engagement_rate: float
    primary_category: ContentCategory
    relevance_score: float
    activity_score: float
    quality_score: float
    is_active: bool
    is_monitored: bool
    last_checked: datetime
    discovered_at: datetime
```

### ApprovalQueueItem
```python
@dataclass
class ApprovalQueueItem:
    tweet_id: str
    content_item: ContentItem
    generated_tweet: str
    status: ApprovalStatus
    approved_at: Optional[datetime]
    rejected_at: Optional[datetime]
    edited_tweet: Optional[str]
```

### ScheduledPost
```python
@dataclass
class ScheduledPost:
    post_id: str
    tweet_id: str
    scheduled_time: datetime
    status: PostStatus
    posted_at: Optional[datetime]
    twitter_id: Optional[str]
    error_message: Optional[str]
```

---

## API Endpoints (Worker FastAPI)

### Content
```
GET    /api/content/sources                    # List all sources
GET    /api/content/latest                    # Get latest aggregated content
POST   /api/content/refresh                   # Trigger content refresh
GET    /api/content/by-category/{category}    # Get content by category
```

### Influencers
```
GET    /api/influencers                       # List all influencers
GET    /api/influencers/{username}            # Get influencer details
POST   /api/influencers/discover              # Trigger discovery
PUT    /api/influencers/{username}            # Update influencer
DELETE /api/influencers/{username}            # Remove influencer
GET    /api/influencers/by-category/{cat}     # Get by category
```

### Approval Queue
```
GET    /api/queue/pending                     # Get pending tweets
GET    /api/queue/approved                    # Get approved tweets
GET    /api/queue/{tweet_id}                  # Get single tweet
POST   /api/queue/{tweet_id}/approve          # Approve tweet
POST   /api/queue/{tweet_id}/reject           # Reject tweet
POST   /api/queue/{tweet_id}/edit             # Edit tweet text
```

### Scheduler
```
GET    /api/schedule/upcoming                 # Get upcoming posts
GET    /api/schedule/history                  # Get post history
POST   /api/schedule/{tweet_id}/reschedule    # Reschedule post
DELETE /api/schedule/{post_id}                # Cancel scheduled post
```

### Analytics
```
GET    /api/analytics/categories              # Category distribution
GET    /api/analytics/sources                 # Source effectiveness
GET    /api/analytics/engagement              # Tweet engagement stats
GET    /api/analytics/influencers             # Influencer performance
GET    /api/analytics/timeline                # Performance timeline
```

---

## Storage

### Files:
```
apps/worker/data/
├── approval_queue.json         # Approval queue
├── post_schedule.json          # Scheduled posts
├── influencers.json            # Influencer database
├── content_cache.json          # Content cache
└── analytics.json              # Analytics data
```

### Future (PostgreSQL):
```sql
CREATE TABLE influencers (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE,
    twitter_id BIGINT UNIQUE,
    followers_count INT,
    engagement_rate FLOAT,
    primary_category VARCHAR(50),
    relevance_score FLOAT,
    is_active BOOLEAN,
    is_monitored BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE content_items (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500),
    url VARCHAR(2000),
    source_type VARCHAR(50),
    source_name VARCHAR(100),
    category VARCHAR(50),
    relevance_score FLOAT,
    engagement_score FLOAT,
    collected_at TIMESTAMP
);

CREATE TABLE approval_queue (
    id SERIAL PRIMARY KEY,
    content_id INT REFERENCES content_items(id),
    generated_tweet TEXT,
    status VARCHAR(50),
    approved_at TIMESTAMP,
    created_at TIMESTAMP
);

CREATE TABLE scheduled_posts (
    id SERIAL PRIMARY KEY,
    approval_id INT REFERENCES approval_queue(id),
    scheduled_time TIMESTAMP,
    status VARCHAR(50),
    posted_at TIMESTAMP,
    twitter_id BIGINT
);

CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    post_id INT REFERENCES scheduled_posts(id),
    likes INT,
    retweets INT,
    replies INT,
    collected_at TIMESTAMP
);
```

---

## Configuration

### Environment Variables:
```bash
# Twitter/X
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_TOKEN_SECRET=...

# Reddit
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...

# YouTube
YOUTUBE_API_KEY=...

# GitHub
GITHUB_TOKEN=...

# Discord
DISCORD_BOT_TOKEN=...

# Telegram (for bot)
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

### Config Files:
```
apps/worker/config/
├── sources.yaml                # Source configurations
├── categories.yaml             # Category settings
└── influencers_seed.yaml       # Seed influencers
```

---

## Deployment

### Development:
```bash
# Worker
cd apps/worker
python -m uvicorn app.main:app --reload

# Desktop
cd apps/desktop
npm run tauri dev
```

### Production:
```bash
# Worker (background service)
python -m posting.auto_poster

# Desktop (compiled binary)
npm run tauri build
```

---

## Security

- ✅ Environment variables for all credentials
- ✅ .env files in .gitignore
- ✅ Rate limiting on all APIs
- ✅ Input validation on all endpoints
- ✅ No hardcoded secrets
- ✅ Error handling without exposing internals

---

## Monitoring

- 📊 Logging to files
- 🚨 Error tracking
- 💓 Source health monitoring
- 📈 API rate limit tracking
- 🔔 Queue size alerts
- 📊 Analytics dashboard
