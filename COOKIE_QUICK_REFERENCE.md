# JSON Cookie System - Quick Reference

## 30-Second Setup

1. Install EditThisCookie extension (Chrome/Firefox)
2. Go to website (logged in)
3. Click EditThisCookie → Export
4. Copy JSON array
5. Create file: `apps/worker/cookies/{site}.json`
6. Paste JSON
7. Done!

## Supported Sites & Filenames

| Site | Filename | Purpose |
|------|----------|---------|
| Medium | `medium.json` | Article scraping (403 fix) |
| Perplexity | `perplexity.json` | Discover page scraping (403 fix) |
| Reddit | `reddit.json` | Subreddit scraping |
| Twitter/X | `twitter.json` | Tweet scraping |
| Substack | `substack.json` | Newsletter scraping |
| LinkedIn | `linkedin.json` | Optional (future) |
| GitHub | `github.json` | Optional (future) |
| Product Hunt | `producthunt.json` | Optional (future) |
| YouTube | `youtube.json` | Optional (future) |

## Cookie File Format

```json
[
    {
        "domain": ".medium.com",
        "name": "cookie_name",
        "value": "cookie_value_here",
        ...other fields...
    },
    {
        "domain": ".medium.com",
        "name": "another_cookie",
        "value": "another_value",
        ...
    }
]
```

**Note:** EditThisCookie exports this exact format automatically.

## How to Export

### Chrome
```
1. EditThisCookie icon (top-right)
2. "Export" button
3. Select all (Ctrl+A)
4. Copy (Ctrl+C)
```

### Firefox
```
1. EditThisCookie icon (top-right)
2. "Export" button
3. Select all (Ctrl+A)
4. Copy (Ctrl+C)
```

## System Usage

```python
# Automatic in all scrapers - no code change needed!
from intel.cookie_manager import get_cookie_manager

cm = get_cookie_manager()

# Try JSON cookies first, fall back to .env
headers = cm.get_headers_for_site('medium')

# Use headers in requests
async with session.get(url, headers=headers) as response:
    ...
```

## Verify Installation

```bash
# Check if files exist
ls apps/worker/cookies/*.json

# Check if JSON is valid
python -c "import json; json.load(open('apps/worker/cookies/medium.json')); print('[OK] Valid JSON')"

# See what's loaded
python -c "from intel.cookie_manager import get_cookie_manager; cm = get_cookie_manager(); print(cm.get_headers_for_site('medium'))"
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| 403 errors continue | Re-export cookies, ensure logged in |
| File not found warning | Export cookies using EditThisCookie |
| Invalid JSON error | Check file format, ensure JSON is valid |
| Cookies not used | Check logs for "✅ Using JSON cookies" message |
| After 30+ days not working | Cookies expired - re-export fresh ones |

## Security Checklist

- ✅ Never commit JSON files (check `.gitignore`)
- ✅ Never share these files
- ✅ Keep repo private on GitHub
- ✅ Local machine only
- ✅ Rotate every 30-60 days

Verify no JSON files in git:
```bash
git status  # Should NOT show cookies/*.json
```

## Integration Points

| Component | What It Does |
|-----------|-------------|
| `cookie_loader.py` | Reads JSON files, caches cookies |
| `cookie_manager.py` | Provides unified interface |
| All scrapers | Automatically use system |

No manual integration needed - all scrapers updated already!

## Performance Impact

- Memory: ~100KB for all sites
- Speed: Negligible (cached in memory)
- Disk: ~50KB per site JSON file

## What Happens

```
Your JSON cookies
    ↓ CookieLoader parses them
    ↓ CookieManager provides headers
    ↓ Scraper uses headers
    ↓ Requests sent with authentication
    ↓ 200 OK instead of 403
```

## File Locations

```
apps/worker/
├── cookies/
│   ├── medium.json         ← You create this
│   ├── twitter.json        ← You create this
│   └── README.md           ← Already provided
└── intel/
    ├── cookie_loader.py    ← System component
    ├── cookie_manager.py   ← System component
    └── *_scraper.py        ← Already updated
```

## One-Liner Tests

```bash
# Test Medium
cd apps/worker && python -c "from intel.cookie_manager import get_cookie_manager; cm = get_cookie_manager(); print('Cookie header present:' if 'Cookie' in cm.get_headers_for_site('medium') else 'No cookies')"

# Test all registered sites
cd apps/worker && python -c "from intel.cookie_manager import get_cookie_manager; cm = get_cookie_manager(); sites = ['reddit', 'twitter', 'medium', 'perplexity']; [print(f'{s}: ' + ('YES' if 'Cookie' in cm.get_headers_for_site(s) else 'NO')) for s in sites]"
```

## Next Phase (Phase 2)

- Proxy/VPN rotation
- GitHub advanced auth
- Reddit OAuth flow
- Automatic cookie refresh
- WebDriver-based cookie capture

---

**Questions?** See `JSON_COOKIE_SETUP.md` for detailed guide.
