# Cookie Authentication System 🍪

Complete cookie-based authentication system for X-Hive content sources.

---

## Quick Start

### 1. Extract Cookies (One-time Setup)

```bash
cd apps/worker
python tools/cookie_extractor.py
```

**Select Option 1** (Essential: Reddit + Twitter)

- Browser opens for each platform
- Login with throwaway account
- Cookies auto-detected and saved
- **Done in ~5 minutes!**

---

### 2. Verify Installation

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

✅ All essential cookies available!
```

---

### 3. Test Reddit with Cookies

```bash
python test_batch1_sources.py
```

**Should see:**
```
✅ RedditSource initialized (20 subreddits, with cookie)
✅ Reddit: Scraped 200 posts from 20 subreddits
```

---

## System Architecture

### Components

1. **Cookie Manager** (`intel/cookie_manager.py`)
   - Centralized cookie storage
   - Platform-specific header generation
   - Cookie validation

2. **Auto Extractor** (`tools/cookie_extractor.py`)
   - Interactive browser automation
   - Automatic cookie detection
   - Secure .env storage

3. **Source Integration** (e.g., `intel/reddit_source.py`)
   - Uses cookie manager for headers
   - Fallback to unauthenticated mode
   - Rate-limit protection

---

## Cookie Manager API

### Basic Usage

```python
from intel.cookie_manager import get_cookie_manager

cm = get_cookie_manager()
```

### Check Cookie Availability

```python
if cm.validate_cookie('reddit'):
    print("✅ Reddit cookie available")
else:
    print("❌ Need to extract Reddit cookie")
```

### Get Platform Headers

```python
# Reddit
headers = cm.get_headers_for_reddit()
# Returns: {'User-Agent': '...', 'Cookie': 'reddit_session=...', ...}

# Twitter
headers = cm.get_headers_for_twitter()
# Returns: {'User-Agent': '...', 'Cookie': 'auth_token=...; ct0=...', 'x-csrf-token': '...'}

# Medium
headers = cm.get_headers_for_medium()

# LinkedIn
headers = cm.get_headers_for_linkedin()
```

---

## Auto Cookie Extractor

### Command-Line Usage

```bash
python tools/cookie_extractor.py
```

**Interactive Menu:**
```
Select platforms to extract cookies from:
  1. Essential (Reddit + Twitter) - Recommended for Phase 1
  2. All available platforms
  3. Custom selection

Enter choice (1-3): 1
```

### Programmatic Usage

```python
from tools.cookie_extractor import CookieExtractor
import asyncio

async def main():
    extractor = CookieExtractor()
    
    # Extract specific platforms
    await extractor.extract_all(platforms=['reddit', 'twitter'])

asyncio.run(main())
```

---

## Source Integration Example

### Reddit Source (Already Integrated)

```python
from intel.reddit_source import RedditSource

# Cookie automatically used if available
reddit = RedditSource()

# Logs will show:
# ✅ RedditSource initialized (20 subreddits, with cookie)
# OR
# ⚠️  No Reddit cookie found. Scraping may be rate-limited.
#    Run: python tools/cookie_extractor.py
```

### Implementation Pattern

```python
from intel.cookie_manager import get_cookie_manager

class MySource(BaseContentSource):
    def __init__(self):
        super().__init__()
        
        # Get cookie manager
        self.cookie_manager = get_cookie_manager()
        
        # Check cookie availability
        has_cookie = self.cookie_manager.validate_cookie('platform_name')
        
        if not has_cookie:
            logger.warning("No cookie - may be rate-limited")
    
    def _get_headers(self) -> dict:
        """Get authenticated headers"""
        return self.cookie_manager.get_headers_for_platform()
    
    async def fetch_latest(self):
        headers = self._get_headers()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                # ... scraping logic
```

---

## Supported Platforms

| Platform | Cookie Names | Status | Phase |
|----------|--------------|--------|-------|
| **Reddit** | `reddit_session` | ✅ Ready | 1 |
| **Twitter/X** | `auth_token`, `ct0` | ✅ Ready | 1 |
| **Medium** | `sid` | ✅ Ready | 2 |
| **Substack** | `substack.sid` | ✅ Ready | 2 |
| LinkedIn | `li_at` | 🔜 Coming | 3 |
| YouTube | `SAPISID` | 🔜 Coming | 3 |
| GitHub | `user_session` | 🔜 Coming | 3 |
| Product Hunt | `_producthunt_session` | 🔜 Coming | 3 |

---

## Environment Variables

Cookies are stored in `apps/worker/.env`:

```env
# === COOKIES ===

REDDIT_COOKIE=your_reddit_session_cookie
TWITTER_COOKIE=your_auth_token_cookie
TWITTER_CT0=your_ct0_csrf_token
MEDIUM_COOKIE=your_medium_sid_cookie
SUBSTACK_COOKIE=your_substack_sid_cookie
```

**⚠️ Never commit .env to git!**

Already in `.gitignore`:
```
apps/worker/.env
.env
*.env
```

---

## Security Best Practices

### 1. Use Throwaway Accounts

❌ **DON'T:**
- Use main personal accounts
- Use accounts with sensitive data

✅ **DO:**
- Create dedicated scraper accounts
- Use temporary email addresses
- Use strong unique passwords

### 2. Cookie Rotation Schedule

- **Reddit:** Every 30 days
- **Twitter:** Every 14 days
- **Medium:** Every 60 days

**Re-extract:**
```bash
python tools/cookie_extractor.py
```

### 3. Secure Storage

```bash
# Verify .env is gitignored
git check-ignore apps/worker/.env

# Set strict permissions (Linux/Mac)
chmod 600 apps/worker/.env
```

---

## Troubleshooting

### Cookie not detected

**Problem:**
```
⚠️  Could not detect cookies for Reddit
```

**Solutions:**
1. Make sure fully logged in (see username top-right)
2. Wait longer (up to 5 minutes)
3. Re-run extractor

### Browser doesn't open

**Problem:**
```
Error: Browser type 'chromium' is not installed
```

**Solution:**
```bash
playwright install chromium
```

### Invalid cookie

**Symptoms:**
- 403 Forbidden errors
- Empty results
- "Not logged in" messages

**Solution:**
```bash
# Re-extract cookies
python tools/cookie_extractor.py
```

---

## Testing

### Test Cookie Manager

```bash
python test_cookie_manager.py
```

### Test Reddit Source

```bash
python test_batch1_sources.py
```

### Verify Cookies

```python
from intel.cookie_manager import get_cookie_manager

cm = get_cookie_manager()

# Check all platforms
for platform in ['reddit', 'twitter', 'medium']:
    valid = cm.validate_cookie(platform)
    print(f"{platform}: {valid}")
```

---

## Advanced Usage

### Custom Cookie Path

```python
from pathlib import Path
from tools.cookie_extractor import CookieExtractor

# Use custom .env location
extractor = CookieExtractor(
    env_path=Path('/custom/path/.env')
)

await extractor.extract_all()
```

### Manual Cookie Addition

If auto-extractor doesn't work, manually add to `.env`:

```env
# Get cookie from browser DevTools (F12 -> Application -> Cookies)
REDDIT_COOKIE=paste_cookie_value_here
```

### Validate Specific Cookie

```python
from intel.cookie_manager import get_cookie_manager

cm = get_cookie_manager()

if cm.validate_cookie('reddit'):
    cookie = cm.get_reddit_cookie()
    print(f"Cookie length: {len(cookie)}")
    print(f"Cookie preview: ***{cookie[-20:]}")
```

---

## Next Steps

1. ✅ **Extract cookies** for Phase 1 (Reddit + Twitter)
2. ✅ **Test Reddit source** with authenticated scraping
3. 🔄 **Build Twitter source** with cookie authentication
4. 🔄 **Monitor cookie validity** and rotate as needed

---

## Documentation

- **Full Guide:** [AUTO-COOKIE-EXTRACTION.md](../docs/AUTO-COOKIE-EXTRACTION.md)
- **Cookie Strategy:** [COOKIE-STRATEGY.md](../docs/COOKIE-STRATEGY.md)
- **Phase 1 Sources:** [PHASE1-SOURCES.md](../docs/PHASE1-SOURCES.md)

---

**🎉 Cookie authentication system ready!** 🍪
