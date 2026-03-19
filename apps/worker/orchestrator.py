import asyncio
import sys
import logging
import json
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Set
from dataclasses import dataclass, field

# Windows fix for Playwright subprocess on Python 3.12+ (must be before chrome_pool import)
# Python 3.12+ changed asyncio subprocess handling, try ProactorEventLoopPolicy first
if sys.platform == "win32" and sys.version_info >= (3, 12):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Import all systems
from chrome_pool import ChromePool
from task_queue import TaskQueue, TaskItem, TaskStatus
from ai_content_generator import AIContentGenerator
from post_scheduler import PostScheduler
from approval_manager import ApprovalManager, OperationType
from health_check import health_checker
from metrics_collector import metrics_collector, increment_counter, record_timing
from structured_logger import task_logger
from approval.approval_queue import approval_queue

# Intel sources
from intel.github_source import GitHubTrendingSource
from intel.google_trends_source import GoogleTrendsSource
from intel.hackernews_source import HackerNewsSource
from intel.reddit_source import RedditSource
from intel.producthunt_source import ProductHuntSource
from intel.twitter_source import TwitterSource
from intel.arxiv_source import ArxivSource
from intel.huggingface_source import huggingface_source
from intel.substack_scraper import SubstackScraper
from intel.perplexity_scraper import PerplexityScraper
from intel.youtube_source import YouTubeSource
from intel.linkedin_source import LinkedInSource

# Visibility & Distribution Engine
from visibility_engine import enrich_batch
from intel.base_source import ContentItem, ContentCategory

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    """Orchestrator configuration"""

    # Scheduling
    posts_per_day: int = 3
    post_times: list = field(default_factory=lambda: ["09:00", "14:00", "20:00"])

    # Intel Collection
    intel_enabled: bool = True
    intel_interval_hours: int = 6  # Collect intel every 6 hours
    intel_sources: list = field(default_factory=lambda: [
        "github", "google_trends", "hackernews", "reddit", "producthunt",
        "arxiv", "huggingface", "substack", "perplexity", "telegram"
        # twitter: cookie gerektirir; youtube/linkedin: güvenilir değil
    ])

    # AI Generation
    ai_enabled: bool = True
    ai_topics: list = field(default_factory=lambda: [
        "Yapay zeka ve otomasyon",
        "Verimlilik ipuçları",
        "Teknoloji inovasyonu"
    ])
    ai_style: str = "professional"

    # Approval
    require_approval: bool = False  # Set to True when ApprovalManager is available
    auto_approve_after_minutes: int = 60

    # Health monitoring
    health_check_interval_minutes: int = 5


class Orchestrator:
    """
    Main orchestrator coordinating all X-Hive systems.

    Responsibilities:
    - Schedule daily posts
    - Generate AI content
    - Execute approved posts
    - Monitor system health
    - Collect metrics
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """
        Initialize orchestrator.

        Args:
            config: Orchestrator configuration
        """

        self.config = config or OrchestratorConfig()

        # ─── Seen-URL persistent store ───────────────────────────────────────
        # Her işlenmiş URL burada saklanır; bir sonraki taramada tekrar eklenmez.
        self._seen_urls_file = Path("data/seen_urls.json")
        self._seen_urls_file.parent.mkdir(parents=True, exist_ok=True)
        self._seen_urls: Dict[str, str] = self._load_seen_urls()  # {url: iso_timestamp}
        self._seen_url_ttl_days = 14  # 14 günden eski kayıtları otomatik temizle
        logger.info(f"📌 Seen-URL store: {len(self._seen_urls)} URLs tracked")

        # ─── Persistent intel memory (raw journal + urgent watchlist) ────────
        self._intel_raw_journal_file = Path("data/intel_raw_journal.jsonl")
        self._intel_raw_journal_file.parent.mkdir(parents=True, exist_ok=True)
        self._watchlist_file = Path("data/urgent_watchlist.json")
        self._watchlist_file.parent.mkdir(parents=True, exist_ok=True)
        self._watchlist_ttl_hours = 72
        self._urgent_watchlist: Dict[str, Dict[str, Any]] = self._load_watchlist()
        logger.info(f"📌 Urgent watchlist loaded: {len(self._urgent_watchlist)} URLs")

        # Initialize components
        self.chrome_pool = ChromePool()
        self.task_queue = TaskQueue()
        self.ai_generator = AIContentGenerator()
        
        # Create a custom post generator for the scheduler that pulls from our intel queue
        def _get_intel_based_post(time_period: str) -> str:
            from approval.approval_queue import approval_queue
            
            # Try to find a pending item in the approval queue
            queue_items = list(approval_queue.items.values())
            
            # Sadece onaylanan (APPROVED) veya beklemede olan (PENDING) veriyi al.
            pending_items = []
            for i in queue_items:
                status_val = i.status.value if hasattr(i.status, "value") else str(i.status)
                if status_val in ["approved", "pending"]:
                    pending_items.append(i)
            
            if pending_items:
                # Ilk uygun tweedi sec
                item = pending_items[0]
                text = item.generated_tweet
                
                # Mark as processed so we don't repeat it
                # status propertysi Enum oldugu icin string yerine degeri isleyelim veya dogrudan string atayalim.
                # Eger atama hatasi verirse diye hasattr kontrolu.
                from approval.approval_queue import ApprovalStatus
                item.status = ApprovalStatus("processed") if "processed" in [e.value for e in ApprovalStatus] else "processed"
                approval_queue._save()
                
                logger.info(f"📥 Using intel-based post from queue: {text[:50]}...")
                return text
                
            # Fallback if no intel is available
            greetings = {
                "morning": "🌅 Good morning! Starting the day with X-Hive automated updates. Let's make today productive!",
                "afternoon": "☀️ Good afternoon! Mid-day check-in from X-Hive. Keep pushing forward!",
                "evening": "🌙 Good evening! Wrapping up the day with X-Hive insights. Stay tuned for more tomorrow!"
            }
            return greetings.get(time_period, greetings["afternoon"])

        self.scheduler = PostScheduler(content_generator_func=_get_intel_based_post)
        self.approval_manager = ApprovalManager(
            timeout_seconds=self.config.auto_approve_after_minutes * 60
        )

        # State
        self._running = False
        self._health_check_task: Optional[asyncio.Task] = None
        self.last_intel_collection: Optional[datetime] = None
        self._intel_run_lock = asyncio.Lock()

        logger.info("🎯 Orchestrator initialized")

    async def start(self) -> None:
        """Start the orchestrator and all subsystems"""

        if self._running:
            logger.warning("⚠️ Orchestrator already running")
            return

        logger.info("🚀 Starting X-Hive Orchestrator...")

        try:
            # Set approval mode based on config
            if self.config.require_approval:
                self.approval_manager.set_mode('REQUIRED')
                logger.info("✋ Approval mode: REQUIRED")
            else:
                self.approval_manager.set_mode('DISABLED')
                logger.info("✋ Approval mode: DISABLED")

            # Start task queue (auto-starts ChromePool)
            await self.task_queue.start()

            # Start post scheduler
            await self.scheduler.start()

            # Start health monitoring
            self._health_check_task = asyncio.create_task(
                self._health_monitor_loop()
            )

            self._running = True

            logger.info("✅ Orchestrator started successfully")
            task_logger.info(
                "Orchestrator started",
                posts_per_day=self.config.posts_per_day,
                post_times=self.config.post_times,
                ai_enabled=self.config.ai_enabled,
                approval_mode=self.approval_manager.mode
            )

        except Exception as e:
            logger.error(f"❌ Failed to start orchestrator: {e}")
            raise

    async def stop(self) -> None:
        """Stop the orchestrator and all subsystems"""

        if not self._running:
            return

        logger.info("🛑 Stopping X-Hive Orchestrator...")

        # Stop health monitoring
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # Stop subsystems
        await self.scheduler.stop()
        await self.task_queue.stop()

        self._running = False

        logger.info("✅ Orchestrator stopped")
        task_logger.info("Orchestrator stopped")

    async def run(self) -> None:
        """
        Main orchestrator loop - keeps running in background.
        Handles:
        - Auto-start on first run
        - Intel collection every N hours
        - AI content generation
        - Post scheduling
        - Continuous operation
        - Graceful error handling
        """
        logger.info("🔄 Orchestrator run() loop started")
        
        # Start orchestrator if not already running
        if not self._running:
            await self.start()
        
        # Start intel collection task
        if self.config.intel_enabled:
            intel_task = asyncio.create_task(self._intel_collection_loop())
            logger.info(f"📡 Intel collection started (every {self.config.intel_interval_hours}h)")
        
        # Keep running until stopped
        try:
            while self._running:
                await asyncio.sleep(60)  # Check every minute
        except asyncio.CancelledError:
            logger.info("🛑 Orchestrator run() loop cancelled")
            if self.config.intel_enabled:
                intel_task.cancel()
        except Exception as e:
            logger.error(f"❌ Orchestrator run() loop error: {e}")
            raise
    
    async def _intel_collection_loop(self) -> None:
        """Background task for periodic intel collection"""
        while self._running:
            try:
                logger.info("📡 Starting periodic intel collection cycle...")
                self.last_intel_collection = datetime.now()
                await self.run_intel_collection_once()
                # Wait for next cycle
                await asyncio.sleep(self.config.intel_interval_hours * 3600)

            except asyncio.CancelledError:
                logger.info("🛑 Intel collection loop cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in intel collection loop: {e}")
                await asyncio.sleep(600)  # Retry after 10 minutes

    def _load_seen_urls(self) -> Dict[str, str]:
        """Disk'ten seen-URL kayıtlarını yükler."""
        try:
            if self._seen_urls_file.exists():
                return json.loads(self._seen_urls_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"⚠️ seen_urls.json okunamadı, temiz başlanıyor: {e}")
        return {}

    def _save_seen_urls(self) -> None:
        """Seen-URL kayıtlarını disk'e yazar ve eski girişleri temizler."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self._seen_url_ttl_days)).isoformat()
        self._seen_urls = {u: t for u, t in self._seen_urls.items() if t >= cutoff}
        try:
            self._seen_urls_file.write_text(
                json.dumps(self._seen_urls, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"❌ seen_urls.json kaydedilemedi: {e}")

    def _mark_urls_seen(self, urls: list) -> None:
        """Verilen URL'leri seen-store'a ekler ve kaydeder."""
        now = datetime.now(timezone.utc).isoformat()
        for url in urls:
            if url:
                self._seen_urls[url] = now
        self._save_seen_urls()

    def _filter_seen(self, items: list) -> list:
        """Daha önce işlenmiş URL'lere sahip item'ları döndürülen listeden çıkarır."""
        fresh = [item for item in items if item.url not in self._seen_urls]
        skipped = len(items) - len(fresh)
        if skipped:
            logger.info(f"🔁 {skipped} item zaten işlenmiş (seen-URL), atlandı")
        return fresh

    def _compute_urgency_score(self, item) -> float:
        """Time-sensitive öncelik skoru (0-10)."""
        title = (getattr(item, "title", "") or "").lower()
        source = (getattr(item, "source_name", "") or "").lower()
        source_type = (getattr(item, "source_type", "") or "").lower()
        relevance = float(getattr(item, "relevance_score", 0.0) or 0.0)
        engagement = float(getattr(item, "engagement_score", 0.0) or 0.0)

        score = relevance * 4.0 + engagement * 3.0

        hot_terms = [
            "breaking", "urgent", "hack", "breach", "ban", "lawsuit", "leak",
            "launch", "release", "acquire", "funding", "openai", "google", "meta",
            "nvidia", "bitcoin", "ethereum", "regulation", "security"
        ]
        if any(term in title for term in hot_terms):
            score += 1.8

        # Newsy/fast streams deserve slight priority boost.
        if source_type in {"telegram", "reddit", "hackernews", "google_trends"}:
            score += 0.6

        if any(ch.isdigit() for ch in title):
            score += 0.4

        published_at = getattr(item, "published_at", None)
        if isinstance(published_at, datetime):
            dt = published_at if published_at.tzinfo else published_at.replace(tzinfo=timezone.utc)
            age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
            if age_hours <= 2:
                score += 1.2
            elif age_hours <= 8:
                score += 0.6

        if "telegram" in source or "trend" in source:
            score += 0.3

        return max(0.0, min(10.0, score))

    def _item_to_journal_record(self, item) -> Dict[str, Any]:
        category_raw = getattr(item, "category", None)
        if hasattr(category_raw, "value"):
            category_raw = category_raw.value

        published_at = getattr(item, "published_at", None)
        published_iso = published_at.isoformat() if isinstance(published_at, datetime) else None

        return {
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "title": getattr(item, "title", "") or "",
            "url": getattr(item, "url", "") or "",
            "source_type": getattr(item, "source_type", "") or "",
            "source_name": getattr(item, "source_name", "") or "",
            "description": getattr(item, "description", "") or "",
            "ai_summary": getattr(item, "ai_summary", "") or "",
            "category": category_raw or "",
            "published_at": published_iso,
            "relevance_score": float(getattr(item, "relevance_score", 0.0) or 0.0),
            "engagement_score": float(getattr(item, "engagement_score", 0.0) or 0.0),
            "urgency_score": self._compute_urgency_score(item),
        }

    def _append_raw_journal(self, items: list) -> None:
        if not items:
            return
        try:
            with self._intel_raw_journal_file.open("a", encoding="utf-8") as f:
                for item in items:
                    rec = self._item_to_journal_record(item)
                    if rec["url"]:
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"❌ intel_raw_journal write failed: {e}")

    def _load_watchlist(self) -> Dict[str, Dict[str, Any]]:
        try:
            if self._watchlist_file.exists():
                data = json.loads(self._watchlist_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
        except Exception as e:
            logger.warning(f"⚠️ urgent_watchlist.json okunamadı, temiz başlanıyor: {e}")
        return {}

    def _save_watchlist(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self._watchlist_ttl_hours)
        pruned: Dict[str, Dict[str, Any]] = {}

        for url, rec in self._urgent_watchlist.items():
            if url in self._seen_urls:
                continue
            last_seen_raw = rec.get("last_seen")
            try:
                last_seen = datetime.fromisoformat(last_seen_raw) if last_seen_raw else cutoff
                if last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=timezone.utc)
            except Exception:
                last_seen = cutoff
            if last_seen >= cutoff:
                pruned[url] = rec

        self._urgent_watchlist = pruned
        try:
            self._watchlist_file.write_text(
                json.dumps(self._urgent_watchlist, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"❌ urgent_watchlist save failed: {e}")

    def _update_urgent_watchlist(self, items: list, min_score: float = 6.5) -> None:
        if not items:
            return

        now = datetime.now(timezone.utc).isoformat()
        changed = 0
        for item in items:
            url = getattr(item, "url", "") or ""
            if not url or url in self._seen_urls:
                continue

            urgency = self._compute_urgency_score(item)
            if urgency < min_score:
                continue

            rec = self._item_to_journal_record(item)
            rec["first_seen"] = now
            rec["last_seen"] = now
            rec["hits"] = 1

            existing = self._urgent_watchlist.get(url)
            if existing:
                rec["first_seen"] = existing.get("first_seen", now)
                rec["hits"] = int(existing.get("hits", 0) or 0) + 1
                rec["urgency_score"] = max(float(existing.get("urgency_score", 0.0) or 0.0), urgency)

            self._urgent_watchlist[url] = rec
            changed += 1

        if changed:
            logger.info(f"📌 Urgent watchlist updated: +{changed} entries")
            self._save_watchlist()

    def _build_content_item_from_watchlist(self, rec: Dict[str, Any]) -> ContentItem:
        published = None
        raw_pub = rec.get("published_at")
        if raw_pub:
            try:
                published = datetime.fromisoformat(raw_pub)
            except Exception:
                published = None

        category_raw = rec.get("category")
        try:
            category = ContentCategory(category_raw) if category_raw else ContentCategory.OTHER
        except Exception:
            category = ContentCategory.OTHER

        item = ContentItem(
            title=rec.get("title", ""),
            url=rec.get("url", ""),
            source_type=rec.get("source_type", "watchlist"),
            source_name=rec.get("source_name", "Urgent Watchlist"),
            description=rec.get("description", ""),
            published_at=published,
            category=category,
            relevance_score=float(rec.get("relevance_score", 0.0) or 0.0),
            engagement_score=float(rec.get("engagement_score", 0.0) or 0.0),
        )
        item.ai_summary = rec.get("ai_summary", "") or ""
        return item

    def _get_watchlist_replay_candidates(self, limit: int = 6, min_score: float = 7.2) -> list:
        candidates = []
        for url, rec in self._urgent_watchlist.items():
            if url in self._seen_urls:
                continue
            urgency = float(rec.get("urgency_score", 0.0) or 0.0)
            if urgency < min_score:
                continue
            candidates.append((urgency, rec.get("last_seen", ""), rec))

        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        replay_items = [self._build_content_item_from_watchlist(rec) for _, _, rec in candidates[:limit]]
        if replay_items:
            logger.info(f"🔁 Watchlist replay candidates: {len(replay_items)}")
        return replay_items

    def _remove_from_watchlist(self, urls: list) -> None:
        removed = 0
        for url in urls:
            if url and url in self._urgent_watchlist:
                del self._urgent_watchlist[url]
                removed += 1
        if removed:
            logger.info(f"🧹 Urgent watchlist cleaned: -{removed} processed URLs")
            self._save_watchlist()

    async def run_intel_collection_once(self) -> Dict[str, Any]:
        if self._intel_run_lock.locked():
            logger.warning("⚠️ Intel collection already in progress, skipping overlapping request")
            return {"status": "busy", "message": "intel collection already running"}

        async with self._intel_run_lock:
            return await self._run_intel_collection_once_impl()

    async def _run_intel_collection_once_impl(self) -> Dict[str, Any]:
        logger.info("📡 Running intel collection pass...")
        all_items = []
        
        try:
            if "github" in self.config.intel_sources:
                try:
                    github = GitHubTrendingSource(language="python", max_repos=3)
                    items = await asyncio.wait_for(github.fetch_latest(), timeout=30.0)
                    all_items.extend(items)
                    logger.info(f"✅ GitHub: {len(items)} items collected")
                except Exception as e:
                    logger.error(f"❌ Error collecting from GitHub: {e}")

            if "google_trends" in self.config.intel_sources:
                try:
                    trends = GoogleTrendsSource()
                    items = await asyncio.wait_for(trends.fetch_latest(), timeout=30.0)
                    items = items[:3]
                    all_items.extend(items)
                    logger.info(f"✅ Google Trends: {len(items)} items collected")
                except Exception as e:
                    logger.error(f"❌ Error collecting from Google Trends: {e}")

            if "hackernews" in self.config.intel_sources:
                try:
                    hn = HackerNewsSource(limit=3)
                    items = await asyncio.wait_for(hn.fetch_latest(), timeout=20.0)
                    all_items.extend(items)
                    logger.info(f"✅ HackerNews: {len(items)} items collected")
                except Exception as e:
                    logger.error(f"❌ Error collecting from HackerNews: {e}")

            if "reddit" in self.config.intel_sources:
                try:
                    reddit = RedditSource(limit=5)
                    items = await asyncio.wait_for(reddit.fetch_latest(), timeout=45.0)
                    all_items.extend(items)
                    logger.info(f"✅ Reddit: {len(items)} items collected")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Reddit: Timeout 45s (atlandı)")
                except Exception as e:
                    logger.warning(f"⚠️ Reddit bağlanamadı (atlandı): {e}")

            if "producthunt" in self.config.intel_sources:
                try:
                    ph = ProductHuntSource(limit=10)
                    items = await asyncio.wait_for(ph.fetch_latest(), timeout=20.0)
                    all_items.extend(items)
                    logger.info(f"✅ ProductHunt: {len(items)} items collected")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ ProductHunt: Timeout 20s")
                except Exception as e:
                    logger.error(f"❌ Error collecting from ProductHunt: {e}")

            if "twitter" in self.config.intel_sources:
                try:
                    ts = TwitterSource(tweets_per_influencer=3)
                    items = await asyncio.wait_for(ts.fetch_latest(), timeout=15.0)
                    all_items.extend(items)
                    logger.info(f"✅ Twitter: {len(items)} items collected")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Twitter: Timeout 15s (atlandı)")
                except Exception as e:
                    logger.warning(f"⚠️ Twitter bağlanamadı (atlandı): {e}")

            if "arxiv" in self.config.intel_sources:
                try:
                    arx = ArxivSource(max_results=20)
                    items = await asyncio.wait_for(arx.fetch_latest(), timeout=20.0)
                    all_items.extend(items[:8])
                    logger.info(f"✅ Arxiv: {len(items[:8])} items collected")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Arxiv: Timeout 20s")
                except Exception as e:
                    logger.error(f"❌ Error collecting from Arxiv: {e}")

            if "huggingface" in self.config.intel_sources:
                try:
                    items = await asyncio.wait_for(huggingface_source.fetch_latest(), timeout=20.0)
                    all_items.extend(items[:8])
                    logger.info(f"✅ HuggingFace: {len(items[:8])} items collected")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ HuggingFace: Timeout 20s")
                except Exception as e:
                    logger.error(f"❌ Error collecting from HuggingFace: {e}")

            if "substack" in self.config.intel_sources:
                try:
                    sub = SubstackScraper()
                    items = await asyncio.wait_for(sub.fetch_latest(), timeout=15.0)
                    all_items.extend(items[:5])
                    logger.info(f"✅ Substack: {len(items[:5])} items collected")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Substack: Timeout 15s (atlandı)")
                except Exception as e:
                    logger.warning(f"⚠️ Substack bağlanamadı (atlandı): {e}")

            if "perplexity" in self.config.intel_sources:
                try:
                    px = PerplexityScraper()
                    items = await asyncio.wait_for(px.fetch_latest(), timeout=15.0)
                    all_items.extend(items[:5])
                    logger.info(f"✅ Perplexity: {len(items[:5])} items collected")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Perplexity: Timeout 15s (atlandı)")
                except Exception as e:
                    logger.warning(f"⚠️ Perplexity bağlanamadı (atlandı): {e}")

            if "youtube" in self.config.intel_sources:
                try:
                    yt = YouTubeSource()
                    items = await asyncio.wait_for(yt.fetch_latest(), timeout=15.0)
                    all_items.extend(items[:5])
                    logger.info(f"✅ YouTube: {len(items[:5])} items collected")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ YouTube: Timeout 15s (atlandı)")
                except Exception as e:
                    logger.warning(f"⚠️ YouTube bağlanamadı (atlandı): {e}")

            if "linkedin" in self.config.intel_sources:
                try:
                    li = LinkedInSource()
                    items = await asyncio.wait_for(li.fetch_latest(), timeout=15.0)
                    all_items.extend(items[:5])
                    logger.info(f"✅ LinkedIn: {len(items[:5])} items collected")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ LinkedIn: Timeout 15s (atlandı)")
                except Exception as e:
                    logger.warning(f"⚠️ LinkedIn bağlanamadı (atlandı): {e}")

            if "telegram" in self.config.intel_sources:
                tg_source = None
                try:
                    from intel.telegram_source import telegram_source
                    tg_source = telegram_source
                    if not tg_source:
                        raise RuntimeError("Telegram source not initialized")
                    items = await asyncio.wait_for(tg_source.fetch_latest(limit=5), timeout=30.0)
                    all_items.extend(items)
                    logger.info(f"✅ Telegram: {len(items)} items collected")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Telegram: Timeout 30s (atlandı)")
                except Exception as e:
                    logger.warning(f"⚠️ Telegram intel skipped: {e}")
                finally:
                    if tg_source:
                        try:
                            await tg_source.disconnect()
                        except Exception as disc_err:
                            logger.debug(f"Telegram disconnect skipped: {disc_err}")

            # Persist all collected signals before selection (for missed-opportunity replay).
            self._append_raw_journal(all_items)
            self._update_urgent_watchlist(all_items)

            # ─── VIRAL SCORING & THREAD GENERATION PIPELINE ───
            if self.config.ai_enabled:
                # Daha önce işlenmiş URL'leri çıkar
                fresh_items = self._filter_seen(all_items)

                # High-urgency replay: bu turda kaynaklardan gelmese bile watchlist'ten yeniden dene.
                replay_items = self._get_watchlist_replay_candidates(limit=6, min_score=7.2)
                if replay_items:
                    fresh_urls = {i.url for i in fresh_items if getattr(i, "url", "")}
                    replay_new = [i for i in replay_items if i.url not in fresh_urls]
                    if replay_new:
                        logger.info(f"⏱️ Added {len(replay_new)} replay items from urgent watchlist")
                        fresh_items.extend(replay_new)

                if not fresh_items:
                    logger.info("ℹ️ Tüm toplanan içerikler zaten işlenmiş, yeni tarama gerekli değil.")
                    return {"status": "success", "items_collected": len(all_items), "fresh": 0}

                logger.info(f"🚀 Starting viral thread pipeline for {len(fresh_items)} fresh items (of {len(all_items)} collected)...")

                # Pending item'ları otomatik temizleme.
                # UI'da açık olan eski item id'leri kaybolup /approval/post-thread 404 üretiyordu.
                logger.info("ℹ️ Existing pending queue preserved (no clear_pending)")

                # AI: Viral skorla → En iyi N'ini seç → TR+EN thread üret
                try:
                    # Thread pipeline free-tier rate limits nedeniyle dakikalar sürebilir.
                    # 120s timeout gerçek çalışma süresinden kısa kaldığı için fallback'e düşüyordu.
                    pipeline_timeout = 7200.0
                    results = await asyncio.wait_for(
                        self.ai_generator.generate_viral_threads(fresh_items, top_n=3),
                        timeout=pipeline_timeout
                    )

                    # Visibility Enrichment timeout (image generation etc)
                    try:
                        results = await asyncio.wait_for(enrich_batch(results), timeout=60.0)
                        logger.info(f"🔍 Visibility enrichment complete for {len(results)} threads")
                    except Exception as ve:
                        logger.error(f"⚠️ Visibility enrichment failed (non-fatal): {ve}")
                    
                    for entry in results:
                        item = entry["item"]
                        viral_score = entry["viral_score"]
                        tr_thread = entry["tr_thread"]
                        en_thread = entry["en_thread"]
                        
                        # Thread olarak queue'ya ekle (with visibility data)
                        approval_queue.add_thread(
                            content_item=item,
                            viral_score=viral_score,
                            tr_thread=tr_thread,
                            en_thread=en_thread,
                            mentions=entry.get("mentions", []),
                            keywords=entry.get("keywords", []),
                            image_url=entry.get("image_url"),
                            sniper_targets=entry.get("sniper_targets", []),
                        )
                    
                    logger.info(f"🎉 Viral pipeline complete: {len(results)} threads queued for approval")

                    # ✅ İşlenen URL'leri seen-store'a kaydet (tekrar işlenmesini engeller)
                    processed_urls = [e["item"].url for e in results if e.get("item")]
                    self._mark_urls_seen(processed_urls)
                    self._remove_from_watchlist(processed_urls)

                    # 📲 Telegram bildirim: Thread'ler hazır
                    try:
                        from telegram_hub import get_telegram_hub
                        tg = get_telegram_hub()
                        if tg._running:
                            top_score = max(e["viral_score"] for e in results) if results else 0
                            await tg.notify_threads_ready(count=len(results), top_score=top_score)
                    except Exception as tg_err:
                        logger.debug(f"Telegram notification skipped: {tg_err}")
                except Exception as eval_err:
                    logger.error(
                        f"❌ Viral pipeline failed. No fallback content will be enqueued: {eval_err}",
                        exc_info=True,
                    )
                    # No-fallback policy: mevcut pending queue korunur,
                    # yeni düşük kaliteli içerik eklenmez ve seen_urls güncellenmez.

            logger.info(f"✅ Intel collection pass complete. {len(all_items)} items collected, fresh={len(fresh_items) if 'fresh_items' in dir() else len(all_items)}.")
            return {"status": "success", "items_collected": len(all_items)}

        except Exception as e:
            logger.error(f"❌ Fatal error during intel collection pass: {e}")
            return {"status": "error", "message": str(e), "items_collected": len(all_items)}

    async def create_approved_post(self, content: str) -> Dict[str, Any]:
        """Helper method to create post with approval workflow if needed"""
        try:
            # Request approval if required
            if self.config.require_approval:
                approved, reason = await self.approval_manager.request_approval(
                    operation_type=OperationType.POST,
                    payload={'content': content}
                )

                if not approved:
                    logger.warning(f"❌ Post rejected: {reason}")
                    increment_counter('posts_rejected')
                    return {'success': False, 'reason': reason}

            # Add to task queue
            task_id = await self.task_queue.add_task(
                task_type="post_tweet",
                payload={'content': content}
            )

            increment_counter('posts_approved')
            return {'success': True, 'task_id': task_id}

        except Exception as e:
            logger.error(f"❌ Post creation failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _health_monitor_loop(self) -> None:
        """Continuous health monitoring loop"""

        while self._running:
            try:
                # Run health checks
                health_report = await health_checker.check_all(
                    chrome_pool=self.chrome_pool,
                    task_queue=self.task_queue,
                    ai_generator=self.ai_generator
                )

                # Log health status
                overall_status = health_report['overall_status']

                if overall_status == 'healthy':
                    logger.debug("💚 System health: HEALTHY")
                elif overall_status == 'degraded':
                    logger.warning("💛 System health: DEGRADED")
                    task_logger.warning(
                        "System degraded",
                        components=health_report['components']
                    )
                else:
                    logger.error("❤️ System health: UNHEALTHY")
                    task_logger.error(
                        "System unhealthy",
                        components=health_report['components']
                    )

                # Wait for next check
                await asyncio.sleep(self.config.health_check_interval_minutes * 60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Health check error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute

    async def post_now(self, content: str) -> Dict[str, Any]:
        """
        Post immediately (bypass scheduling).

        Args:
            content: Post content

        Returns:
            Result dictionary
        """

        try:
            # Request approval if required
            if self.config.require_approval:
                approved, reason = await self.approval_manager.request_approval(
                    operation_type=OperationType.POST,
                    payload={'content': content, 'immediate': True}
                )

                if not approved:
                    logger.warning(f"❌ Immediate post rejected: {reason}")
                    return {'success': False, 'reason': reason}

            # Create immediate task
            task_id = await self.task_queue.add_task(
                task_type="post_tweet",
                payload={'content': content, 'immediate': True}
            )

            logger.info(f"✅ Immediate post queued (ID: {task_id})")
            increment_counter('posts_immediate')

            return {'success': True, 'task_id': task_id}

        except Exception as e:
            logger.error(f"❌ Immediate post failed: {e}")
            return {'success': False, 'error': str(e)}

    def get_status(self) -> Dict[str, Any]:
        """
        Get orchestrator status.

        Returns:
            Status dictionary
        """

        return {
            'running': self._running,
            'config': {
                'posts_per_day': self.config.posts_per_day,
                'post_times': self.config.post_times,
                'ai_enabled': self.config.ai_enabled,
                'require_approval': self.config.require_approval
            },
            'metrics': metrics_collector.get_metrics_report(),
            'health': health_checker.get_status_summary(),
            'last_intel_collection': self.last_intel_collection.isoformat() if self.last_intel_collection else None
        }


orchestrator = Orchestrator()


async def main():
    """Main entry point for X-Hive"""

    try:
        # Start orchestrator
        await orchestrator.start()

        # Keep running
        logger.info("🎯 X-Hive is running. Press Ctrl+C to stop.")

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("\n⚠️ Shutdown signal received")

    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(main())
