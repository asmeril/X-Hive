from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from lock_manager import LockManager, LockTimeoutError, LockStaleButBusyError
import os
import sys

# Initialize lock manager
lock_manager = LockManager(
    lock_path=settings.LOCK_PATH,
    timeout=settings.LOCK_TIMEOUT_SECONDS if hasattr(settings, 'LOCK_TIMEOUT_SECONDS') else 180,
    stale=settings.LOCK_STALE_SECONDS if hasattr(settings, 'LOCK_STALE_SECONDS') else 600,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs(os.path.dirname(settings.LOCK_PATH), exist_ok=True)
    os.makedirs(settings.DATA_PATH, exist_ok=True)
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
    
    yield
    
    # Shutdown
    print("🔓 Releasing lock...")
    lock_manager.release_lock()
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=settings.WORKER_PORT)
