from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import os
import sys

from config import settings
from lock_manager import LockManager, LockTimeoutError, LockStaleButBusyError
from chrome_pool import ChromePool, shutdown_chrome_pool
from task_queue import TaskQueue, shutdown_task_queue
from x_daemon import XDaemon, shutdown_x_daemon

# Initialize lock manager
lock_manager = LockManager(
    lock_path=settings.LOCK_PATH,
    timeout=settings.LOCK_TIMEOUT_SECONDS if hasattr(settings, 'LOCK_TIMEOUT_SECONDS') else 180,
    stale=settings.LOCK_STALE_SECONDS if hasattr(settings, 'LOCK_STALE_SECONDS') else 600,
)

# Initialize Chrome pool
chrome_pool = ChromePool()

# Initialize task queue
task_queue = TaskQueue()

# Initialize X-Daemon
x_daemon = XDaemon()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs(os.path.dirname(settings.LOCK_PATH), exist_ok=True)
    os.makedirs(settings.DATA_PATH, exist_ok=True)
    os.makedirs(settings.BROWSER_DATA_DIR, exist_ok=True)
    print(f"✅ Worker started | Lock: {settings.LOCK_PATH}")
    
    # Acquire lock on startup
    try:
        lock_manager.acquire_lock()
        print(f"🔒 Lock acquired: {settings.LOCK_PATH}")
    except LockTimeoutError:
        print("❌ Lock acquisition timed out")
        sys.exit(1)
    except LockStaleButBusyError as e:
        print(f"❌ Lock is stale but process busy: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Lock error: {e}")
        sys.exit(1)
    
    # Initialize Chrome pool on startup
    try:
        await chrome_pool.initialize()
        print(f"✅ Chrome pool initialized")
    except Exception as e:
        print(f"⚠️  Chrome pool initialization failed: {e}")
        # Don't exit - Chrome pool is optional for now
    
    # Initialize task queue on startup
    try:
        await task_queue.start()
        print(f"✅ Task queue started")
    except Exception as e:
        print(f"⚠️  Task queue initialization failed: {e}")
    
    # Initialize X-Daemon on startup
    try:
        await x_daemon.start()
        print(f"✅ X-Daemon started")
    except Exception as e:
        print(f"⚠️  X-Daemon initialization failed: {e}")
    
    yield
    
    # Shutdown
    print("🔓 Releasing lock...")
    lock_manager.release_lock()
    
    # Shutdown X-Daemon
    try:
        await shutdown_x_daemon()
    except Exception as e:
        print(f"⚠️  X-Daemon shutdown error: {e}")
    
    # Shutdown task queue
    try:
        await shutdown_task_queue()
    except Exception as e:
        print(f"⚠️  Task queue shutdown error: {e}")
    
    # Shutdown Chrome pool
    try:
        await shutdown_chrome_pool()
    except Exception as e:
        print(f"⚠️  Chrome pool shutdown error: {e}")
    
    print("✅ Shutdown complete")


app = FastAPI(title="X-HIVE Worker", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "worker": "x-hive",
        "lock_path": settings.LOCK_PATH,
        "data_path": settings.DATA_PATH,
    }


@app.get("/chrome/status")
async def chrome_status():
    """Get Chrome pool status"""
    try:
        is_healthy = await chrome_pool.is_healthy()
        return {
            "status": "ok",
            "chrome_pool": {
                "initialized": chrome_pool.browser is not None,
                "healthy": is_healthy,
                "page_open": chrome_pool.page is not None and not chrome_pool.page.is_closed(),
                "cookie_path": str(chrome_pool.cookie_path),
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/chrome/restart")
async def chrome_restart():
    """Restart Chrome pool"""
    try:
        await chrome_pool.restart()
        return {
            "status": "ok",
            "message": "Chrome pool restarted"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/lock/acquire")
async def acquire():
    try:
        lock_manager.acquire_lock()
        return {"status": "acquired", "process": os.path.basename(sys.argv[0])}
    except LockTimeoutError as e:
        return {"status": "error", "message": str(e)}
    except LockStaleButBusyError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/lock/release")
async def release():
    try:
        lock_manager.release_lock()
        return {"status": "released"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/lock/status")
async def lock_status():
    import json
    if os.path.exists(settings.LOCK_PATH):
        try:
            with open(settings.LOCK_PATH, "r") as f:
                data = json.load(f)
            return {"locked": True, "owner": data}
        except Exception as e:
            return {"locked": True, "error": str(e)}
    else:
        return {"locked": False}


@app.post("/tasks/add")
async def add_task(task_type: str, payload: dict, priority: int = 1):
    """Add a new task to the queue"""
    try:
        task_id = await task_queue.add_task(task_type, payload, priority)
        return {
            "status": "ok",
            "task_id": task_id,
            "message": f"Task added: {task_type}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/tasks/status/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a specific task"""
    try:
        task = await task_queue.get_task_status(task_id)
        if task is None:
            return {
                "status": "error",
                "error": f"Task not found: {task_id}"
            }
        return {
            "status": "ok",
            "task": task.to_dict()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/tasks/queue-status")
async def get_queue_status():
    """Get current queue statistics"""
    try:
        stats = await task_queue.get_queue_status()
        return {
            "status": "ok",
            "queue": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/daemon/status")
async def daemon_status():
    """Get X-Daemon status"""
    try:
        status = await x_daemon.get_status()
        return {
            "status": "ok",
            "daemon": status
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/daemon/start")
async def daemon_start():
    """Start X-Daemon"""
    try:
        result = await x_daemon.start()
        return {
            "status": "ok",
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/daemon/stop")
async def daemon_stop():
    """Stop X-Daemon"""
    try:
        result = await x_daemon.stop()
        return {
            "status": "ok",
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/daemon/restart")
async def daemon_restart():
    """Restart X-Daemon"""
    try:
        result = await x_daemon.restart()
        return {
            "status": "ok",
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/x/post")
async def x_post_tweet(text: str, images: list = None):
    """Post a tweet via X-Daemon"""
    try:
        result = await x_daemon.post_tweet(text, images)
        return {
            "status": "ok",
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/x/reply")
async def x_reply_tweet(tweet_url: str, text: str):
    """Reply to a tweet via X-Daemon"""
    try:
        result = await x_daemon.reply_to_tweet(tweet_url, text)
        return {
            "status": "ok",
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/x/like")
async def x_like_tweet(tweet_url: str):
    """Like a tweet via X-Daemon"""
    try:
        result = await x_daemon.like_tweet(tweet_url)
        return {
            "status": "ok",
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/x/retweet")
async def x_retweet(tweet_url: str):
    """Retweet a tweet via X-Daemon"""
    try:
        result = await x_daemon.retweet(tweet_url)
        return {
            "status": "ok",
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/x/quote")
async def x_quote_tweet(tweet_url: str, text: str, images: list = None):
    """Quote tweet (retweet with comment) via X-Daemon"""
    try:
        result = await x_daemon.quote_tweet(tweet_url, text, images)
        return {
            "status": "ok",
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=settings.WORKER_PORT)
