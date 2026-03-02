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
from fastapi import FastAPI, HTTPException
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
    
    # Start X Daemon
    try:
        x_daemon = XDaemon()
        await x_daemon.start()
        logger.info("✅ X Daemon started")
    except Exception as e:
        logger.error(f"❌ X Daemon start failed: {e}")
    
    # Start Orchestrator (Main automation engine)
    try:
        orchestrator_config = OrchestratorConfig(
            # Posting schedule
            posts_per_day=3,
            post_times=["09:00", "14:00", "20:00"],
            
            # Intel collection
            intel_enabled=True,
            intel_interval_hours=6,  # Her 6 saatte bir içerik topla
            intel_sources=["github", "google_trends", "hackernews", "reddit", "producthunt"],
            
            # AI content generation
            ai_enabled=True,
            
            # Approval system
            require_approval=True,  # Desktop UI'dan onay gerekli
            
            # Health monitoring
            health_check_interval_minutes=5
        )
        orchestrator = Orchestrator(config=orchestrator_config)
        asyncio.create_task(orchestrator.run())
        logger.info("✅ Orchestrator started (full auto-pilot mode)")
        logger.info("📡 Intel collection: Every 6 hours")
        logger.info("🤖 AI generation: Enabled")
        logger.info("✋ Approval required: Yes (Desktop UI)")
        logger.info("📅 Post schedule: 09:00, 14:00, 20:00")
    except Exception as e:
        logger.error(f"❌ Orchestrator start failed: {e}")
    
    logger.info("🎉 X-HIVE Worker startup complete!")
    
    # Check daily reminder
    safety_logger.check_daily_reminder()
    
    yield
    
    # ───────── SHUTDOWN ─────────
    logger.info("🛑 X-HIVE Worker shutting down...")
    
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
    """Get all pending content items in approval queue"""
    try:
        pending = approval_queue.get_pending()
        
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=settings.WORKER_PORT)