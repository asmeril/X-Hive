# JSON Cookie System - Setup & Usage Guide

## Overview

The X-Hive content scraper now supports **EditThisCookie JSON exports** for authentication. This allows you to use your own browser cookies to access restricted content on Medium, Perplexity, Reddit, Twitter, and other platforms.

## Why JSON Cookies?

- ✅ **403 Resolution**: Medium, Perplexity block scrapers - real browser cookies work
- ✅ **No Complex Auth**: No need for OAuth, JWT tokens, or API credentials
- ✅ **Browser-Based**: Export cookies directly from where you're logged in
- ✅ **Fallback Support**: If JSON missing, system falls back to `.env` automatically
- ✅ **Secure**: Cookies protected in `.gitignore`, stay on local machine only

## Quick Start (2 minutes)

### 1. Install EditThisCookie Extension

**Chrome/Chromium:**
- Visit: https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg
- Click "Add to Chrome"

**Firefox:**
- Visit: https://addons.mozilla.org/en-US/firefox/addon/editthistcookie/
- Click "Add to Firefox"

### 2. Export Cookies for One Site

**Example: Medium**

1. Visit https://medium.com (logged in)
2. Click EditThisCookie icon (top-right of browser)
3. Click **Export** button
4. JSON array appears → copy it
5. Create file: `apps/worker/cookies/medium.json`
6. Paste the JSON array
7. Done! Medium scraper now has authentication

### 3. Repeat for Other Sites (Optional)

Supported sites: `reddit`, `twitter`, `medium`, `perplexity`, `substack`, `linkedin`, `github`, `producthunt`, `youtube`

Each gets its own JSON file in `apps/worker/cookies/` directory.

## How It Works

```
Browser (You logged in)
    ↓ EditThisCookie Export
    ↓ JSON Array of cookies
    ↓ Save to cookies/{site}.json
    ↓
CookieLoader
    ↓ Parse JSON file
    ↓ Extract name/value pairs
    ↓ Cache in memory
    ↓
CookieManager
    ↓ Check JSON first (if available)
    ↓ Fall back to .env (if JSON missing)
    ↓ Provide headers/dict
    ↓
Scrapers (Medium, Perplexity, etc.)
    ↓ Use headers in HTTP requests
    ↓ Authenticated = 200 OK instead of 403
    ↓ Content fetched successfully
```

## File Structure

```
apps/worker/
├── cookies/                    # JSON cookie files
│   ├── .gitkeep               # Placeholder (always tracked)
│   ├── README.md              # Setup instructions
│   ├── medium.json            # Medium cookies (ignored by git)
│   ├── twitter.json           # Twitter cookies (ignored by git)
│   ├── reddit.json            # Reddit cookies (ignored by git)
│   ├── perplexity.json        # Perplexity cookies (ignored by git)
│   └── substack.json          # Substack cookies (ignored by git)
├── intel/
│   ├── cookie_loader.py       # Loads JSON, manages cache
│   ├── cookie_manager.py      # Integrates JSON + .env
│   ├── medium_scraper.py      # Uses get_headers_for_site('medium')
│   ├── twitter_source.py      # Uses get_headers_for_site('twitter')
│   └── ...
└── .env                       # Fallback .env variables (tracked)
```

## Step-by-Step: Export for Each Site

### Medium

```
1. Go to https://medium.com
2. Logged in? Check top-right corner
3. Click EditThisCookie icon
4. Click "Export"
5. Select all JSON text (Ctrl+A)
6. Copy (Ctrl+C)
7. Create new file: apps/worker/cookies/medium.json
8. Paste (Ctrl+V)
9. Save
10. Test: python -c "from intel.cookie_manager import get_cookie_manager; cm = get_cookie_manager(); print(cm.get_headers_for_site('medium'))"
```

Expected output shows `Cookie: ...` header with multiple Medium cookies.

### Twitter/X

```
1. Go to https://twitter.com
2. Logged in? Check top-right (profile icon)
3. Click EditThisCookie icon
4. Click "Export"
5. Copy JSON array
6. Create: apps/worker/cookies/twitter.json
7. Paste JSON array
8. Save
```

### Reddit

```
1. Go to https://reddit.com
2. Logged in? Check top-right
3. Click EditThisCookie icon
4. Click "Export"
5. Copy JSON array
6. Create: apps/worker/cookies/reddit.json
7. Paste JSON array
8. Save
```

### Perplexity

```
1. Go to https://www.perplexity.ai
2. Logged in? Check top-right
3. Click EditThisCookie icon
4. Click "Export"
5. Copy JSON array
6. Create: apps/worker/cookies/perplexity.json
7. Paste JSON array
8. Save
```

### Substack

```
1. Go to https://substack.com
2. Logged in? Check top-right
3. Click EditThisCookie icon
4. Click "Export"
5. Copy JSON array
6. Create: apps/worker/cookies/substack.json
7. Paste JSON array
8. Save
```

## Verification

Test if cookies are being loaded:

```bash
cd apps/worker

# Check if JSON cookies exist
ls cookies/*.json

# Test Reddit cookies
python -c "from intel.cookie_manager import get_cookie_manager; cm = get_cookie_manager(); print('Reddit headers:'); print(cm.get_headers_for_site('reddit'))"

# Test Medium cookies
python -c "from intel.cookie_manager import get_cookie_manager; cm = get_cookie_manager(); print('Medium headers:'); print(cm.get_headers_for_site('medium'))"

# Check what's in a cookie file
python -c "import json; data = json.load(open('cookies/medium.json')); print(f'Medium has {len(data)} cookies')"
```

## Troubleshooting

### "Cookie file not found" warning
- File doesn't exist yet → export it using EditThisCookie
- Filename wrong → should be lowercase (e.g., `reddit.json` not `Reddit.json`)
- Wrong location → must be in `apps/worker/cookies/` directory

### 403 errors still happening
- Cookies expired → re-export with EditThisCookie
- Logged out → log back in to site, then re-export
- Wrong site → double-check domain name matches
- Multiple exports → some sites set multiple cookie names/values

### How to verify JSON format

```bash
# Check if JSON is valid
python -c "import json; json.load(open('apps/worker/cookies/medium.json')); print('Valid JSON')"

# See what's inside
python -c "import json; data = json.load(open('apps/worker/cookies/medium.json')); print(f'Cookies: {[c[\"name\"] for c in data]}')"
```

Expected output:
```
Cookies: ['__stripe_mid', 'sid', 'user_session', 'logged_in', ...]
```

## Security Best Practices

⚠️ **IMPORTANT:**

1. **Never commit** `cookies/*.json` (protected by `.gitignore`)
2. **Never share** these files - they contain real auth credentials
3. **Never upload** to cloud services unencrypted
4. **Local only** - keep on your machine only
5. **Rotate regularly** - re-export every 30-60 days
6. **Private repository** - ensure GitHub repo is private
7. **Check `.gitignore`** - verify JSON files are excluded:
   ```bash
   git status  # Should show no .json files from cookies/
   ```

## How It Integrates

Each scraper automatically uses the system:

```python
# In your scraper code:
from intel.cookie_manager import get_cookie_manager

cm = get_cookie_manager()

# Automatic: tries JSON cookies → falls back to .env
headers = cm.get_headers_for_site('medium')

# Headers now include:
# {
#   'User-Agent': '...',
#   'Cookie': 'cookie1=value1; cookie2=value2; ...',
#   'Accept': '*/*',
#   ...
# }
```

No other changes needed!

## Fallback System

If you don't provide JSON cookies:

1. CookieLoader checks: `cookies/site.json` - NOT FOUND
2. CookieManager checks: `.env` variables - FOUND (if set)
3. Falls back to `.env` cookie (backward compatible)
4. If neither exist: uses default headers (no auth)

**Result:** Zero breaking changes. Old `.env` system still works.

## Performance

- **Memory:** Cookies cached after first load (~100KB for all sites)
- **Disk:** Each JSON file ~5-50KB
- **Speed:** No performance impact - cached in memory

## Limitations

- **Cookies expire:** 30-180 days typically (re-export when needed)
- **Site-specific:** Medium cookies don't work on Twitter
- **Format depends:** EditThisCookie format is standardized but may vary
- **Browser required:** Must export from logged-in browser session

## Next Steps

1. ✅ Install EditThisCookie extension
2. ✅ Export cookies for sites you want to scrape
3. ✅ Save to `apps/worker/cookies/{site}.json`
4. ✅ Run scrapers - they now have authentication
5. ✅ Monitor for 403 errors - if seen, re-export cookies

## Example: Fixing Medium 403

**Before:**
```
Medium: 0 items (HTTP 403)
```

**Steps:**
1. Install EditThisCookie
2. Visit medium.com (logged in)
3. Export → save to `apps/worker/cookies/medium.json`
4. Run scraper again

**After:**
```
Medium: 8 items (HTTP 200)
```

## Questions?

See the system logs for details:

```bash
# Run scraper with debug logging
DEBUG=1 python -c "from intel.medium_scraper import MediumScraper; ..."

# Check logs
tail -f logs/scraper.log

# Look for:
# "✅ Using JSON cookies for medium" → working
# "⚠️ Cookie file not found" → need to export
# "❌ Invalid JSON" → corrupted file
```

---

**Last Updated:** February 2026  
**Version:** 1.0  
**Status:** Production Ready
