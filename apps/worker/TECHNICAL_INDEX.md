# X-Hive Technical Index 🗂️

**Last Updated:** 5 Mart 2026  
**Version:** 1.0.0  
**Status:** Production Ready ✅

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Directory Structure](#directory-structure)
3. [Core Modules](#core-modules)
4. [Intelligence System](#intelligence-system)
5. [Task & Queue Management](#task--queue-management)
6. [Posting System](#posting-system)
7. [Monitoring & Logging](#monitoring--logging)
8. [Configuration](#configuration)
9. [Testing](#testing)
10. [Data Flow](#data-flow)
11. [API Reference](#api-reference)
12. [Troubleshooting Guide](#troubleshooting-guide)

---

## 📌 Project Overview

**X-Hive** is an AI-powered automated Twitter (X) posting system that:
- Aggregates tech/AI content from multiple sources (GitHub, RSS, Telegram)
- Uses Google Gemini AI to generate Turkish & English tweets
- Posts automatically with scheduling and approval workflows
- Monitors system health and collects metrics

**Tech Stack:**
- Python 3.11
- Playwright (browser automation)
- Google Gemini 2.5 Flash (AI)
- Telethon (Telegram)
- APScheduler (job scheduling)
- python-telegram-bot (approval bot)

---

## 📁 Directory Structure

```
apps/worker/
├── intel/                          # Intelligence & Content Aggregation
│   ├── __init__.py                # Module initialization
│   ├── base_source.py             # Base classes & data models
│   ├── aggregator.py              # Multi-source content aggregator
│   ├── ai_processor.py            # Gemini AI tweet generator
│   ├── github_source.py           # GitHub Trending scraper
│   ├── rss_source.py              # RSS feed aggregator
│   └── telegram_source.py         # Telegram channel scraper
│
├── Core System Files
│   ├── orchestrator.py            # Main system orchestrator
│   ├── task_queue.py              # Task queue manager
│   ├── chrome_pool.py             # Browser pool manager
│   ├── x_daemon.py                # X (Twitter) posting daemon
│   ├── post_scheduler.py          # Post scheduling system
│   ├── approval_manager.py        # Approval workflow manager
│   ├── telegram_bot.py            # Telegram approval bot
│   ├── ai_content_generator.py    # Legacy AI generator (transitioning)
│   └── content_generator.py       # Content generation coordinator
│
├── Utilities
│   ├── health_check.py            # System health monitoring
│   ├── metrics_collector.py       # Performance metrics
│   ├── structured_logger.py       # JSON logging
│   ├── safety_logger.py           # Safety checks logger
│   ├── rate_limiter.py            # Rate limiting
│   ├── lock_manager.py            # File-based locking
│   └── human_behavior.py          # Human-like delays
│
├── Configuration
│   ├── .env                       # Environment variables (SECRET)
│   ├── .env.example               # Environment template
│   ├── config.py                  # Configuration loader
│   └── requirements.txt           # Python dependencies
│
├── Testing
│   ├── test_aggregator.py         # Content aggregation tests
│   ├── test_ai_processor.py       # AI processor tests
│   ├── test_github.py             # GitHub source tests
│   ├── test_rss.py                # RSS source tests
│   ├── test_telegram.py           # Telegram source tests
│   ├── test_full_system.py        # End-to-end tests
│   └── test_*.py                  # Other component tests
│
├── Data & Runtime
│   ├── data/                      # Runtime data storage
│   │   ├── telegram/              # Telegram session files
│   │   ├── task_history.json     # Task history
│   │   └── metrics.json           # Metrics data
│   ├── .venv/                     # Python virtual environment
│   └── __pycache__/               # Python bytecode cache
│
└── Documentation
    ├── README.md                  # Project documentation
    ├── AI_CONTENT_GENERATOR_SETUP.md  # AI setup guide
    ├── IMPLEMENTATION_SUMMARY.md  # Implementation details
    ├── PROJECT_STRUCTURE.md       # Project structure
    └── TECHNICAL_INDEX.md         # This file
```

---

## 🧠 Core Modules

### Orchestrator (`orchestrator.py`)

**Main class:** `Orchestrator`

**Purpose:** Central coordinator for all system components

**Key Methods:**
```python
async def start()                    # Line 150 - Start all systems
async def stop()                     # Line 200 - Graceful shutdown
async def post_now(content, **kwargs) # Line 250 - Immediate post
def get_status()                     # Line 300 - System status
def health_check()                   # Line 350 - Health check
```

**Dependencies:**
- `TaskQueue` (task management)
- `PostScheduler` (scheduling)
- `ApprovalManager` (approval workflow)
- `TelegramBot` (bot interface)
- `ContentGenerator` (content creation)

**Usage:**
```python
from orchestrator import Orchestrator

orchestrator = Orchestrator()
await orchestrator.start()
await orchestrator.post_now("Hello X!")
await orchestrator.stop()
```

---

### Task Queue (`task_queue.py`)

**Main class:** `TaskQueue` (Singleton)

**Purpose:** Manages task lifecycle, retry logic, and Dead Letter Queue

**Key Methods:**
```python
def add_task(task_type, data, priority)  # Line 100 - Queue new task
async def start()                         # Line 150 - Start processor
async def stop()                          # Line 200 - Stop processor
def get_stats()                           # Line 250 - Queue statistics
def get_dlq_tasks()                       # Line 300 - Failed tasks
def clear_dlq()                           # Line 350 - Clear DLQ
```

**Task Types:**
- `post_tweet` - Post a tweet
- `generate_content` - Generate AI content
- `health_check` - System health check

**Data Model:**
```python
@dataclass
class Task:
    id: str
    type: str
    data: dict
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    attempts: int
    max_attempts: int
```

**File Location:** Lines 1-600  
**Key Features:** Auto-retry, DLQ, persistence, priority queue

---

### Chrome Pool (`chrome_pool.py`)

**Main class:** `ChromePool` (Singleton)

**Purpose:** Manages browser instances with stealth mode

**Key Methods:**
```python
async def get_browser()              # Line 80 - Get browser instance
async def close()                    # Line 150 - Close browser
async def health_check()             # Line 200 - Browser health
```

**Configuration:**
```python
# Lines 30-50
STEALTH_CONFIG = {
    'viewport': {'width': 1920, 'height': 1080},
    'user_agent': 'Mozilla/5.0...',
    'locale': 'en-US',
    'timezone': 'America/Los_Angeles'
}
```

**File Location:** Lines 1-300

---

### X Daemon (`x_daemon.py`)

**Main class:** `XDaemon`

**Purpose:** Posts tweets to X (Twitter) via Playwright

**Key Methods:**
```python
async def execute_task(task)         # Line 100 - Execute post task
async def post_tweet(content, media) # Line 200 - Post tweet
async def login()                    # Line 300 - Login to X
async def _perform_safety_checks()   # Line 400 - Pre-post checks
```

**Safety Features:**
- Content validation (Line 420)
- Rate limit checking (Line 450)
- Login verification (Line 480)
- Error recovery (Line 500)

**File Location:** Lines 1-700  
**Retry Logic:** Max 2 attempts with 5-second delay

---

## 🔍 Intelligence System

### Content Aggregator (`intel/aggregator.py`)

**Main class:** `ContentAggregator`

**Purpose:** Aggregates content from multiple sources

**Key Methods:**
```python
async def fetch_all()                     # Line 50 - Fetch from all sources
def get_top_items(items, n=10)           # Line 100 - Get top N items
def filter_by_category(items, category)  # Line 150 - Category filter
def get_stats()                          # Line 200 - Aggregation stats
```

**Sources Integration:**
```python
# Lines 20-40
self.sources = [
    github_source,      # GitHub Trending
    tech_news_source,   # RSS Tech News
    ai_news_source,     # RSS AI News
    telegram_source     # Telegram Channels
]
```

**File Location:** Lines 1-250

---

### AI Processor (`intel/ai_processor.py`)

**Main class:** `AIContentProcessor`

**Purpose:** Gemini-powered Turkish & English tweet generation

**Key Methods:**
```python
async def process_item(item)              # Line 150 - Process single item
async def process_batch(items, max_items) # Line 250 - Batch processing
def filter_by_quality(items, min_quality) # Line 350 - Quality filter
def _build_turkish_prompt(item)           # Line 400 - Turkish prompt
def _build_english_prompt(item)           # Line 500 - English prompt
```

**Quality Scoring System (8 points):**
```python
# Lines 200-230
QUALITY_CRITERIA = {
    'relevance': 2,      # Topic relevance
    'engagement': 2,     # Engagement potential
    'clarity': 1,        # Message clarity
    'value': 1,          # Information value
    'timeliness': 1,     # News freshness
    'completeness': 1    # Content completeness
}
```

**Gemini Configuration:**
```python
# Lines 50-80
MODEL = "gemini-2.5-flash"
TEMPERATURE = 0.7
MAX_TOKENS = 300
TOP_P = 0.9
```

**File Location:** Lines 1-600  
**Languages:** Turkish (primary), English (fallback)

---

### GitHub Source (`intel/github_source.py`)

**Main class:** `GitHubTrendingSource`

**Purpose:** Scrapes GitHub Trending repositories

**Key Methods:**
```python
async def fetch_latest(limit=25)     # Line 50 - Fetch trending repos
async def _fetch_trending_page(lang) # Line 150 - Fetch specific language
def _parse_repository(article)       # Line 250 - Parse repo data
```

**Supported Languages:**
```python
# Line 30
LANGUAGES = ['python', 'javascript', 'rust', 'c++', 'jupyter-notebook']
```

**Data Extracted:**
- Repository name & URL
- Description
- Star count
- Today's stars
- Language
- Fork count

**File Location:** Lines 1-400

---

### RSS Source (`intel/rss_source.py`)

**Main class:** `RSSSource`

**Purpose:** Aggregates content from RSS feeds

**Key Methods:**
```python
async def fetch_latest(limit=50)         # Line 100 - Fetch from all feeds
async def _fetch_feed(name, url)         # Line 200 - Fetch single feed
def _categorize_content(title, desc)     # Line 300 - Auto-categorize
```

**Preconfigured Sources:**
```python
# Lines 400-500
tech_news_source = RSSSource(
    feed_name="Tech News Aggregator",
    feeds={
        'TechCrunch': 'https://techcrunch.com/feed/',
        'The Verge': 'https://www.theverge.com/rss/index.xml',
        'Ars Technica': 'https://feeds.arstechnica.com/arstechnica/index',
        'Hacker News': 'https://hnrss.org/frontpage',
        'MIT Tech Review': 'https://www.technologyreview.com/feed/',
        # ... more feeds
    }
)

ai_news_source = RSSSource(
    feed_name="AI & ML News Aggregator",
    feeds={
        'OpenAI Blog': 'https://openai.com/blog/rss/',
        'DeepMind': 'https://deepmind.google/blog/rss.xml',
        'Google AI': 'https://blog.google/technology/ai/rss/',
        # ... more AI feeds
    }
)
```

**File Location:** Lines 1-600

---

### Telegram Source (`intel/telegram_source.py`)

**Main class:** `TelegramChannelSource`

**Purpose:** Scrapes Telegram channels for content

**Key Methods:**
```python
async def initialize()                   # Line 80 - Connect to Telegram
async def fetch_latest(limit=50)         # Line 150 - Fetch messages
async def disconnect()                   # Line 250 - Disconnect
def _categorize_message(text)            # Line 300 - Categorize content
```

**Configured Channels:**
```python
# Lines 40-60
CHANNELS = [
    '@techcrunch',
    '@verge',
    '@hackernews'
]
```

**Authentication:**
- Uses `.env` credentials: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`
- Session persisted in `data/telegram/`
- 2FA support

**File Location:** Lines 1-500

---

### Base Source (`intel/base_source.py`)

**Purpose:** Base classes and data models for all sources

**Key Classes:**
```python
# Lines 20-100
class ContentCategory(Enum):
    AI_ML = "ai_ml"
    TECH_NEWS = "tech_news"
    PRODUCTIVITY = "productivity"
    STARTUP = "startup"
    PROGRAMMING = "programming"
    OTHER = "other"

class ContentQuality(Enum):
    HIGH = "high"      # >= 7 points
    MEDIUM = "medium"  # >= 5 points
    LOW = "low"        # < 5 points

@dataclass
class ContentItem:
    title: str
    url: str
    source_type: str  # 'github', 'rss', 'telegram'
    source_name: str
    description: str = ""
    category: ContentCategory = ContentCategory.OTHER
    quality: ContentQuality = ContentQuality.MEDIUM
    relevance_score: float = 0.0
    engagement_score: float = 0.0
    published_at: datetime = None
    tags: List[str] = None
    processed: bool = False
    ai_summary: str = ""
    suggested_tweet: str = ""

class BaseSource(ABC):
    @abstractmethod
    async def fetch_latest(self, limit: int) -> List[ContentItem]:
        pass
```

**File Location:** Lines 1-300

---

## 📝 Task & Queue Management

### Task Lifecycle

```
1. CREATED    → Task added to queue
   ↓
2. PENDING    → Waiting in priority queue
   ↓
3. PROCESSING → Being executed
   ↓
4. COMPLETED  → Successfully finished
   ↓ (if failed)
5. FAILED     → Max retries exceeded → DLQ
```

**Implementation:** `task_queue.py` Lines 100-400

### Priority System

```python
# task_queue.py Lines 50-70
class TaskPriority(Enum):
    HIGH = 1      # Immediate posts
    NORMAL = 2    # Scheduled posts
    LOW = 3       # Background tasks
```

**Queue Processing:**
- High priority processed first
- FIFO within same priority
- Max 4 retry attempts
- 5-second delay between retries

### Dead Letter Queue (DLQ)

**Purpose:** Store permanently failed tasks for analysis

**Access Methods:**
```python
# task_queue.py Lines 300-350
queue = TaskQueue()
dlq_tasks = queue.get_dlq_tasks()      # Get all failed tasks
count = queue.get_dlq_count()          # Count failed tasks
queue.clear_dlq()                      # Clear DLQ
queue.retry_dlq_task(task_id)         # Retry specific task
```

**Persistence:** `data/task_history.json`

---

## 📤 Posting System

### Post Scheduler (`post_scheduler.py`)

**Main class:** `PostScheduler`

**Purpose:** Schedule posts at specific times

**Key Methods:**
```python
async def start()                     # Line 100 - Start scheduler
async def stop()                      # Line 150 - Stop scheduler
async def schedule_post(time, content) # Line 200 - Schedule new post
def get_scheduled_posts()             # Line 250 - List scheduled
```

**Configuration:**
```python
# Lines 50-80
POST_TIMES = [
    "09:00",  # Morning
    "14:00",  # Afternoon
    "20:00"   # Evening
]
TIMEZONE = "Europe/Istanbul"
```

**File Location:** Lines 1-400

---

### Approval Manager (`approval_manager.py`)

**Main class:** `ApprovalManager`

**Purpose:** Manage tweet approval workflow

**Approval Modes:**
```python
# Lines 30-50
class ApprovalMode(Enum):
    DISABLED = "disabled"        # Auto-approve all
    MANUAL = "manual"            # Require approval
    AUTO_APPROVE = "auto_approve" # Auto after timeout
```

**Key Methods:**
```python
async def request_approval(content)   # Line 100 - Request approval
async def approve(request_id)         # Line 200 - Approve tweet
async def reject(request_id, reason)  # Line 250 - Reject tweet
def get_pending_approvals()           # Line 300 - List pending
```

**Telegram Integration:** Lines 150-180

**File Location:** Lines 1-500

---

### Telegram Bot (`telegram_bot.py`)

**Main class:** `TelegramApprovalBot`

**Purpose:** Telegram bot for approving tweets

**Commands:**
```python
/start       # Welcome message
/pending     # Show pending approvals
/approve [id] # Approve tweet
/reject [id]  # Reject tweet
/stats       # System statistics
/health      # Health check
```

**Implementation:**
```python
# Lines 100-300
async def handle_approve(update, context)  # Line 150
async def handle_reject(update, context)   # Line 200
async def handle_pending(update, context)  # Line 250
```

**Inline Keyboards:** Lines 180-220  
**File Location:** Lines 1-600

---

## 📊 Monitoring & Logging

### Health Check (`health_check.py`)

**Main class:** `HealthChecker` (Singleton)

**Purpose:** Monitor system component health

**Components Monitored:**
```python
# Lines 50-100
- ChromePool (browser status)
- TaskQueue (queue size, processing)
- XDaemon (login status, rate limits)
- PostScheduler (job status)
- Disk space (< 10% warning)
- Memory usage (< 100MB warning)
```

**Key Methods:**
```python
async def check_all()                 # Line 150 - Check all components
def get_health_report()               # Line 200 - Full health report
async def check_component(name)       # Line 250 - Check specific component
```

**Health Status:**
```python
class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
```

**File Location:** Lines 1-400

---

### Metrics Collector (`metrics_collector.py`)

**Main class:** `MetricsCollector` (Singleton)

**Purpose:** Collect and store performance metrics

**Metrics Tracked:**
```python
# Lines 50-150
- Task metrics (total, completed, failed, avg time)
- Post metrics (posts/day, success rate, engagement)
- System metrics (uptime, memory, CPU)
- Error metrics (by type, by component)
- Rate limit metrics (requests/hour, throttling)
```

**Key Methods:**
```python
def increment_counter(name, value)    # Line 200 - Increment counter
def record_timing(name, duration)     # Line 250 - Record timing
def record_gauge(name, value)         # Line 300 - Set gauge value
def get_metrics_report()              # Line 350 - Full metrics
def reset()                           # Line 400 - Reset metrics
```

**Persistence:** `data/metrics.json`  
**File Location:** Lines 1-600

---

### Structured Logger (`structured_logger.py`)

**Purpose:** JSON-formatted logging for easy parsing

**Logger Instances:**
```python
# Lines 50-100
task_logger = get_logger("task")          # Task operations
health_logger = get_logger("health")      # Health checks
security_logger = get_logger("security")  # Security events
error_logger = get_logger("error")        # Errors
```

**Log Format:**
```json
{
  "timestamp": "2026-02-06T15:30:00.000Z",
  "level": "INFO",
  "logger": "task",
  "message": "Task completed",
  "task_id": "abc-123",
  "duration": 2.5,
  "status": "success"
}
```

**Usage:**
```python
from structured_logger import task_logger

task_logger.info(
    "Task started",
    task_id="abc-123",
    task_type="post_tweet"
)
```

**File Location:** Lines 1-300

---

## ⚙️ Configuration

### Environment Variables (`.env`)

**Critical Variables:**
```bash
# X (Twitter) Credentials
X_USERNAME=your_username
X_PASSWORD=your_password
X_EMAIL=your_email

# Google Gemini AI
GEMINI_API_KEY=your_gemini_key

# Telegram Bot
TELEGRAM_BOT_TOKEN=bot_token
TELEGRAM_ADMIN_ID=your_chat_id

# Telegram API (for channel scraping)
TELEGRAM_API_ID=api_id
TELEGRAM_API_HASH=api_hash
TELEGRAM_PHONE=+1234567890

# System Settings
POSTS_PER_DAY=3
POST_TIMES=09:00,14:00,20:00
APPROVAL_MODE=manual
AI_LANGUAGE=tr

# Optional
DEBUG=false
LOG_LEVEL=INFO
TIMEZONE=Europe/Istanbul
```

**File:** `.env` (not in git)  
**Template:** `.env.example`

---

### Configuration Loader (`config.py`)

**Purpose:** Load and validate environment variables

**Key Functions:**
```python
def load_config()                     # Line 50 - Load all config
def get(key, default=None)            # Line 100 - Get config value
def validate_required()               # Line 150 - Validate required vars
```

**Configuration Objects:**
```python
# Lines 200-300
class Config:
    X_USERNAME: str
    X_PASSWORD: str
    GEMINI_API_KEY: str
    TELEGRAM_BOT_TOKEN: str
    POSTS_PER_DAY: int = 3
    POST_TIMES: List[str] = ["09:00", "14:00", "20:00"]
    APPROVAL_MODE: str = "manual"
    AI_LANGUAGE: str = "tr"
```

**File Location:** Lines 1-400

---

## 🧪 Testing

### Test Organization

```
test_*.py files:

Core Tests:
├── test_aggregator.py        # Content aggregation (Lines 1-300)
├── test_ai_processor.py      # AI tweet generation (Lines 1-400)
├── test_full_system.py       # End-to-end system test (Lines 1-500)
└── test_infrastructure.py    # Infrastructure components (Lines 1-350)

Source Tests:
├── test_github.py            # GitHub scraping (Lines 1-250)
├── test_rss.py               # RSS feeds (Lines 1-300)
└── test_telegram.py          # Telegram channels (Lines 1-350)

Component Tests:
├── test_chrome_pool.py       # Browser pool (Lines 1-200)
├── test_task_queue.py        # Task queue (Lines 1-300)
├── test_x_daemon.py          # X posting (Lines 1-400)
├── test_post_scheduler.py    # Scheduling (Lines 1-250)
└── test_telegram_bot.py      # Telegram bot (Lines 1-300)

Integration Tests:
├── test_orchestrator.py      # Orchestrator (Lines 1-400)
└── test_production_ready.py  # Production validation (Lines 1-300)
```

### Running Tests

```bash
# Single test
python test_aggregator.py

# All tests
python -m pytest test_*.py

# With coverage
python -m pytest --cov=. test_*.py

# Specific component
python test_ai_processor.py
```

---

## 🔄 Data Flow

### Content Aggregation → AI Processing → Posting

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTENT SOURCES                          │
├─────────────────────────────────────────────────────────────┤
│  GitHub Trending  │  RSS Feeds  │  Telegram Channels        │
└────────┬──────────┴─────┬───────┴────────┬─────────────────┘
         │                │                │
         └────────────────┼────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │   ContentAggregator            │
         │   (intel/aggregator.py)        │
         │   - Fetch from all sources     │
         │   - Deduplicate                │
         │   - Sort by relevance          │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │   AIContentProcessor           │
         │   (intel/ai_processor.py)      │
         │   - Generate Turkish tweets    │
         │   - Quality scoring (8-point)  │
         │   - Filter low quality         │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │   ApprovalManager              │
         │   (approval_manager.py)        │
         │   - Manual/Auto approval       │
         │   - Telegram bot interface     │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │   TaskQueue                    │
         │   (task_queue.py)              │
         │   - Priority queuing           │
         │   - Retry logic                │
         │   - DLQ for failures           │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │   XDaemon                      │
         │   (x_daemon.py)                │
         │   - Browser automation         │
         │   - Post to X                  │
         │   - Safety checks              │
         └────────────────────────────────┘
```

### File Locations:
- **Aggregation:** `intel/aggregator.py` Lines 50-100
- **AI Processing:** `intel/ai_processor.py` Lines 150-250
- **Approval:** `approval_manager.py` Lines 100-200
- **Queue:** `task_queue.py` Lines 100-300
- **Posting:** `x_daemon.py` Lines 200-400

---

## 📖 API Reference

### Quick Function Finder

#### Content Aggregation
```python
# Fetch all content
from intel.aggregator import aggregator
items = await aggregator.fetch_all()                    # aggregator.py:50

# Get top items
top_items = aggregator.get_top_items(items, n=10)      # aggregator.py:100

# Filter by category
ai_items = aggregator.filter_by_category(               # aggregator.py:150
    items, 
    ContentCategory.AI_ML
)
```

#### AI Tweet Generation
```python
# Process single item
from intel.ai_processor import ai_processor
processed = await ai_processor.process_item(item)      # ai_processor.py:150

# Batch processing
processed = await ai_processor.process_batch(           # ai_processor.py:250
    items,
    max_items=5
)

# Filter by quality
high_quality = ai_processor.filter_by_quality(          # ai_processor.py:350
    processed,
    ContentQuality.HIGH
)
```

#### Task Management
```python
# Add task
from task_queue import TaskQueue
queue = TaskQueue()
task_id = queue.add_task(                               # task_queue.py:100
    task_type="post_tweet",
    data={"content": "Hello X!"},
    priority=TaskPriority.HIGH
)

# Get stats
stats = queue.get_stats()                               # task_queue.py:250

# DLQ management
dlq_tasks = queue.get_dlq_tasks()                       # task_queue.py:300
queue.clear_dlq()                                       # task_queue.py:350
```

#### Posting
```python
# Post immediately
from orchestrator import Orchestrator
orch = Orchestrator()
result = await orch.post_now("Hello X!")                # orchestrator.py:250

# Schedule post
from post_scheduler import PostScheduler
scheduler = PostScheduler()
await scheduler.schedule_post("14:00", "Scheduled post") # post_scheduler.py:200
```

#### Monitoring
```python
# Health check
from health_check import health_checker
health = await health_checker.check_all()               # health_check.py:150

# Metrics
from metrics_collector import get_metrics_report
metrics = get_metrics_report()                          # metrics_collector.py:350
```

#### Logging
```python
# Structured logging
from structured_logger import task_logger
task_logger.info(                                       # structured_logger.py:100
    "Task completed",
    task_id="abc-123",
    duration=2.5
)
```

---

## 🔧 Troubleshooting Guide

### Common Issues & Solutions

#### 1. **Gemini API Not Working**
**Error:** `google.genai.errors.PermissionDenied`

**Location:** `intel/ai_processor.py` Line 80-100

**Solution:**
```python
# Check .env file
GEMINI_API_KEY=your_actual_key_here

# Verify in code
from config import get
print(get('GEMINI_API_KEY'))  # Should not be None

# Test API
from intel.ai_processor import ai_processor
print(ai_processor.model)  # Should show model instance
```

---

#### 2. **Browser Not Starting**
**Error:** `playwright._impl._api_types.Error: Browser closed`

**Location:** `chrome_pool.py` Line 80-150

**Solution:**
```bash
# Reinstall Playwright browsers
python -m playwright install chromium

# Check ChromePool
from chrome_pool import ChromePool
pool = ChromePool()
browser = await pool.get_browser()  # Should not error
```

---

#### 3. **Tasks Stuck in Queue**
**Error:** Tasks in PENDING state forever

**Location:** `task_queue.py` Line 100-200

**Solution:**
```python
# Check if queue is running
from task_queue import TaskQueue
queue = TaskQueue()
print(queue._running)  # Should be True

# Start queue if not running
await queue.start()

# Check queue stats
stats = queue.get_stats()
print(stats)  # Shows queue size, processing
```

---

#### 4. **Telegram Auth Failed**
**Error:** `telethon.errors.SessionPasswordNeededError`

**Location:** `intel/telegram_source.py` Line 80-120

**Solution:**
```python
# Set 2FA password in .env
TELEGRAM_2FA_PASSWORD=your_password

# Or manually authenticate
from intel.telegram_source import telegram_source
await telegram_source.initialize()
# Enter code when prompted
```

---

#### 5. **High Quality Tweets Not Generated**
**Issue:** All tweets rated LOW quality

**Location:** `intel/ai_processor.py` Line 200-350

**Debug:**
```python
# Check quality scoring
from intel.ai_processor import ai_processor
processed = await ai_processor.process_item(item)
print(f"Quality: {processed.quality}")
print(f"Relevance: {processed.relevance_score}")
print(f"Engagement: {processed.engagement_score}")

# Check prompt
prompt = ai_processor._build_turkish_prompt(item)
print(prompt)  # Verify prompt is correct
```

**Solution:** Adjust quality thresholds in `ai_processor.py` Line 220-240

---

#### 6. **DLQ Filling Up**
**Issue:** Many tasks in Dead Letter Queue

**Location:** `task_queue.py` Line 300-350

**Debug:**
```python
# Check DLQ
from task_queue import TaskQueue
queue = TaskQueue()
dlq_tasks = queue.get_dlq_tasks()

for task in dlq_tasks:
    print(f"Task: {task.id}")
    print(f"Type: {task.type}")
    print(f"Error: {task.error}")
    print(f"Attempts: {task.attempts}")
```

**Solution:** Fix underlying errors, then retry DLQ tasks

---

#### 7. **Rate Limit Errors**
**Error:** `429 Too Many Requests` from X

**Location:** `rate_limiter.py` Line 50-150

**Solution:**
```python
# Check rate limits
from rate_limiter import rate_limiter
status = rate_limiter.get_status()
print(status)  # Shows current usage

# Increase delays
# Edit config.py Line 250
MIN_DELAY = 60  # seconds between posts
```

---

#### 8. **Memory Usage High**
**Issue:** Worker using > 500MB RAM

**Location:** `health_check.py` Line 250-300

**Debug:**
```python
# Check health report
from health_check import health_checker
health = await health_checker.check_all()
print(health['system']['memory_mb'])
```

**Solution:**
```python
# Close browser when not in use
from chrome_pool import ChromePool
pool = ChromePool()
await pool.close()

# Clear metrics periodically
from metrics_collector import metrics_collector
metrics_collector.reset()
```

---

### Debug Mode

Enable detailed logging:
```python
# In .env
DEBUG=true
LOG_LEVEL=DEBUG

# In code
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📚 Additional Resources

### Key Documentation Files
- `README.md` - Project overview and setup
- `AI_CONTENT_GENERATOR_SETUP.md` - AI system setup guide
- `IMPLEMENTATION_SUMMARY.md` - Implementation details
- `.env.example` - Configuration template

### External Documentation
- **Playwright:** https://playwright.dev/python/
- **Google Gemini:** https://ai.google.dev/docs
- **Telethon:** https://docs.telethon.dev/
- **APScheduler:** https://apscheduler.readthedocs.io/
- **python-telegram-bot:** https://docs.python-telegram-bot.org/

### Contact & Support
- **Repository:** https://github.com/asmeril/X-Hive
- **Issues:** https://github.com/asmeril/X-Hive/issues

---

## 📈 Performance Benchmarks

### Typical Performance Metrics

**Content Aggregation:**
- GitHub Trending: ~2-3 seconds (25 repos)
- RSS Feeds: ~1-2 seconds (50 items)
- Telegram: ~3-5 seconds (50 messages)
- **Total aggregation: ~10-15 seconds**

**AI Processing:**
- Single tweet generation: ~5-10 seconds
- Batch (5 items): ~30-45 seconds
- Quality >= HIGH: ~60% of tweets

**Task Queue:**
- Task throughput: ~10-20 tasks/minute
- Queue processing delay: < 1 second
- DLQ rate: < 5%

**Browser Operations:**
- Login: ~15-20 seconds
- Post tweet: ~10-15 seconds
- Browser startup: ~3-5 seconds

---

## 🎯 Quick Reference Card

### Essential Commands
```bash
# Start system
python run.py

# Test full system
python test_full_system.py

# Generate tweets
python test_ai_processor.py

# Check health
python -c "from health_check import health_checker; import asyncio; print(asyncio.run(health_checker.check_all()))"

# View metrics
python -c "from metrics_collector import get_metrics_report; import json; print(json.dumps(get_metrics_report(), indent=2))"
```

### Most Used Imports
```python
# Core system
from orchestrator import Orchestrator

# Intel system
from intel.aggregator import aggregator
from intel.ai_processor import ai_processor

# Task management
from task_queue import TaskQueue

# Monitoring
from health_check import health_checker
from metrics_collector import get_metrics_report

# Logging
from structured_logger import task_logger
```

---

**Index Maintained By:** X-Hive Development Team  
**Last Review Date:** 6 Şubat 2026  
**Next Review:** Before v2.0.0 release

---

*This index is automatically generated and maintained. For updates, please modify source code comments and run the index generator.*
