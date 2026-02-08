# HuggingFace Cookie Setup Guide

## How to Extract Your HuggingFace Cookies

### Step 1: Login to HuggingFace
1. Open your browser and go to https://huggingface.co
2. Login with your credentials
3. Make sure you stay logged in

### Step 2: Extract Cookies Using EditThisCookie
1. Install the **EditThisCookie** extension:
   - Chrome: https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg
   - Firefox: https://addons.mozilla.org/en-US/firefox/addon/edit-this-cookie/

2. On huggingface.co, click the EditThisCookie icon
3. You should see your HuggingFace cookies
4. Click the **Export** button (usually at the bottom)
5. Copy the JSON data

### Step 3: Update Cookie File
1. Open `cookies/huggingface.json`
2. Replace the placeholder values with your actual cookies
3. Paste the exported JSON data

### Example Cookie Format
```json
[
  {
    "domain": ".huggingface.co",
    "expirationDate": 1735689600,
    "hostOnly": false,
    "httpOnly": false,
    "name": "token",
    "path": "/",
    "sameSite": "Lax",
    "secure": true,
    "session": false,
    "storeId": null,
    "value": "YOUR_ACTUAL_TOKEN_HERE"
  },
  ...
]
```

## Key Cookie Names
- `token` - Your HuggingFace API token
- `user-session` - Session identifier
- `hf_session` - HF-specific session cookie

## Testing Your Cookies
Once you've added your cookies, run:
```bash
python -c "from intel.huggingface_source import huggingface_source; import asyncio; print(len(asyncio.run(huggingface_source.fetch_latest())))"
```

If successful, it should print the number of items fetched (should be 50).

## Important Notes
- Cookies are optional - HuggingFace allows public access without authentication
- With authentication, you may get better results or access to private content
- Keep your cookies secret - don't commit them to git
- Cookies expire - refresh them periodically if they stop working

## Troubleshooting
- **"Cookie file not found"** - Create the `cookies/huggingface.json` file with your cookies
- **"0 cookies loaded"** - Check that your JSON is valid and has the correct structure
- **"Still getting 0 items"** - Try without cookies (public access works fine)
