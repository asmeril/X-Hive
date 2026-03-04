"""
X-HIVE Worker - Main FastAPI Application
Enhanced with comprehensive safety systems.
"""

import asyncio
import sys
import io

# Force UTF-8 encoding for stdout/stderr on Windows to avoid Unicode errors
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List

# Core modules
from config import settings
from chrome_pool import ChromePool, shutdown_chrome_pool
from task_queue import TaskQueue, shutdown_task_queue
from x_daemon import XDaemon
from lock_manager import LockManager
from orchestrator import Orchestrator, OrchestratorConfig

# Safety modules (NEW)
from rate_limiter import get_rate_limiter, OperationType as RateLimiterOpType
from approval_manager import get_approval_manager, OperationType as ApprovalOpType
from safety_logger import get_safety_logger

# Approval queue for content items
from approval.approval_queue import approval_queue

# Global Orchestrator instance
from orchestrator import orchestrator as global_orchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────
# Lifespan Events (Startup/Shutdown)
# ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan events.
    
    Startup:
    - Show safety banner
    - Initialize Chrome Pool
    - Start Task Queue
    - Start X Daemon
    
    Shutdown:
    - Save safety data
    - Shutdown X Daemon
    - Shutdown Task Queue
    - Shutdown Chrome Pool
    """
    # ───────── STARTUP ─────────
    logger.info("🚀 X-HIVE Worker starting up...")
    
    # Show safety banner (CRITICAL - NEVER SKIP)
    safety_logger = get_safety_logger()
    try:
        safety_logger.print_startup_banner()
    except Exception as e:
        logger.warning(f"Safety banner display failed (non-critical): {e}")
    
    # Initialize rate limiter (loads history)
    rate_limiter = get_rate_limiter()
    logger.info("🛡️ Rate limiter initialized")
    
    # Initialize approval manager (loads history)
    approval_manager = get_approval_manager()
    logger.info("✋ Approval manager initialized")
    
    # Initialize Chrome Pool
    try:
        chrome_pool = ChromePool()
        await chrome_pool.initialize()
        logger.info("✅ Chrome pool initialized")
    except Exception as e:
        logger.error(f"❌ Chrome pool initialization failed: {e}")
        logger.warning("⚠️ Worker running without Chrome (limited functionality)")
    
    # Start Task Queue
    try:
        task_queue = TaskQueue()
        await task_queue.start()
        logger.info("✅ Task queue started")
    except Exception as e:
        logger.error(f"❌ Task queue start failed: {e}")
    
    # Start X Daemon (chrome_pool ve task_queue singleton olarak zaten üstte başlatıldı)
    # x_daemon.start() içinde "already running" guard var, çift init olmaz
    try:
        x_daemon = XDaemon()
        result = await x_daemon.start()
        logger.info(f"✅ X Daemon: {result.get('status', 'started')}")
    except Exception as e:
        logger.error(f"❌ X Daemon start failed: {e}")
    
    # Start Orchestrator (Main automation engine)
    try:
        global_orchestrator.config = OrchestratorConfig(
            # Posting schedule
            posts_per_day=3,
            post_times=["09:00", "14:00", "20:00"],

            # Intel collection
            intel_enabled=True,
            intel_interval_hours=6,  # Her 6 saatte bir içerik topla
            intel_sources=["github", "google_trends", "hackernews", "reddit", "producthunt", "twitter", "arxiv", "huggingface", "substack", "perplexity", "youtube", "linkedin", "telegram"],

            # AI content generation
            ai_enabled=True,

            # Approval system
            require_approval=True,  # Desktop UI'dan onay gerekli

            # Health monitoring
            health_check_interval_minutes=5
        )
        asyncio.create_task(global_orchestrator.run())
        logger.info("✅ Orchestrator started (full auto-pilot mode)")
        logger.info("📡 Intel collection: Every 6 hours")
        logger.info("🤖 AI generation: Enabled")
        logger.info("✋ Approval required: Yes (Desktop UI)")
        logger.info("📅 Post schedule: 09:00, 14:00, 20:00")
    except Exception as e:
        logger.error(f"❌ Orchestrator start failed: {e}")
    
    logger.info("🎉 X-HIVE Worker startup complete!")
    
    # Start Telegram Hub (notifications + mobile approval + channel broadcast)
    try:
        from telegram_hub import start_telegram_hub
        tg_ok = await start_telegram_hub()
        if tg_ok:
            logger.info("✅ Telegram Hub started (notifications + mobile approval + channel)")
        else:
            logger.warning("⚠️ Telegram Hub disabled (missing token or library)")
    except Exception as e:
        logger.warning(f"⚠️ Telegram Hub start failed (non-critical): {e}")
    
    # Check daily reminder
    safety_logger.check_daily_reminder()
    
    yield
    
    # ───────── SHUTDOWN ─────────
    logger.info("🛑 X-HIVE Worker shutting down...")
    
    # Stop Telegram Hub
    try:
        from telegram_hub import stop_telegram_hub
        await stop_telegram_hub()
        logger.info("✅ Telegram Hub stopped")
    except Exception as e:
        logger.error(f"Error stopping Telegram Hub: {e}")
    
    # Stop X Daemon
    try:
        x_daemon = XDaemon()
        await x_daemon.stop()
        logger.info("✅ X Daemon stopped")
    except Exception as e:
        logger.error(f"Error stopping X Daemon: {e}")
    
    # Stop Task Queue
    try:
        task_queue = TaskQueue()
        await task_queue.stop()
        logger.info("✅ Task queue stopped")
    except Exception as e:
        logger.error(f"Error stopping task queue: {e}")
    
    # Shutdown Chrome Pool
    try:
        await shutdown_chrome_pool()
        logger.info("✅ Chrome pool shutdown")
    except Exception as e:
        logger.error(f"Error shutting down Chrome pool: {e}")
    
    logger.info("👋 X-HIVE Worker shutdown complete")


# ─────────────────────────────────────────────────────────
# FastAPI App Initialization
# ─────────────────────────────────────────────────────────

app = FastAPI(
    title="X-HIVE Worker API",
    description="AI-powered X (Twitter) automation with comprehensive safety systems",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────
# Request Models
# ─────────────────────────────────────────────────────────

class TweetRequest(BaseModel):
    text: str
    images: Optional[List[str]] = None


class ReplyRequest(BaseModel):
    tweet_url: str
    text: str


class QuoteRequest(BaseModel):
    tweet_url: str
    text: str
    images: Optional[List[str]] = None


class LikeRequest(BaseModel):
    tweet_url: str


class RetweetRequest(BaseModel):
    tweet_url: str


class ApprovalActionRequest(BaseModel):
    request_id: str
    action: str  # "approve" or "reject"
    reason: Optional[str] = None


# ─────────────────────────────────────────────────────────
# Health & Status Endpoints
# ─────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "X-HIVE Worker API",
        "version": "2.0.0",
        "status": "running",
        "safety_systems": "active"
    }


@app.get("/health")
async def health_check():
    """Worker health check"""
    safety_logger = get_safety_logger()
    memorial = safety_logger.get_memorial_message()

    return {
        "status": "ok",
        "worker": "x-hive-worker",
        "lock_path": str(settings.LOCK_PATH),
        "data_path": str(settings.DATA_PATH),
        "safety_warning": memorial,
        "timestamp": "2026-01-22T00:00:00Z"
    }

@app.get("/system/status")
async def system_status():
    """Get overall status of all background services"""
    try:
        orch_status = global_orchestrator.get_status()
        
        # Chrome Pool
        chrome_pool = ChromePool()
        is_healthy = await chrome_pool.is_healthy()
        
        # Task Queue
        task_queue = TaskQueue()
        queue_stats = await task_queue.get_queue_status()
        
        # X Daemon
        x_daemon = XDaemon()
        daemon_status = await x_daemon.get_status()
        
        return {
            "status": "ok",
            "services": {
                "orchestrator": {
                    "running": orch_status.get("running", False),
                    "ai_enabled": orch_status.get("config", {}).get("ai_enabled", False),
                    "intel_enabled": True
                },
                "task_queue": {
                    "running": task_queue._running,
                    "stats": queue_stats
                },
                "chrome_pool": {
                    "running": chrome_pool._initialized,
                    "healthy": is_healthy
                },
                "x_daemon": daemon_status,
                "scheduler": {
                    "running": global_orchestrator.scheduler.is_running if hasattr(global_orchestrator, 'scheduler') else False
                }
            }
        }
    except Exception as e:
        logger.error(f"Error fetching system status: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/system/force-intel")
async def force_intel_collection(background_tasks: BackgroundTasks):
    """Manually triggers the orchestrator's intel collection process in the background."""
    if not global_orchestrator._running:
        return {"status": "error", "message": "Orkestratör çalışmıyor. Önce başlatmalısınız."}
    
    # Run the gathering process in background so API responds immediately
    background_tasks.add_task(global_orchestrator.run_intel_collection_once)
    return {
        "status": "ok", 
        "message": "Arka planda haber toplama manuel olarak başlatıldı. Onay ekranında sonuçları yakında görebilirsiniz."
    }

# ─────────────────────────────────────────────────────────
# Chrome Pool Endpoints
# ─────────────────────────────────────────────────────────

@app.get("/chrome/status")
async def chrome_status():
    """Get Chrome pool status"""
    chrome_pool = ChromePool()
    is_healthy = await chrome_pool.is_healthy()
    
    return {
        "status": "ok",
        "chrome_pool": {
            "initialized": chrome_pool._initialized,
            "healthy": is_healthy,
            "page_open": chrome_pool.page is not None,
            "cookie_path": str(chrome_pool.cookie_path)
        }
    }


@app.post("/chrome/restart")
async def chrome_restart():
    """Restart Chrome pool"""
    chrome_pool = ChromePool()
    await chrome_pool.restart()
    
    return {
        "status": "ok",
        "message": "Chrome pool restarted"
    }


# ─────────────────────────────────────────────────────────
# X Daemon Endpoints
# ─────────────────────────────────────────────────────────

@app.get("/daemon/status")
async def daemon_status():
    """Get X Daemon status"""
    x_daemon = XDaemon()
    status = await x_daemon.get_status()
    
    return {
        "status": "ok",
        "daemon": status
    }


@app.post("/daemon/start")
async def daemon_start():
    """Start X Daemon"""
    x_daemon = XDaemon()
    result = await x_daemon.start()
    
    return {
        "status": "ok",
        "daemon": result
    }


@app.post("/daemon/stop")
async def daemon_stop():
    """Stop X Daemon"""
    x_daemon = XDaemon()
    result = await x_daemon.stop()
    
    return {
        "status": "ok",
        "daemon": result
    }


@app.post("/daemon/restart")
async def daemon_restart():
    """Restart X Daemon"""
    x_daemon = XDaemon()
    result = await x_daemon.restart()
    
    return {
        "status": "ok",
        "daemon": result
    }



# ─────────────────────────────────────────────────────────
# X Operations Endpoints (Tweet, Reply, Like, Retweet, Quote)
# ─────────────────────────────────────────────────────────

@app.post("/x/post")
async def post_tweet(req: TweetRequest):
    """Post a tweet"""
    x_daemon = XDaemon()
    result = await x_daemon.post_tweet(text=req.text, images=req.images)
    
    return result


@app.post("/x/reply")
async def reply_tweet(req: ReplyRequest):
    """Reply to a tweet"""
    x_daemon = XDaemon()
    result = await x_daemon.reply_to_tweet(tweet_url=req.tweet_url, text=req.text)
    
    return result


@app.post("/x/quote")
async def quote_tweet(req: QuoteRequest):
    """Quote a tweet"""
    x_daemon = XDaemon()
    result = await x_daemon.quote_tweet(
        tweet_url=req.tweet_url,
        text=req.text,
        images=req.images
    )
    
    return result


@app.post("/x/like")
async def like_tweet(req: LikeRequest):
    """Like a tweet"""
    x_daemon = XDaemon()
    result = await x_daemon.like_tweet(tweet_url=req.tweet_url)
    
    return result


@app.post("/x/retweet")
async def retweet_tweet(req: RetweetRequest):
    """Retweet a tweet"""
    x_daemon = XDaemon()
    result = await x_daemon.retweet(tweet_url=req.tweet_url)
    
    return result


# ─────────────────────────────────────────────────────────
# Rate Limiter Endpoints (NEW)
# ─────────────────────────────────────────────────────────

@app.get("/safety/rate-limits")
async def get_rate_limits():
    """Get current rate limit usage for all operations"""
    rate_limiter = get_rate_limiter()
    stats = rate_limiter.get_all_stats()
    
    return {
        "status": "ok",
        "rate_limits": stats
    }


@app.get("/safety/rate-limits/{operation_type}")
async def get_rate_limit_by_type(operation_type: str):
    """Get rate limit usage for specific operation type"""
    try:
        op_type = RateLimiterOpType(operation_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid operation type: {operation_type}")
    
    rate_limiter = get_rate_limiter()
    stats = rate_limiter.get_usage_stats(op_type)
    
    return {
        "status": "ok",
        "operation_type": operation_type,
        "usage": stats
    }


@app.post("/safety/rate-limits/reset")
async def reset_rate_limits():
    """Reset rate limit history (USE WITH CAUTION)"""
    rate_limiter = get_rate_limiter()
    rate_limiter.reset_history()
    
    return {
        "status": "ok",
        "message": "⚠️ Rate limit history reset"
    }


# ─────────────────────────────────────────────────────────
# Approval Manager Endpoints (NEW)
# ─────────────────────────────────────────────────────────

@app.get("/approval/mode")
async def get_approval_mode():
    """Get current approval mode"""
    approval_manager = get_approval_manager()
    
    return {
        "status": "ok",
        "mode": approval_manager.mode
    }


@app.post("/approval/mode")
async def set_approval_mode(mode: str):
    """Set approval mode (DISABLED | OPTIONAL | REQUIRED)"""
    approval_manager = get_approval_manager()
    
    try:
        approval_manager.set_mode(mode.upper())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "status": "ok",
        "mode": approval_manager.mode
    }


@app.get("/approval/pending")
async def get_pending_approvals():
    """Get all pending content items in approval queue, sorted by viral_score desc"""
    try:
        pending = approval_queue.get_pending()
        
        # Viral skordan büyükten küçüğe sırala
        pending.sort(key=lambda x: x.viral_score, reverse=True)
        
        # Convert to dict format
        items = [item.to_dict() for item in pending]
        
        return {
            "status": "success",
            "data": {
                "items": items,
                "total": len(items)
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching pending items: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": {
                "items": [],
                "total": 0
            }
        }


@app.post("/approval/approve-all-threads")
async def approve_all_pending():
    """Approve all pending threads at once"""
    try:
        pending = approval_queue.get_pending()
        count = 0
        for item in pending:
            approval_queue.approve(item.tweet_id)
            count += 1
        return {"status": "success", "approved": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/approval/post-thread/{item_id}")
async def post_thread(item_id: str, background_tasks: BackgroundTasks):
    """
    Onaylanan thread'i X/Twitter'a yayınla.
    İlk tweeti atar, sonra reply chain olarak devam eder.
    Görsel varsa ilk tweet'e ekler.
    """
    try:
        if item_id not in approval_queue.items:
            raise HTTPException(status_code=404, detail=f"Thread not found: {item_id}")
        
        item = approval_queue.items[item_id]
        
        # Hangi dilde yayınlanacak (default: tr)
        thread = item.tr_thread if item.tr_thread else item.en_thread
        if not thread:
            return {"status": "error", "message": "Thread boş"}
        
        # Mention'ları ilk tweet'e ekle (doğal bir şekilde)
        if item.mentions:
            mention_text = " ".join(item.mentions[:2])  # Max 2 mention
            # İlk tweete mention'ları ekle
            thread[0] = f"{thread[0]}\n\n{mention_text}"
        
        async def _post_thread_chain():
            """Background'da thread'i X'e at"""
            x_daemon = XDaemon()
            previous_url = None
            first_tweet_url = None
            
            for i, tweet_text in enumerate(thread):
                try:
                    if i == 0:
                        # İlk tweet (görsel varsa ekle)
                        images = [item.image_url] if item.image_url else None
                        result = await x_daemon.post_tweet(text=tweet_text, images=images)
                        if result.get("success") and result.get("tweet_url"):
                            previous_url = result["tweet_url"]
                            first_tweet_url = result["tweet_url"]
                        logger.info(f"🐦 Thread tweet 1/{len(thread)} posted")
                    else:
                        # Reply chain
                        if previous_url:
                            result = await x_daemon.reply_to_tweet(
                                tweet_url=previous_url, text=tweet_text
                            )
                            if result.get("success") and result.get("tweet_url"):
                                previous_url = result["tweet_url"]
                        logger.info(f"🐦 Thread tweet {i+1}/{len(thread)} posted")
                    
                    # Tweet arası bekleme (X rate limit)
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    logger.error(f"❌ Thread tweet {i+1} failed: {e}")
                    break
            
            # Mark as processed
            from approval.approval_queue import ApprovalStatus
            item.status = ApprovalStatus.PROCESSED
            approval_queue._save()
            logger.info(f"✅ Thread fully posted: {item_id}")
            
            # 📲 Telegram bildirim + kanal yayını
            try:
                from telegram_hub import get_telegram_hub
                tg = get_telegram_hub()
                if tg._running:
                    await tg.notify_thread_posted(
                        title=item.content_item.title,
                        tweet_count=len(thread),
                        tweet_url=first_tweet_url or "",
                    )
                    await tg.broadcast_thread_to_channel(
                        title=item.content_item.title,
                        tr_thread=thread,
                        x_tweet_url=first_tweet_url or "",
                        image_url=item.image_url if hasattr(item, 'image_url') else None,
                        viral_score=item.viral_score,
                    )
            except Exception as tg_err:
                logger.debug(f"Telegram post notification skipped: {tg_err}")
        
        background_tasks.add_task(_post_thread_chain)
        
        return {
            "status": "success",
            "message": f"Thread yayınlanıyor ({len(thread)} tweet)",
            "item_id": item_id,
            "tweet_count": len(thread),
            "has_image": bool(item.image_url),
            "mentions": item.mentions,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Thread post failed: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/approval/sniper-reply/{item_id}")
async def sniper_reply(item_id: str, background_tasks: BackgroundTasks):
    """
    Bir thread'in konusuyla ilgili büyük hesapların son tweetlerine akıllı reply at.
    Sniper Reply: Onların trafiğinden otostop çekme stratejisi.
    """
    try:
        if item_id not in approval_queue.items:
            raise HTTPException(status_code=404, detail=f"Thread not found: {item_id}")
        
        item = approval_queue.items[item_id]
        
        if not item.sniper_targets:
            return {"status": "info", "message": "Bu içerik için sniper target bulunamadı"}
        
        # AI ile konuya özel akıllı reply'lar üret
        from ai_content_generator import get_ai_generator
        ai = get_ai_generator()
        
        async def _execute_sniper_replies():
            """Background'da sniper reply'ları çalıştır"""
            x_daemon = XDaemon()
            replies_sent = 0
            
            for target in item.sniper_targets[:3]:  # Max 3 reply
                try:
                    username = target["username"]
                    
                    # AI ile o hesabın konusuyla ilgili değer katan bir reply üret
                    reply_prompt = f"""
Sen X/Twitter'da viral reply yazan bir uzmansın.

@{username} ({target['name']}) hesabına, aşağıdaki konuyla ilgili DEĞER KATAN bir reply yaz.

Konu: {item.content_item.title}
Detay: {item.generated_tweet[:200]}

Reply kuralları:
- 200 karakteri geçme
- Yeni bir bilgi veya farklı bakış açısı ekle
- "Bunu da düşünmek lazım:" veya "İlginç bir detay:" gibi değer katan giriş
- SPAM GÖRÜNME, doğal ol
- 1 emoji max
- Link KOYMA (reply'da link spam sayılır)
- Sadece reply metnini döndür
"""
                    reply_text = await ai._generate_with_retry(reply_prompt, max_retries=2)
                    
                    # TODO: Gerçek implementasyon - target'ın son tweetini bul ve reply at
                    # Şimdilik loglayalım
                    logger.info(f"🎯 Sniper reply ready for @{username}: {reply_text[:80]}...")
                    replies_sent += 1
                    
                    await asyncio.sleep(5)  # Rate limit
                    
                except Exception as e:
                    logger.error(f"❌ Sniper reply to @{target['username']} failed: {e}")
            
            logger.info(f"🎯 Sniper reply preview complete: {replies_sent} hazır metin üretildi")
        
        background_tasks.add_task(_execute_sniper_replies)
        
        return {
            "status": "success",
            "message": f"Sniper reply simülasyonu başlatıldı ({len(item.sniper_targets[:3])} hedef)",
            "targets": [t["handle"] for t in item.sniper_targets[:3]],
            "mode": "preview_only",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Sniper reply failed: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/approval/approve/{item_id}")
async def approve_item(item_id: str):
    """Approve a content item in the approval queue"""
    try:
        success = approval_queue.approve(item_id)
        
        if not success:
            return {
                "status": "error",
                "message": f"Item not found: {item_id}"
            }
        
        return {
            "status": "success",
            "message": "Item approved successfully",
            "item_id": item_id,
            "action": "approved"
        }
    except Exception as e:
        logger.error(f"❌ Error approving item {item_id}: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/approval/reject/{item_id}")
async def reject_item(item_id: str):
    """Reject a content item in the approval queue"""
    try:
        success = approval_queue.reject(item_id)
        
        if not success:
            return {
                "status": "error",
                "message": f"Item not found: {item_id}"
            }
        
        return {
            "status": "success",
            "message": "Item rejected successfully",
            "item_id": item_id,
            "action": "rejected"
        }
    except Exception as e:
        logger.error(f"❌ Error rejecting item {item_id}: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/approval/action")
async def approval_action(req: ApprovalActionRequest):
    """Approve or reject an approval request"""
    approval_manager = get_approval_manager()
    
    if req.action.lower() == "approve":
        success = approval_manager.approve_request(req.request_id, req.reason)
    elif req.action.lower() == "reject":
        success = approval_manager.reject_request(req.request_id, req.reason)
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {req.action}")
    
    if not success:
        raise HTTPException(status_code=404, detail="Request not found or already resolved")
    
    return {
        "status": "ok",
        "action": req.action,
        "request_id": req.request_id
    }


@app.get("/approval/stats")
async def get_approval_stats():
    """Get approval statistics"""
    approval_manager = get_approval_manager()
    stats = approval_manager.get_statistics()
    
    return {
        "status": "ok",
        "statistics": stats
    }


@app.post("/approval/emergency-stop")
async def emergency_stop():
    """Activate emergency stop (halt all operations)"""
    approval_manager = get_approval_manager()
    approval_manager.emergency_stop()
    
    return {
        "status": "ok",
        "message": "🚨 EMERGENCY STOP ACTIVATED"
    }


@app.post("/approval/resume")
async def resume_operations():
    """Deactivate emergency stop"""
    approval_manager = get_approval_manager()
    approval_manager.resume()
    
    return {
        "status": "ok",
        "message": "▶️ Operations resumed"
    }


# ─────────────────────────────────────────────────────────
# Safety Logger Endpoints (NEW)
# ─────────────────────────────────────────────────────────

@app.get("/safety/memorial")
async def get_memorial_message():
    """Get ban incident memorial message"""
    safety_logger = get_safety_logger()
    message = safety_logger.get_memorial_message()
    
    return {
        "status": "ok",
        "memorial_message": message,
        "has_incidents": message is not None
    }


@app.get("/safety/weekly-report")
async def get_weekly_report():
    """Get weekly safety report"""
    safety_logger = get_safety_logger()
    report = safety_logger.generate_weekly_report()
    
    return {
        "status": "ok",
        "report": report
    }


@app.post("/safety/daily-reminder")
async def trigger_daily_reminder():
    """Manually trigger daily reminder (for testing)"""
    safety_logger = get_safety_logger()
    shown = safety_logger.check_daily_reminder()
    
    return {
        "status": "ok",
        "reminder_shown": shown
    }


# ─────────────────────────────────────────────────────────
# Task Queue Endpoints (Existing - kept for compatibility)
# ─────────────────────────────────────────────────────────

@app.post("/tasks/add")
async def add_task(task_type: str, payload: Dict, priority: int = 1):
    """Add task to queue"""
    task_queue = TaskQueue()
    task_id = await task_queue.add_task(task_type, payload, priority)
    
    return {
        "status": "ok",
        "task_id": task_id
    }


@app.get("/tasks/status/{task_id}")
async def get_task_status(task_id: str):
    """Get task status"""
    task_queue = TaskQueue()
    task = await task_queue.get_task_status(task_id)
    
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "status": "ok",
        "task": task.to_dict()
    }


@app.get("/tasks/queue-status")
async def get_queue_status():
    """Get queue statistics"""
    task_queue = TaskQueue()
    stats = await task_queue.get_queue_status()
    
    return {
        "status": "ok",
        "queue": stats
    }


# ─────────────────────────────────────────────────────────
# Lock Manager Endpoints (Existing)
# ─────────────────────────────────────────────────────────

@app.get("/lock/status")
async def lock_status():
    """Get lock file status"""
    lock_manager = LockManager(lock_path=str(settings.LOCK_PATH))
    
    lock_exists = lock_manager.lock_path.exists()
    lock_data = None
    
    if lock_exists:
        lock_data = lock_manager._read_lock_file()
    
    return {
        "status": "ok",
        "lock_exists": lock_exists,
        "lock_path": str(settings.LOCK_PATH),
        "lock_data": lock_data
    }


@app.post("/lock/acquire")
async def lock_acquire():
    """Acquire session lock"""
    lock_manager = LockManager(lock_path=str(settings.LOCK_PATH))
    try:
        acquired = lock_manager.acquire_lock()
        return {
            "status": "ok",
            "acquired": acquired,
            "lock_path": str(settings.LOCK_PATH)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/lock/release")
async def lock_release():
    """Release session lock"""
    lock_manager = LockManager(lock_path=str(settings.LOCK_PATH))
    try:
        released = lock_manager.release_lock()
        return {
            "status": "ok",
            "released": released,
            "lock_path": str(settings.LOCK_PATH)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=settings.WORKER_PORT)


# ─────────────────────────────────────────────────────────
# Telegram Hub Endpoints
# ─────────────────────────────────────────────────────────

@app.get("/telegram/status")
async def telegram_status():
    """Get Telegram Hub status"""
    try:
        from telegram_hub import get_telegram_hub
        hub = get_telegram_hub()
        return {
            "status": "ok",
            "telegram": {
                "running": hub._running,
                "admin_chat": bool(hub.admin_chat_id),
                "channel_configured": bool(hub.channel_id),
                "group_configured": bool(hub.group_id),
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/telegram/test-notification")
async def telegram_test_notification():
    """Send a test notification to admin chat"""
    try:
        from telegram_hub import get_telegram_hub
        hub = get_telegram_hub()
        if not hub._running:
            return {"status": "error", "message": "Telegram Hub çalışmıyor"}
        
        await hub.notify_threads_ready(count=1, top_score=9.5)
        return {"status": "ok", "message": "Test bildirimi gönderildi"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/telegram/broadcast/{item_id}")
async def telegram_broadcast(item_id: str):
    """Manually broadcast a thread to Telegram channel"""
    try:
        from telegram_hub import get_telegram_hub
        hub = get_telegram_hub()
        
        if not hub._running:
            return {"status": "error", "message": "Telegram Hub çalışmıyor"}
        
        if item_id not in approval_queue.items:
            raise HTTPException(status_code=404, detail=f"Thread not found: {item_id}")
        
        item = approval_queue.items[item_id]
        
        success = await hub.broadcast_thread_to_channel(
            title=item.content_item.title,
            tr_thread=item.tr_thread,
            x_tweet_url="",  # Henüz X'e atılmamışsa boş
            image_url=getattr(item, 'image_url', None),
            viral_score=item.viral_score,
        )
        
        return {
            "status": "success" if success else "error",
            "message": "Kanala yayınlandı" if success else "Kanal ID yapılandırılmamış"
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}