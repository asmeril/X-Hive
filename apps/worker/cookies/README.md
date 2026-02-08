# Cookie Management System

This directory contains browser cookies exported from Chrome/Firefox using the **EditThisCookie** extension.

## Setup Instructions

### 1. Install EditThisCookie Extension

**Chrome:**
- Visit: https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg
- Click "Add to Chrome"

**Firefox:**
- Visit: https://addons.mozilla.org/en-US/firefox/addon/editthistcookie/
- Click "Add to Firefox"

### 2. Export Cookies for Each Site

#### For Reddit:
1. Go to https://reddit.com
2. Make sure you're logged in
3. Click EditThisCookie icon → Export
4. Copy the JSON array
5. Save to `reddit.json` in this directory

#### For Twitter/X:
1. Go to https://twitter.com
2. Make sure you're logged in
3. Click EditThisCookie icon → Export
4. Copy the JSON array
5. Save to `twitter.json` in this directory

#### For Medium:
1. Go to https://medium.com
2. Make sure you're logged in
3. Click EditThisCookie icon → Export
4. Copy the JSON array
5. Save to `medium.json` in this directory

#### For Perplexity:
1. Go to https://www.perplexity.ai
2. Make sure you're logged in
3. Click EditThisCookie icon → Export
4. Copy the JSON array
5. Save to `perplexity.json` in this directory

#### For Substack:
1. Go to https://substack.com
2. Make sure you're logged in
3. Click EditThisCookie icon → Export
4. Copy the JSON array
5. Save to `substack.json` in this directory

### 3. Cookie File Format

Each cookie file must be a JSON array exported by EditThisCookie. The format looks like:

```json
[
    {
        "domain": ".reddit.com",
        "expirationDate": 1704067200,
        "flag": false,
        "httpOnly": true,
        "name": "reddit_session",
        "path": "/",
        "sameSite": "No_Restriction",
        "secure": true,
        "session": false,
        "storeId": "0",
        "value": "YOUR_SESSION_VALUE_HERE"
    },
    {
        "domain": ".reddit.com",
        "expirationDate": 1735689600,
        "flag": false,
        "httpOnly": false,
        "name": "token_v2",
        "path": "/",
        "sameSite": "No_Restriction",
        "secure": true,
        "session": false,
        "storeId": "0",
        "value": "YOUR_TOKEN_V2_VALUE_HERE"
    }
]
```

## Supported Sites

The system automatically loads cookies for these sites when available:

- `reddit.json` → Reddit authentication
- `twitter.json` → Twitter/X authentication
- `medium.json` → Medium authentication
- `perplexity.json` → Perplexity authentication
- `substack.json` → Substack authentication
- `linkedin.json` → LinkedIn authentication (optional)
- `github.json` → GitHub authentication (optional)
- `producthunt.json` → Product Hunt authentication (optional)
- `youtube.json` → YouTube authentication (optional)

## How It Works

1. **Cookie Loader** (`apps/worker/intel/cookie_loader.py`):
   - Loads JSON cookie files from this directory
   - Caches them in memory for performance
   - Provides methods to extract cookies in various formats

2. **Cookie Manager Integration** (`apps/worker/intel/cookie_manager.py`):
   - Automatically uses JSON cookies when available
   - Falls back to `.env` environment variables
   - Provides universal `get_headers_for_site(site)` method

3. **Source Integration**:
   - Each scraper can use `get_cookie_manager().get_headers_for_site('site_name')`
   - Headers automatically include all cookies from both `.env` and JSON files
   - No additional configuration needed

## Testing

To verify cookies are loaded correctly:

```bash
cd apps/worker
python -c "from intel.cookie_manager import get_cookie_manager; cm = get_cookie_manager(); print(cm.get_headers_for_site('reddit'))"
```

Should show headers with Cookie field if `reddit.json` exists.

## Security

⚠️ **IMPORTANT:** Cookie files contain sensitive authentication data.

- **DO NOT** commit these files to git (add to `.gitignore`)
- **DO NOT** share these files or their contents
- **DO NOT** expose these files publicly
- Store securely on your local machine only
- Regenerate cookies if they're compromised
- Rotate cookies regularly (~30 days recommended)

## Cookie Expiration

Most browser cookies expire within 30-180 days. If scrapers start failing with 401/403 errors:

1. Re-export cookies using EditThisCookie
2. Replace the JSON files
3. Restart the application

## Troubleshooting

**"Cookie file not found" warning:**
- Ensure the JSON file exists in this directory
- Verify the filename matches exactly (e.g., `reddit.json`)
- Check that JSON format is valid (use online JSON validator)

**Cookies not being used:**
- Verify file has valid JSON format
- Ensure cookies are still valid (not expired)
- Check application logs for "✅ Using JSON cookies"

**403/401 errors persist:**
- Re-export cookies with EditThisCookie
- Log out completely and back in before exporting
- Try incognito mode if using private browsing
- Some sites may require additional anti-bot measures

## Fallback System

If JSON cookies aren't available or invalid:
- System automatically falls back to `.env` environment variables
- Existing `.env` cookies continue to work unchanged
- Zero disruption if JSON files are missing
- Provides smooth transition between cookie systems

---

**Last Updated:** February 2026
**Status:** Active
