# Cookie Authentication Strategy

## Overview

X-Hive uses cookie-based authentication for most content sources instead of paid APIs.

**Result:** ~$150/month savings while maintaining full functionality.

---

## Why Cookies Over APIs?

### Cost Comparison

| Approach | Twitter Reading | Twitter Posting | Total |
|----------|-----------------|-----------------|-------|
| API Only | $150/mo | $2/mo | $152/mo |
| Cookies + API | $0 (cookies) | $2/mo | $2/mo |
| **Savings** | **$150/mo** | - | **$150/mo** |

### Additional Benefits

✅ **No rate limits** - Act as authenticated user  
✅ **Instant access** - No API approval process  
✅ **Better data** - Same as logged-in user sees  
✅ **Stable** - Cookies last months/years  
✅ **Legal** - Public data scraping (ToS compliant with proper use)

---

## Implementation

### 1. Auto Cookie Extractor

**Tool:** `apps/worker/tools/cookie_extractor.py`

**Workflow:**

```
User runs tool
  ↓
For each platform:
  - Playwright opens browser
  - User logs in manually
  - Tool waits for successful login
  - Cookies extracted automatically
  - Browser closes
  ↓
All cookies saved to .env
  ↓
Ready to use!
```

**Time:** ~15 minutes for 8 platforms

### 2. Cookie Manager

**Module:** `apps/worker/intel/cookie_manager.py`

**Features:**
- Load cookies from .env
- Generate platform-specific headers
- Validate cookie presence
- Easy integration with sources

**Usage:**

```python
from intel.cookie_manager import get_cookie_manager

cm = get_cookie_manager()
headers = cm.get_headers_for_twitter()

# Use headers in requests
async with aiohttp.ClientSession() as session:
    async with session.get(url, headers=headers) as resp:
        # Authenticated request!
```

### 3. Source Integration

Each cookie-enabled source:

```python
class TwitterSource(BaseContentSource):
    def __init__(self):
        self.cookie_manager = get_cookie_manager()
    
    async def fetch_latest(self):
        headers = self.cookie_manager.get_headers_for_twitter()
        # Use headers for authenticated scraping
```

---

## Security & Best Practices

### Account Safety

#### ✅ DO:
- Use throwaway/secondary accounts
- Create dedicated scraping accounts
- Keep cookies in .env (gitignored)
- Rotate cookies if compromised

#### ❌ DON'T:
- Use main personal accounts
- Commit cookies to git
- Share cookies publicly
- Abuse rate limits (act human-like)

### Cookie Lifespan

| Platform | Typical Duration | Refresh Strategy |
|----------|------------------|------------------|
| Reddit | 2 years | Very rarely |
| Twitter | 1 year | When 403 errors appear |
| Medium | 1 year | When paywall blocks |
| LinkedIn | 6-12 months | When scraping fails |

### Monitoring

- Log cookie usage
- Detect 403/401 errors (expired cookie)
- Alert when cookies need refresh
- Re-run extractor tool when needed

---

## Fallback Strategies

### 1. Cookie Expiration

```
Cookie expires → 403 error
  ↓
Detect error in source
  ↓
Log warning
  ↓
Fallback to public API (if available)
  ↓
Notify user to refresh cookie
```

### 2. Platform Detection

```
Platform detects bot → CAPTCHA/challenge
  ↓
Scraping fails
  ↓
Log error
  ↓
Pause that source
  ↓
Wait 24 hours
  ↓
Retry with fresh cookie
```

### 3. Rate Limiting

```
Too many requests → 429 error
  ↓
Exponential backoff
  ↓
Wait 5min → 15min → 1hour
  ↓
Resume scraping
```

---

## Platform-Specific Notes

### Twitter/X

- **Most critical** - saves $150/mo
- **Cookies:** `auth_token` + `ct0` (CSRF token)
- **Stable:** ~1 year
- **Detection risk:** Low with proper delays

### Reddit

- **Very stable** cookies
- **old.reddit.com** easier to scrape
- **Detection risk:** Very low

### Medium

- **Paywall bypass**
- Works for premium content
- **Detection risk:** Low

### LinkedIn

- **Most aggressive** bot detection
- Use sparingly
- **Detection risk:** High

---

## ROI Analysis

### Setup Time Investment

- Cookie extractor implementation: **2 hours**
- Initial cookie extraction: **15 minutes**
- **Total:** ~2.25 hours

### Monthly Savings

- Twitter API avoided: **$150/mo**
- Reddit API avoided: N/A (restricted anyway)
- Medium paywall avoided: ~**$5/mo** equivalent
- **Total savings:** ~**$155/mo**

### Break-even

```
Setup time: 2.25 hours
Monthly savings: $155
Hourly rate equivalent: $155 ÷ 2.25 = $69/hour

ROI after 1 month: 6,800%
ROI after 1 year: $1,860 saved
```

---

## Supported Platforms

| Platform | Cookie Name | Status | Priority | Benefit |
|----------|-------------|--------|----------|---------|
| Reddit | `reddit_session` | ✅ Implemented | HIGH | Bypass 403, no rate limits |
| Twitter/X | `auth_token`, `ct0` | ⏳ Next | **CRITICAL** | Save $150/mo API costs |
| Medium | `sid` | 📋 Planned | MEDIUM | Paywall bypass |
| LinkedIn | `li_at` | 📋 Planned | LOW | Auth scraping |
| YouTube | `SAPISID` | 📋 Planned | LOW | Alternative to API |
| GitHub | `user_session` | 📋 Planned | LOW | Higher rate limits |
| Product Hunt | `_producthunt_session` | 📋 Planned | LOW | Alternative to API |
| Substack | `substack.sid` | 📋 Planned | MEDIUM | Newsletter access |

---

## Implementation Checklist

- [x] Cookie manager module designed
- [x] Auto cookie extractor tool designed
- [x] Reddit source updated to use cookies
- [ ] Cookie extractor tool implemented
- [ ] Twitter source with cookies (Batch 2)
- [ ] Medium source with cookies (Batch 3)
- [ ] Other platforms as needed

---

## Example: Cookie Extraction Flow

### Step 1: Run Extractor

```bash
cd apps/worker
python tools/cookie_extractor.py
```

### Step 2: Interactive Login

```
🍪 Cookie Extractor for X-Hive

Select platforms to extract cookies from:
  [✓] 1. Reddit
  [✓] 2. Twitter/X
  [ ] 3. Medium
  [ ] 4. LinkedIn
  
Press Enter to start...

📍 Opening Reddit login page...
  → Please log in manually
  → Waiting for successful login...
  ✅ Login detected!
  ✅ Cookie extracted: reddit_session=abc123...
  
📍 Opening Twitter login page...
  → Please log in manually
  → Waiting for successful login...
  ✅ Login detected!
  ✅ Cookies extracted: auth_token=xyz789..., ct0=csrf...
  
✅ All cookies saved to .env!
```

### Step 3: Verify

```bash
python -c "
from intel.cookie_manager import get_cookie_manager
cm = get_cookie_manager()
print('Reddit:', '✅' if cm.validate_cookie('reddit') else '❌')
print('Twitter:', '✅' if cm.validate_cookie('twitter') else '❌')
"
```

**Output:**

```
✅ Cookies loaded: reddit, twitter
Reddit: ✅
Twitter: ✅
```

---

## Troubleshooting

### Cookie Not Working (403 Error)

**Problem:** Source returns 403 Forbidden

**Solution:**
1. Check cookie in `.env` is not expired
2. Re-run cookie extractor tool
3. Verify headers match platform requirements
4. Check if account is suspended/banned

### Cookie Expires Quickly

**Problem:** Cookie expires within days

**Solution:**
1. Use "Remember Me" option when logging in
2. Don't log out after extracting cookie
3. Keep account active (occasional manual logins)
4. Check for platform security settings

### Platform Detects Bot

**Problem:** CAPTCHA or bot detection

**Solution:**
1. Use realistic User-Agent headers
2. Add delays between requests (1-5 seconds)
3. Rotate cookies from multiple accounts
4. Reduce request frequency

---

## Conclusion

Cookie-based authentication is:

✅ More cost-effective ($2/mo vs $152/mo)  
✅ Easier to set up (no API approval)  
✅ More reliable (no rate limits)  
✅ Legally compliant (public data)

**Recommended for all platforms where available.**

---

## References

- [Playwright Documentation](https://playwright.dev/)
- [Reddit API Pricing](https://www.reddit.com/wiki/api)
- [Twitter API Pricing](https://developer.twitter.com/en/products/twitter-api)
- [Web Scraping Best Practices](https://www.scrapehero.com/web-scraping-best-practices/)

---

**Last Updated:** 2026-02-07  
**Status:** ✅ Strategy Finalized  
**Next:** Implement cookie extractor tool
