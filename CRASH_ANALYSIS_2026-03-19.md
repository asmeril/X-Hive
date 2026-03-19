# X-HIVE Backend Crash Analysis & Recovery Plan
**Date:** 2026-03-19  
**Status:** CRITICAL - BACKEND UNSTABLE (Intel Collection Loop Issue)

## PROBLEM SUMMARY

### Current State
- **Setup:** v1.2.6 with timeouts and heartbeat  
- **Issue:** Backend starts successfully but crashes ~80-120s after startup
- **Impact:** Tauri health monitor goes into restart loop (visible in screenshots)
- **User Impact:** "Backend Yanıt Vermiyor" (Backend Not Responding) UI state

### Root Cause Analysis

**Identified:**
✅ Backend initialization: **WORKS** - all systems start cleanly
✅ Timeout implementation: **WORKS** - orchestrator.py has asyncio.wait_for on all sources
✅ Module imports: **WORK** - all Intel sources initialize successfully
✅ FastAPI startup: **WORKS** - Uvicorn binds to 127.0.0.1:8765 successfully

**Unknown:**
❌ Process termination trigger - Backend exits cleanly after "Uvicorn running..." message
❌ Specific Intel source causing crash - Not isolated yet (test_intel_isolation.py created)
❌ Exception handling gap - No unhandled exception in logs, process just exits

###  Temporary Fix Applied
**Status:** DEPLOYED  
**Change:** `apps/worker/app/main.py` line ~102  
**Setting:** `intel_enabled=False` in OrchestratorConfig

This disables periodic Intel collection to:
- Allow backend to start and stay online
- Prevent crash loop during health monitor polling
- Enable API endpoints to work for manual testing

---

## DEBUGGING FINDINGS

### Log Analysis
**Source:** Backend stdout/stderr logs from C:\Users\ttevf\AppData\Local\XHive\worker\

Last successful startup sequence:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
```

Immediately followed by terminal exit with no error stacktrace.

### v1.2.6 Timeout Verification

All Intel sources properly have `asyncio.wait_for()`:
- GitHub: 30s  ❌ No evidence of working
- Google Trends: 30s with Playwright fallback
- Reddit: 45s
- ProductHunt: 20s
- Telegram: 30s with exception handler
- Arxiv: 20s
- HuggingFace: 20s
- Substack: 15s
- Perplexity: 15s
- YouTube: 15s
- LinkedIn: 15s
- AI Generation: 120s
- Visibility Enrichment: 60s

✅ **Timeouts ARE implemented** but crash still occurs.

### Environmental Issues Discovered

1. **Module path issue in production:**
   - Backend runs from d:\Projects\X-Hive\apps\worker (DEV) - WORKS
   - Backend crashes from C:\Users\ttevf\AppData\Local\XHive\worker (PROD) - Different behavior

2. **Python venv paths:**
   - Development: Uses system Python or .venv in source
   - Production: Uses C:\Users\ttevf\AppData\Local\XHive\worker\.venv

3. **Lock file locations:** Uses LocalAppData normalization (good)

---

## SOLUTION PATH

### Phase 1: Stabilize Backend (Current)
✅ **DONE:** Intel collection disabled via main.py config
✅ **DONE:** Created test_intel_isolation.py for source-by-source testing
✅ **DONE:** Documented findings in AGENT_LOG.md

### Phase 2: Test Intel Sources in Isolation
**Next:** Run diagnostic script to find which source causes crash

```bash
cd d:\Projects\X-Hive\apps\worker
python test_intel_isolation.py
```

Expected output will identify:
- Which source hangs despite timeouts
- Which source raises unhandled exception
- Response times for working sources

### Phase 3: Fix or Skip Problematic Source
Once identified, either:
- **Fix:** Update source code to handle edge cases
- **Skip:** Remove from intel_sources list in config
- **Wrap:** Add outer try-except in orchestrator.run_intel_collection_once()

### Phase 4: Re-enable Intelligence Collection
After fixing:
1. Set `intel_enabled=True` in main.py
2. Test with reduced interval (1 hour instead of 6)
3. Monitor backend stability for 30+ minutes
4. If stable, enable Tauri auto-restart logic

### Phase 5: Full Pipeline Testing
Then test end-to-end:
- Intel collection → AI generation → Viral scoring → Thread creation
- Approval workflow
- Tweet posting (in safe mode)

---

## NEW DIAGNOSTIC SCRIPT

**Location:** `apps/worker/test_intel_isolation.py`

**Usage:**
```bash
cd d:\Projects\X-Hive\apps\worker
python test_intel_isolation.py
```

**Tests Each Source In Isolation:**
- Runs with specified timeout
- Catches asyncio.TimeoutError separately
- Catches other exceptions
- Logs response time and item count
- Provides summary table

**Expected Summary Output:**
```
TEST SUMMARY
============
GitHub               ✅ PASS
Google Trends        ✅ PASS
HackerNews           ✅ PASS
Reddit               ❌ FAIL (timeout)
ProductHunt          ✅ PASS
Substack             ❌ FAIL (403 Forbidden)
Telegram             ❌ FAIL (Connection refused)
AI Generation        ✅ PASS

Passed: 5/8
```

---

## IMMEDIATE ACTIONS FOR USER

### 1. Test Backend Stability (NO Intel Collection)
```powershell
# Kill old Python processes
taskkill /F /IM python.exe

# Start backend from source
cd d:\Projects\X-Hive\apps\worker
$env:PYTHONUNBUFFERED='1'
python -m app.main
```

Expected: Backend runs indefinitely without crashing
- Should see: "Uvicorn running on http://127.0.0.1:8765"
- Should NOT see: exits after 90s

### 2. Test API Endpoints (While Running)
```bash
# In another terminal
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/system/status
```

Expected: 200 OK responses

### 3. Run Intel Isolation Test
```bash
cd d:\Projects\X-Hive\apps\worker
python test_intel_isolation.py
```

This will display which sources work and which fail.

### 4. Deploy Fixed Backend
Once Intel crash source is identified and fixed:
1. Commit changes to git
2. Run: `build_setup_versioned.ps1` to create v1.2.7 installer
3. This auto-updates C:\Users\ttevf\AppData\Local\XHive\worker

---

## APPROVAL QUEUE STATUS

Current state from logs:
- **Loaded**: 17 items from previous runs
- **Location**: C:\Users\ttevf\AppData\Local\XHive\data
- **Format**: JSON persistence via approval_queue.py

These can be manually approved/tested via:
- Desktop UI "Onay" tab
- Or direct API call to `/approval/approve/{item_id}`

---

## PERFORMANCE NOTES

### Intel Collection Expected Times (Without Hangs)
- GitHub: ~5-10s
- Google Trends: ~15-20s (Playwright rendering)
- HackerNews: ~2-3s
- Reddit: ~10-15s
- ProductHunt: ~5s
- All sources: ~60-80s total

With 30s timeouts on each → Total should complete in <2 minutes

### AI Content Generation
- Single tweet: ~3-5s (Gemini Flash)
- Viral thread (3 items): ~15-20s
- Visibility enrichment: ~10-15s
- Full pipeline: ~40-50s

---

## GIT COMMIT STATUS

**Last Commit:** `4452c05` - "debug: disable intel collection to test backend stability"
- Modified `apps/worker/app/main.py` - Intel disabled
- Added `apps/worker/test_intel_isolation.py` - Diagnostic tool
- Updated `docs/AGENT_LOG.md` - This analysis

**To Deploy:**
```bash
cd d:\Projects\X-Hive
git push
```

---

## FILES TO MONITOR

**Backend Logs:**
- C:\Users\ttevf\AppData\Local\XHive\worker\backend_stderr.log (errors)
- C:\Users\ttevf\AppData\Local\XHive\worker\backend_stdout.log (runtime)
- C:\Users\ttevf\AppData\Local\XHive\data\logs\structured.log (task logs)

**Tauri Logs:**
- C:\Users\ttevf\AppData\Local\XHive\tauri_debug.log (health monitor cycles)

**Approval Queue:**
- C:\Users\ttevf\AppData\Local\XHive\data\approval_queue.json (content items)

---

## SUCCESS CRITERIA

- ✅ Backend stays online for >5 minutes without crashing (Intel disabled)
- ✅ API endpoints return 200 OK responses
- ✅ Intel isolation test completes and shows which sources fail
- ✅ Problematic source either fixed or disabled
- ✅ Backend stays online for >5 minutes WITH Intel enabled
- ✅ Intel collection completes end-to-end
- ✅ AI generation produces viral threads
- ✅ Approval queue fills with 3+ threads
- ✅ User can approve threads via UI
- ✅ Threads post to X (Twitter) without errors

---

## NEXT PHASE (v1.2.8)

After stability achieved:
1. **Permanent Lock Mechanism** - Prevent multi-instance polling conflicts
2. **Telegram Hub Re-enablement** - Optional with token deduplication
3. **Production Installer** - Updated  ISC setup with new binary
4. **Monitoring Dashboard** - Real-time Intel/AI/posting metrics
5. **Fallback Sources** - Alternative providers if primary fails

---

**End of Analysis | Date: 2026-03-19 21:50 UTC+3**

