# Auto Cookie Extraction Guide 🍪

Complete guide for extracting authentication cookies from multiple platforms automatically.

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Platform Support](#platform-support)
- [Detailed Instructions](#detailed-instructions)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)

---

## Overview

The X-Hive Auto Cookie Extractor is an interactive tool that:

1. **Opens browser** for each platform
2. **Waits for you** to login manually
3. **Detects cookies** automatically
4. **Saves to .env** file securely

**No manual cookie copying needed!**

---

## Quick Start

### Prerequisites

1. **Install Playwright browsers:**
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **Verify installation:**
   ```bash
   python -c "from playwright.sync_api import sync_playwright; print('✅ OK')"
   ```

### Run Extractor

```bash
cd apps/worker
python tools/cookie_extractor.py
```

**Interactive Menu:**
```
🍪 X-Hive Cookie Extractor

Select platforms to extract cookies from:
  1. Essential (Reddit + Twitter) - Recommended for Phase 1
  2. All available platforms
  3. Custom selection

Enter choice (1-3): 
```

**Recommended: Choose Option 1** (Reddit + Twitter)

---

## Platform Support

| Platform | Cookie Names | Status | Phase |
|----------|--------------|--------|-------|
| **Reddit** | `reddit_session` | ✅ Ready | Phase 1 |
| **Twitter/X** | `auth_token`, `ct0` | ✅ Ready | Phase 1 |
| **Medium** | `sid` | ✅ Ready | Phase 2 |
| **Substack** | `substack.sid` | ✅ Ready | Phase 2 |
| LinkedIn | `li_at` | 🔜 Coming | Phase 3 |
| YouTube | `SAPISID` | 🔜 Coming | Phase 3 |
| GitHub | `user_session` | 🔜 Coming | Phase 3 |
| Product Hunt | `_producthunt_session` | 🔜 Coming | Phase 3 |

---

## Detailed Instructions

### 1. Reddit Cookie Extraction

**What to expect:**
1. Browser opens to `https://old.reddit.com/login`
2. You login with throwaway account
3. Cookie auto-detected when homepage loads
4. Browser closes automatically

**Step-by-step:**

```
🌐 PLATFORM: Reddit
═══════════════════════════════════════════════════════

📋 Instructions:
1. Click 'Log in' button (top right)
2. Enter username and password
3. Click 'Log in'
4. Wait for homepage to load
5. Browser will auto-close when cookie is captured

Press ENTER to open Reddit browser...
```

**Login:**
- Use **throwaway account** (not your main!)
- Username: `x_hive_scraper` (example)
- Password: `SecurePass123!`

**Success indicators:**
```
✅ Cookies detected for Reddit!
✅ Successfully extracted 1 cookie(s) from Reddit:
   • reddit_session
```

---

### 2. Twitter/X Cookie Extraction

**What to expect:**
1. Browser opens to `https://twitter.com/i/flow/login`
2. You login with throwaway account
3. Two cookies auto-detected: `auth_token` + `ct0`
4. Browser closes automatically

**Step-by-step:**

```
🌐 PLATFORM: Twitter/X
═══════════════════════════════════════════════════════

📋 Instructions:
1. Enter phone/email/username
2. Click 'Next'
3. Enter password
4. Click 'Log in'
5. Complete any verification if prompted
6. Wait for home feed to load
7. Browser will auto-close when cookies are captured
```

**Login:**
- Use **throwaway account**
- Phone/Email: `xhive.bot@protonmail.com` (example)
- Password: `SecurePass123!`

**Verification:**
- You may be asked to verify phone/email
- Complete verification steps
- Wait for home feed to fully load

**Success indicators:**
```
✅ Cookies detected for Twitter/X!
✅ Successfully extracted 2 cookie(s) from Twitter/X:
   • auth_token
   • ct0
```

---

### 3. Medium Cookie Extraction

**What to expect:**
1. Browser opens to `https://medium.com/m/signin`
2. You sign in with Google or email
3. Cookie auto-detected when homepage loads

**Login options:**
- **Google Sign-In** (recommended for throwaway accounts)
- **Email Sign-In** (magic link sent to email)

**Success indicators:**
```
✅ Cookies detected for Medium!
✅ Successfully extracted 1 cookie(s) from Medium:
   • sid
```

---

### 4. Substack Cookie Extraction

**What to expect:**
1. Browser opens to `https://substack.com/sign-in`
2. You enter email and click magic link
3. Cookie auto-detected after verification

**Step-by-step:**
1. Enter your email
2. Click "Continue"
3. **Check your email inbox**
4. Click the magic link in email
5. Return to browser window
6. Wait for homepage to load

**Success indicators:**
```
✅ Cookies detected for Substack!
✅ Successfully extracted 1 cookie(s) from Substack:
   • substack.sid
```

---

## Extraction Summary

After all platforms complete:

```
═══════════════════════════════════════════════════════
📊 EXTRACTION SUMMARY
═══════════════════════════════════════════════════════

✅ Reddit              : 1 cookie(s)
   • reddit_session
✅ Twitter/X           : 2 cookie(s)
   • auth_token
   • ct0

═══════════════════════════════════════════════════════
✅ COOKIE EXTRACTION COMPLETE!
═══════════════════════════════════════════════════════

🔄 Next steps:
  1. Verify cookies in .env file
  2. Run: python -c "from intel.cookie_manager import get_cookie_manager; get_cookie_manager()"
  3. Run: python test_batch1_sources.py
```

---

## Saved Cookies (.env file)

After extraction, cookies are saved to `apps/worker/.env`:

```env
# === COOKIES ===

REDDIT_COOKIE=your_reddit_session_cookie_here
TWITTER_COOKIE=your_twitter_auth_token_here
TWITTER_CT0=your_twitter_ct0_token_here
MEDIUM_COOKIE=your_medium_sid_cookie_here
SUBSTACK_COOKIE=your_substack_sid_cookie_here
```

**⚠️ NEVER commit .env to git!**

Already added to `.gitignore`:
```
apps/worker/.env
.env
*.env
```

---

## Troubleshooting

### Cookie not detected

**Problem:**
```
⚠️  Could not detect cookies for Reddit
   Expected cookies: reddit_session
   Make sure you're fully logged in!
```

**Solutions:**

1. **Not fully logged in:**
   - Make sure you see your username in top-right corner
   - Navigate to any subreddit to confirm login
   - Wait longer (up to 5 minutes)

2. **Wrong account type:**
   - Some platforms require email verification
   - Use verified throwaway account

3. **Browser closed too early:**
   - Don't close browser manually
   - Let tool detect cookies and close automatically

4. **Re-run extraction:**
   ```bash
   python tools/cookie_extractor.py
   ```

---

### Browser doesn't open

**Problem:**
```
Error: Browser type 'chromium' is not installed
```

**Solution:**
```bash
playwright install chromium
```

**Verify:**
```bash
playwright --version
```

---

### Timeout (5 minutes)

**Problem:**
- You took too long to login
- Verification steps delayed

**Solution:**
- Re-run extractor for that specific platform
- Choose **Option 3** (Custom selection)
- Select only the failed platform

---

### Invalid credentials

**Problem:**
- Wrong password
- Account locked

**Solution:**
1. **Create new throwaway account:**
   - Use temporary email: `guerrillamail.com`, `10minutemail.com`
   - Use strong password
   - Save credentials securely

2. **Re-run extraction**

---

### Cookie already in .env

**Behavior:**
- Tool **overwrites** old cookies with new ones
- Safe to re-run extractor anytime

**Manual cleanup (optional):**
```bash
# Remove all cookies from .env
grep -v "COOKIE\|CT0" apps/worker/.env > temp && mv temp apps/worker/.env
```

---

## Security Best Practices

### 1. Use Throwaway Accounts

**❌ DON'T:**
- Use your main personal accounts
- Use accounts with sensitive data
- Use work/professional accounts

**✅ DO:**
- Create dedicated scraper accounts
- Use temporary email addresses
- Use strong unique passwords

**Example throwaway setup:**
- Email: `xhive.scraper.001@guerrillamail.com`
- Username: `xhive_bot_001`
- Password: `[Generate random 20+ chars]`

---

### 2. Secure .env Storage

**✅ DO:**
```bash
# Verify .env is gitignored
git check-ignore apps/worker/.env
# Should output: apps/worker/.env

# Set strict permissions (Linux/Mac)
chmod 600 apps/worker/.env

# Never commit
git add .env  # ❌ Should fail with gitignore
```

**❌ DON'T:**
- Commit `.env` to git
- Share `.env` file publicly
- Store `.env` in cloud services (Dropbox, Drive)

---

### 3. Cookie Rotation

**Recommended schedule:**
- **Reddit:** Rotate every 30 days
- **Twitter:** Rotate every 14 days
- **Medium:** Rotate every 60 days

**How to rotate:**
```bash
# Re-run extractor
python tools/cookie_extractor.py

# Select platforms to rotate
# Choose Option 3 -> Custom selection
```

---

### 4. Monitor Cookie Validity

**Symptoms of invalid cookie:**
- 403 Forbidden errors
- Empty results from sources
- "Not logged in" messages

**Check validity:**
```bash
python -c "
from intel.cookie_manager import get_cookie_manager

cm = get_cookie_manager()
print(f'Reddit: {cm.validate_cookie(\"reddit\")}')
print(f'Twitter: {cm.validate_cookie(\"twitter\")}')
"
```

**Output:**
```
Reddit: True
Twitter: True
```

---

### 5. Backup Strategy

**Backup .env file:**
```bash
# Encrypted backup (recommended)
gpg -c apps/worker/.env
# Creates: .env.gpg

# Store .env.gpg in secure location
# Delete original: rm apps/worker/.env
```

**Restore from backup:**
```bash
gpg -d .env.gpg > apps/worker/.env
```

---

## Advanced Usage

### Custom Platform Selection

```bash
python tools/cookie_extractor.py
# Choose Option 3

Available platforms:
  1. Reddit
  2. Twitter/X
  3. Medium
  4. Substack

Enter platform numbers separated by commas (e.g., 1,2,4):
> 1,3

✅ Extracting cookies for: reddit, medium
```

---

### Programmatic Extraction

```python
from tools.cookie_extractor import CookieExtractor
import asyncio

async def extract():
    extractor = CookieExtractor()
    
    # Extract only Reddit + Twitter
    await extractor.extract_all(platforms=['reddit', 'twitter'])

asyncio.run(extract())
```

---

### Verify Extracted Cookies

```python
from intel.cookie_manager import get_cookie_manager

cm = get_cookie_manager()

# Check Reddit
if cm.validate_cookie('reddit'):
    headers = cm.get_headers_for_reddit()
    print(f"✅ Reddit headers: {headers}")
else:
    print("❌ No Reddit cookie")

# Check Twitter
if cm.validate_cookie('twitter'):
    headers = cm.get_headers_for_twitter()
    print(f"✅ Twitter headers: {headers}")
else:
    print("❌ No Twitter cookie")
```

---

## Integration with Content Sources

### Reddit Source (Automatic)

```python
from intel.reddit_source import RedditSource

# Cookie manager automatically used
reddit = RedditSource()

# Fetch with authentication
items = await reddit.fetch_latest()
```

**Behind the scenes:**
```python
# In reddit_source.py
def __init__(self):
    self.cookie_manager = get_cookie_manager()

def _get_headers(self):
    return self.cookie_manager.get_headers_for_reddit()
```

---

### Twitter Source (Coming Soon)

```python
from intel.twitter_scraper import TwitterScraper

# Cookie manager automatically used
twitter = TwitterScraper()

# Fetch with authentication
items = await twitter.fetch_viral_tweets()
```

---

## FAQ

### How long do cookies last?

- **Reddit:** ~30 days (with activity)
- **Twitter:** ~30 days (varies)
- **Medium:** ~90 days
- **Substack:** ~90 days

**Re-extract when:**
- 403 Forbidden errors appear
- Source returns no results
- "Login required" messages

---

### Can I use VPN?

**Yes, but:**
- Use **same VPN location** for extraction and scraping
- Avoid frequent VPN changes
- Some platforms may require verification if IP changes

**Recommended:**
- Extract cookies **without VPN**
- Use VPN only if needed for scraping

---

### Multiple accounts per platform?

**Not currently supported**, but planned for Phase 3:

```python
# Future feature
extractor = CookieExtractor()
await extractor.extract_all(
    platforms=['reddit'],
    account_id='account_1'  # Save as REDDIT_COOKIE_1
)
```

---

### Cookie expired mid-scraping?

**Symptoms:**
```
❌ Error scraping r/MachineLearning: 403 Forbidden
```

**Solution:**
```bash
# Re-extract immediately
python tools/cookie_extractor.py
# Choose Option 1 or specific platform

# Re-run scraper
python test_batch1_sources.py
```

---

## Next Steps

After successful extraction:

1. ✅ **Verify cookies loaded:**
   ```bash
   python -c "from intel.cookie_manager import get_cookie_manager; get_cookie_manager()"
   ```

2. ✅ **Test Reddit source:**
   ```bash
   python test_batch1_sources.py
   ```

3. ✅ **Monitor for issues:**
   - Watch for 403 errors
   - Check logs for "No cookie" warnings

4. ✅ **Set calendar reminder:**
   - Reddit cookie rotation: 30 days
   - Twitter cookie rotation: 14 days

---

## Support

**Issues with extraction?**

1. **Check logs:**
   ```bash
   # Verbose mode
   export LOG_LEVEL=DEBUG
   python tools/cookie_extractor.py
   ```

2. **Test Playwright:**
   ```bash
   python -c "
   from playwright.sync_api import sync_playwright
   with sync_playwright() as p:
       browser = p.chromium.launch(headless=False)
       print('✅ Playwright working')
       browser.close()
   "
   ```

3. **Check GitHub Issues:**
   - Search existing issues
   - Create new issue with logs

---

**🎉 Happy Cookie Extraction!** 🍪
