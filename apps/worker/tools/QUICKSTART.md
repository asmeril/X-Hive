# Cookie Authentication Quick Start Guide 🍪

**5-minute setup for authenticated content scraping**

---

## What This Does

Automatically extracts authentication cookies from platforms so you can:

- ✅ Scrape content **without API costs**
- ✅ Bypass rate limits
- ✅ Access authenticated-only content
- ✅ Save **$150/month** on Twitter API fees

---

## Installation (One-Time)

### 1. Install Playwright

```bash
cd apps/worker
pip install playwright
playwright install chromium
```

**Verify:**
```bash
python -c "from playwright.sync_api import sync_playwright; print('✅ OK')"
```

---

## Cookie Extraction (5 Minutes)

### Step 1: Run Extractor

```bash
python tools/cookie_extractor.py
```

### Step 2: Select Platforms

```
Select platforms to extract cookies from:
  1. Essential (Reddit + Twitter) - Recommended ✅
  2. All available platforms
  3. Custom selection

Enter choice (1-3): 1
```

**Choose Option 1** for Phase 1

### Step 3: Login to Reddit

```
🌐 PLATFORM: Reddit
═══════════════════════════════════════════════════════════════════

📋 Instructions:
1. Click 'Log in' button (top right)
2. Enter username and password
3. Click 'Log in'
4. Wait for homepage to load
5. Browser will auto-close when cookie is captured

Press ENTER to open Reddit browser...
```

**Press ENTER** → Browser opens

**Login with throwaway account:**
- Create account: https://old.reddit.com/register
- Or use existing throwaway

**✅ Success:**
```
✅ Cookies detected for Reddit!
✅ Successfully extracted 1 cookie(s) from Reddit:
   • reddit_session

✅ Reddit complete!
```

### Step 4: Login to Twitter

```
🌐 PLATFORM: Twitter/X
═══════════════════════════════════════════════════════════════════

📋 Instructions:
1. Enter phone/email/username
2. Click 'Next'
3. Enter password
4. Click 'Log in'
5. Complete any verification
6. Wait for home feed to load
7. Browser will auto-close

Press ENTER to open Twitter browser...
```

**Press ENTER** → Browser opens

**Login with throwaway account:**
- Create account: https://twitter.com/signup
- Or use existing throwaway

**✅ Success:**
```
✅ Cookies detected for Twitter/X!
✅ Successfully extracted 2 cookie(s) from Twitter/X:
   • auth_token
   • ct0

✅ Twitter/X complete!
```

### Step 5: Extraction Complete

```
═══════════════════════════════════════════════════════════════════
📊 EXTRACTION SUMMARY
═══════════════════════════════════════════════════════════════════

✅ Reddit              : 1 cookie(s)
   • reddit_session
✅ Twitter/X           : 2 cookie(s)
   • auth_token
   • ct0

═══════════════════════════════════════════════════════════════════
✅ COOKIE EXTRACTION COMPLETE!
═══════════════════════════════════════════════════════════════════

💾 Saved 3 cookie(s) to: apps/worker/.env
```

---

## Verification (30 Seconds)

### Test Cookie Manager

```bash
python test_cookie_manager.py
```

**Expected output:**
```
🍪 TESTING COOKIE MANAGER
═══════════════════════════════════════════════════════════════════

📋 Cookie Status:

  ✅ reddit         : Available
  ✅ twitter        : Available
  ❌ medium         : Missing
  ❌ substack       : Missing

✅ Reddit headers: 5 keys
   - User-Agent: Mozilla/5.0...
   - Cookie: reddit_session=***...

✅ Twitter headers: 7 keys
   - User-Agent: Mozilla/5.0...
   - Cookie: auth_token=***...
   - CSRF Token: Present

✅ All essential cookies available!
```

### Test Reddit Source

```bash
python test_batch1_sources.py
```

**Look for:**
```
✅ RedditSource initialized (20 subreddits, with cookie)
✅ Reddit: Scraped 200 posts from 20 subreddits
```

**Before (no cookie):**
```
⚠️  RedditSource initialized (20 subreddits, without cookie)
⚠️  No Reddit cookie found. Scraping may be rate-limited.
```

---

## Files Created

### .env (Auto-created)

```
apps/worker/.env
```

**Contents:**
```env
# === COOKIES ===

REDDIT_COOKIE=your_reddit_session_cookie_here
TWITTER_COOKIE=your_twitter_auth_token_here
TWITTER_CT0=your_twitter_ct0_token_here
```

**⚠️ NEVER commit this file to git!**

Already in `.gitignore` ✅

---

## Usage in Code

### Automatic (Recommended)

Cookie manager is **automatically used** in all sources:

```python
from intel.reddit_source import RedditSource

# Cookie automatically loaded and used
reddit = RedditSource()
items = await reddit.fetch_latest()
```

### Manual Control

```python
from intel.cookie_manager import get_cookie_manager

cm = get_cookie_manager()

# Check cookie
if cm.validate_cookie('reddit'):
    print("✅ Authenticated")
else:
    print("❌ No cookie - extract it")

# Get headers
headers = cm.get_headers_for_reddit()

# Use in requests
async with aiohttp.ClientSession() as session:
    async with session.get(url, headers=headers) as response:
        data = await response.text()
```

---

## Troubleshooting

### Cookie Not Detected

**Problem:**
```
⚠️  Could not detect cookies for Reddit
   Expected cookies: reddit_session
   Make sure you're fully logged in!
```

**Fix:**
1. Make sure you see your **username in top-right**
2. Navigate to any subreddit
3. Wait up to **5 minutes**
4. Don't close browser manually

**Re-run:**
```bash
python tools/cookie_extractor.py
```

---

### Browser Won't Open

**Problem:**
```
Error: Browser type 'chromium' is not installed
```

**Fix:**
```bash
playwright install chromium
```

---

### 403 Forbidden Errors

**Problem:**
```
❌ Error scraping r/MachineLearning: 403 Forbidden
```

**Cause:** Cookie expired

**Fix:**
```bash
# Re-extract cookies
python tools/cookie_extractor.py

# Test again
python test_batch1_sources.py
```

---

### No Results from Reddit

**Problem:**
```
✅ Reddit: Scraped 0 posts from 20 subreddits
```

**Possible causes:**
1. **Cookie invalid** → Re-extract
2. **Rate limited** → Wait 10 minutes
3. **IP blocked** → Change IP/VPN

**Debug:**
```bash
# Check cookie status
python test_cookie_manager.py

# If missing, extract
python tools/cookie_extractor.py
```

---

## Maintenance

### Cookie Rotation Schedule

| Platform | Rotate Every | Why |
|----------|--------------|-----|
| Reddit | 30 days | Session expires |
| Twitter | 14 days | Security policy |
| Medium | 60 days | Long-lived sessions |

**Set calendar reminder!**

### Re-extraction

```bash
# Quick re-extract
python tools/cookie_extractor.py
# Choose Option 1

# Or specific platform
python tools/cookie_extractor.py
# Choose Option 3 -> Select platform number
```

---

## Security Checklist

✅ **Use throwaway accounts**
- Not your main personal accounts
- Create with temp email: guerrillamail.com

✅ **Verify .env is gitignored**
```bash
git check-ignore apps/worker/.env
# Should output: apps/worker/.env
```

✅ **Set file permissions** (Linux/Mac)
```bash
chmod 600 apps/worker/.env
```

✅ **Backup .env** (encrypted)
```bash
gpg -c apps/worker/.env
# Stores to .env.gpg
```

---

## Next Steps

1. ✅ **Cookies extracted** → Proceed to Twitter source (Phase 1 Batch 2)
2. ✅ **Test Reddit** → Verify authenticated scraping works
3. ⏳ **Build Twitter source** → Cookie-based scraping ($150/mo savings)
4. ⏳ **Medium/Substack** → Extract when needed (Phase 2)

---

## Documentation

- **Full Guide:** [docs/AUTO-COOKIE-EXTRACTION.md](../../docs/AUTO-COOKIE-EXTRACTION.md)
- **Cookie Strategy:** [docs/COOKIE-STRATEGY.md](../../docs/COOKIE-STRATEGY.md)
- **API Reference:** [tools/README.md](./README.md)

---

## Cost Savings

**Without cookies:**
- Twitter API: $150/month
- Total: **$152/month**

**With cookies:**
- Twitter posting API: $2/month
- Reddit: FREE (web scraping)
- Total: **$2/month**

**Savings: $150/month = $1,800/year** 🎉

---

## Support

**Issues?**

1. Check logs: `export LOG_LEVEL=DEBUG`
2. Test Playwright: `python -c "from playwright.sync_api import sync_playwright; print('OK')"`
3. Re-run extractor
4. Check GitHub Issues

---

**🎉 You're ready for authenticated scraping!** 🍪
