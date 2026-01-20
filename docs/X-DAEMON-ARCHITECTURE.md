# X Daemon Architecture

**Version:** 1.0  
**Status:** Proposed  
**Target:** Q1 2026  
**Related Issue:** #[X Daemon Mimarisi]

---

## 📋 Executive Summary

This document describes the migration from a **stateless process-per-request** model to a **persistent daemon architecture** for X (Twitter) automation within the X-Hive ecosystem.

### Key Metrics
- **Performance:** 6x faster (30-60s → 5-20s per operation)
- **Resource:** 70% less RAM (single Chrome instance)
- **Reliability:** Zero lock conflicts (single process model)
- **Cookie Management:** Always warm (no reload overhead)

---

## 🏗️ Current Architecture (Stateless)

```
┌─────────────────────────────────────────┐
│  XiDeAI Pro (C# Desktop)                │
│                                         │
│  For each X operation:                  │
│  1. Spawn Python process (2-3s)        │
│  2. Python starts Chrome (5-10s)       │
│  3. Load cookies from disk (2-3s)      │
│  4. Execute operation (10-30s)         │
│  5. Close Chrome & Python              │
│                                         │
│  Total: 30-60 seconds                   │
└─────────────────────────────────────────┘

Problems:
❌ High latency (repeated startup)
❌ Lock file conflicts (concurrent executions)
❌ Cookie reload overhead
❌ High RAM churn
```

---

## 🚀 Proposed Architecture (Daemon)

```
┌──────────────────────────────────────────────────────────┐
│  Desktop App (Tauri + React)                             │
│  ┌────────────────────────────────────┐                  │
│  │  UI: X Operations                  │                  │
│  │  - Post Tweet                       │                  │
│  │  - Reply to Tweet                   │                  │
│  │  - Daemon Status Monitor            │                  │
│  └────────────┬───────────────────────┘                  │
└───────────────┼──────────────────────────────────────────┘
                │ HTTP (localhost:8000)
                │
┌───────────────▼──────────────────────────────────────────┐
│  Worker (Python FastAPI) - DAEMON LAYER                  │
│  ┌────────────────────────────────────┐                  │
│  │  X Automation Daemon                │                  │
│  │  /apps/worker/x_daemon.py           │                  │
│  │                                     │                  │
│  │  ┌──────────────────────────────┐  │                  │
│  │  │ Chrome Driver Pool            │  │                  │
│  │  │ - Persistent WebDriver        │  │                  │
│  │  │ - Always logged in            │  │                  │
│  │  │ - Cookie auto-refresh         │  │                  │
│  │  └──────────────────────────────┘  │                  │
│  │                                     │                  │
│  │  ┌──────────────────────────────┐  │                  │
│  │  │ Task Queue                    │  │                  │
│  │  │ - Sequential execution        │  │                  │
│  │  │ - Lock-aware (uses LockMgr)  │  │                  │
│  │  └──────────────────────────────┘  │                  │
│  │                                     │                  │
│  │  Endpoints:                         │                  │
│  │  POST /api/x/tweet                 │                  │
│  │  POST /api/x/reply                 │                  │
│  │  GET  /api/x/status                │                  │
│  └─────────────┬───────────────────────┘                  │
│                │                                          │
│  ┌─────────────▼───────────────────────┐                  │
│  │  Lock Manager v1.1                  │                  │
│  │  - acquire_lock("x_chrome_session") │                  │
│  │  - release_lock()                   │                  │
│  └─────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────┘

Execution Flow:
1. Desktop → POST /api/x/tweet {"text": "Hello"}
2. Daemon acquires lock (instant)
3. Uses existing Chrome (5-20s)
4. Returns result
5. Releases lock

Total: 5-20 seconds ⚡
```

---

## 📦 Implementation Plan

### Phase 1: Core Daemon (Day 1)

#### File: `apps/worker/x_daemon.py`

```python
"""
X Automation Daemon
Persistent Chrome driver with lock-protected operations
"""
from fastapi import APIRouter, HTTPException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pydantic import BaseModel
import asyncio
from typing import Optional
from .lock_manager import LockManager
from .config import settings
import json

router = APIRouter(prefix="/api/x", tags=["x-automation"])

class XDaemonManager:
    """Singleton manager for persistent Chrome driver"""
    
    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self.lock_manager = LockManager()
        self.is_initialized = False
        self._health_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Initialize Chrome driver and load cookies (called once at startup)"""
        if self.is_initialized:
            return
            
        print("🚀 Starting X Daemon...")
        
        # Configure Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--user-data-dir={settings.CHROME_PROFILE_PATH}")
        
        # Start driver
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Load cookies
        await self._load_cookies()
        
        # Navigate to X
        self.driver.get("https://x.com/home")
        
        self.is_initialized = True
        
        # Start health check loop
        self._health_task = asyncio.create_task(self._health_check_loop())
        
        print("✅ X Daemon ready - Chrome driver initialized")
        
    async def _load_cookies(self):
        """Load X cookies from lock-protected storage"""
        cookie_path = settings.DATA_PATH / "x_cookies.json"
        
        if not cookie_path.exists():
            raise Exception(f"Cookie file not found: {cookie_path}")
        
        try:
            # Acquire lock before reading cookies
            acquired = await self.lock_manager.acquire("x_cookies")
            if not acquired:
                raise Exception("Failed to acquire cookie lock")
            
            # Load from disk
            with open(cookie_path, 'r') as f:
                cookies = json.load(f)
            
            # Navigate to X first (required for cookie domain)
            self.driver.get("https://x.com")
            
            # Add cookies
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            
            print(f"✅ Loaded {len(cookies)} cookies")
            
        finally:
            await self.lock_manager.release("x_cookies")
    
    async def post_tweet(self, text: str) -> dict:
        """Post a tweet using persistent Chrome driver"""
        if not self.is_initialized:
            await self.start()
        
        try:
            # Acquire session lock
            acquired = await self.lock_manager.acquire("x_chrome_session", timeout=30)
            if not acquired:
                raise HTTPException(503, "X session locked by another process")
            
            # Navigate to compose
            self.driver.get("https://x.com/compose/tweet")
            await asyncio.sleep(2)
            
            # Find tweet box
            tweet_box = self.driver.find_element("css selector", "[data-testid='tweetTextarea_0']")
            tweet_box.send_keys(text)
            
            # Click post button
            post_button = self.driver.find_element("css selector", "[data-testid='tweetButtonInline']")
            post_button.click()
            
            await asyncio.sleep(3)
            
            # Extract tweet URL (simplified)
            current_url = self.driver.current_url
            
            return {
                "status": "success",
                "tweet_url": current_url,
                "text": text
            }
            
        except Exception as e:
            raise HTTPException(500, f"Failed to post tweet: {str(e)}")
            
        finally:
            await self.lock_manager.release("x_chrome_session")
    
    async def _health_check_loop(self):
        """Auto-restart Chrome if it crashes"""
        while self.is_initialized:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            try:
                # Ping Chrome
                _ = self.driver.current_url
                
            except Exception as e:
                print(f"❌ Chrome crashed: {e}")
                print("🔄 Attempting recovery...")
                
                # Release all locks
                # (LockManager should have release_all method)
                
                # Restart
                self.is_initialized = False
                try:
                    await self.start()
                    print("✅ Chrome restarted successfully")
                except Exception as restart_error:
                    print(f"❌ Restart failed: {restart_error}")
                    await asyncio.sleep(settings.DAEMON_RESTART_DELAY)
    
    async def shutdown(self):
        """Graceful shutdown"""
        print("🛑 Shutting down X Daemon...")
        
        if self._health_task:
            self._health_task.cancel()
        
        if self.driver:
            self.driver.quit()
        
        self.is_initialized = False
        print("✅ X Daemon stopped")

# Singleton instance
x_daemon = XDaemonManager()

# ─────────────────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────────────────

class TweetRequest(BaseModel):
    text: str

@router.post("/tweet")
async def post_tweet(req: TweetRequest):
    """Post a new tweet    """
    result = await x_daemon.post_tweet(req.text)
    return result

@router.get("/status")
async def get_daemon_status():
    """Get daemon health status    """
    lock_status = await x_daemon.lock_manager.get_all_locks()
    
    return {
        "chrome_ready": x_daemon.is_initialized,
        "driver_session_id": x_daemon.driver.session_id if x_daemon.driver else None,
        "lock_status": lock_status
    }
```

---

### Phase 2: Worker Integration (Day 1)

#### File: `apps/worker/main.py` (modifications)

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .x_daemon import router as x_router, x_daemon

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan events
    Startup: Initialize X Daemon
    Shutdown: Gracefully close Chrome"""  
    print("🚀 Worker starting up...")
    await x_daemon.start()
    yield
    print("🛑 Worker shutting down...")
    await x_daemon.shutdown()

app = FastAPI(lifespan=lifespan)

# Include X automation routes
app.include_router(x_router)

# ... existing lock/health routes ...
```

---

### Phase 3: Desktop UI Integration (Day 2)

#### File: `apps/desktop/App.tsx` (additions)

```tsx
import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api';

interface XDaemonStatus {
  chrome_ready: boolean;
  driver_session_id: string | null;
  lock_status: Record<string, any>;
}

function XAutomationPanel() {
  const [status, setStatus] = useState<XDaemonStatus | null>(null);
  const [tweetText, setTweetText] = useState('');
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const result = await invoke('call_worker_api', {
          endpoint: '/api/x/status',
          method: 'GET'
        });
        setStatus(result as XDaemonStatus);
      } catch (err) {
        console.error('Daemon status error:', err);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const handlePostTweet = async () => {
    if (!tweetText.trim()) return;
    
    setPosting(true);
    try {
      const result = await invoke('call_worker_api', {
        endpoint: '/api/x/tweet',
        method: 'POST',
        body: JSON.stringify({ text: tweetText })
      });
      console.log('Tweet posted:', result);
      alert('Tweet posted successfully!');
      setTweetText('');
    } catch (err) {
      console.error('Tweet failed:', err);
      alert('Failed to post tweet');
    } finally {
      setPosting(false);
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h2>X Automation Daemon</h2>
      <div style={{ marginBottom: '16px' }}>
        <p><strong>Chrome Status:</strong> {status?.chrome_ready ? '✅ Ready' : '❌ Not Ready'}</p>
        <p><strong>Session ID:</strong> {status?.driver_session_id || 'N/A'}</p>
        <p><strong>Active Locks:</strong> {JSON.stringify(status?.lock_status || {})}</p>
      </div>
      <div>
        <textarea
          value={tweetText}
          onChange={(e) => setTweetText(e.target.value)}
          placeholder="What's happening?"
          rows={4}
          style={{ width: '100%', padding: '8px' }}
        />
        <button
          onClick={handlePostTweet}
          disabled={posting || !status?.chrome_ready}
          style={{ marginTop: '8px', padding: '8px 16px' }}
        >
          {posting ? 'Posting...' : 'Post Tweet'}
        </button>
      </div>
    </div>
  );
}

export default XAutomationPanel;
```

---

## 🔧 Configuration

### File: `apps/worker/config.py` (additions)

```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # ... existing settings ...
    # X Daemon settings
    CHROME_PROFILE_PATH: Path = Path.home() / ".x-hive" / "chrome-profile"
    CHROME_HEADLESS: bool = True
    DAEMON_RESTART_DELAY: int = 5  # seconds
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### File: `apps/worker/.env.example` (additions)

```bash
# X Daemon Configuration
CHROME_PROFILE_PATH=/home/user/.x-hive/chrome-profile
CHROME_HEADLESS=true
DAEMON_RESTART_DELAY=5
```

### File: `apps/worker/requirements.txt` (additions)

```txt
selenium==4.15.0
webdriver-manager==4.0.1
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/test_x_daemon.py
import pytest
from apps.worker.x_daemon import XDaemonManager

@pytest.mark.asyncio
async def test_daemon_startup():
    daemon = XDaemonManager()
    await daemon.start()
    assert daemon.is_initialized == True
    assert daemon.driver is not None
    await daemon.shutdown()

@pytest.mark.asyncio
async def test_tweet_post():
    daemon = XDaemonManager()
    await daemon.start()
    result = await daemon.post_tweet("Test tweet from X-Hive")
    assert result["status"] == "success"
    assert "tweet_url" in result
    await daemon.shutdown()

@pytest.mark.asyncio
async def test_crash_recovery():
    daemon = XDaemonManager()
    await daemon.start()
    # Simulate crash
    daemon.driver.quit()
    # Wait for health check to detect and restart
    await asyncio.sleep(35)
    assert daemon.is_initialized == True
```

### Load Testing

```bash
# Simulate 100 tweets in 1 minute
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/x/tweet \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"Load test tweet #$i\"}" &
  sleep 0.6
done
```

### Stability Testing

```bash
# 24-hour stress test
python scripts/stress_test.py --duration=24h --requests-per-minute=10
```

---

## 📊 Performance Comparison

| Metric | Old (Stateless) | New (Daemon) | Improvement |
|--------|----------------|--------------|-------------|
| **Tweet Post Time** | 30-60s | 5-20s | **6x faster** |
| **Chrome Startup** | Every request (10s) | Once (10s) | **∞x better** |
| **Cookie Load** | Every request (3s) | Once (3s) | **∞x better** |
| **RAM Usage** | ~500MB/request | ~200MB total | **70% less** |
| **Lock Conflicts** | Frequent | Zero | **100% solved** |
| **Concurrent Requests** | Impossible | Queued | **✅ Handled** |

---

## 🚨 Error Handling & Recovery

### Crash Scenarios

1. **Chrome crashes**
   - Health check detects (30s)
   - Auto-restart Chrome
   - Reload cookies
   - Resume operations

2. **Worker restarts**
   - FastAPI lifespan shutdown → close Chrome gracefully
   - FastAPI lifespan startup → reinitialize daemon

3. **Lock deadlock**
   - Lock Manager TTL (24h) handles stale locks
   - Manual cleanup: `DELETE /api/lock/{resource_id}`

### Monitoring

```python
# Add to x_daemon.py

async def get_metrics():
    return {
        "uptime_seconds": time.time() - daemon.start_time,
        "total_requests": daemon.request_count,
        "failed_requests": daemon.error_count,
        "chrome_restarts": daemon.restart_count,
        "active_locks": await lock_manager.get_all_locks()
    }
```

---

## 🗺️ Deployment Checklist

- [ ] Update `requirements.txt` with Selenium
- [ ] Configure Chrome profile path in `.env`
- [ ] Test daemon startup/shutdown locally
- [ ] Run unit tests
- [ ] Run load tests (100 requests)
- [ ] Deploy to production
- [ ] Monitor logs for 24 hours
- [ ] Update README with daemon usage

---

## 📚 References

- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [Selenium WebDriver Documentation](https://www.selenium.dev/documentation/)
- [X-Hive Lock Manager Specification](./README.md#lock-standard)

---

**Last Updated:** 2026-01-20 21:15:18  
**Author:** asmeril  
**Status:** Ready for Implementation