# X-Daemon Core

Main orchestrator for ChromePool, TaskQueue, and X (Twitter) operations in X-HIVE worker.

## Overview

X-Daemon is the core orchestrator that:
- **Manages lifecycle** of ChromePool and TaskQueue
- **Implements X operations** (post, reply, like, retweet)
- **Executes tasks** routed from TaskQueue
- **Monitors health** of all components
- **Persists state** to disk for recovery

## Architecture

```
XDaemon (Singleton)
├── ChromePool (persistent browser)
├── TaskQueue (sequential execution)
├── LockManager (file-based locking)
├── DaemonState (status tracking)
└── X Operations
    ├── post_tweet()
    ├── reply_to_tweet()
    ├── like_tweet()
    └── retweet()
```

## Features

✅ **Singleton Pattern** - One daemon instance  
✅ **Lifecycle Management** - start/stop/restart  
✅ **X Operations** - Full Twitter automation  
✅ **Task Execution** - Routes tasks from queue  
✅ **Health Monitoring** - Tracks component status  
✅ **State Persistence** - Saves stats to disk  
✅ **Retry Logic** - Max 2 retries per operation  
✅ **Error Handling** - Graceful degradation  

## Data Models

### DaemonState

```python
@dataclass
class DaemonState:
    status: str = "stopped"                    # "running" or "stopped"
    started_at: Optional[datetime] = None      # Start timestamp
    stopped_at: Optional[datetime] = None      # Stop timestamp
    total_operations: int = 0                  # Total ops executed
    successful_operations: int = 0             # Successful ops
    failed_operations: int = 0                 # Failed ops
```

Saved to: `C:\XHive\data\daemon_state.json`

## API Reference

### Lifecycle Management

#### Start Daemon

```python
result = await daemon.start()
# {
#     "status": "running",
#     "started_at": "2026-01-21T10:30:45.123456+00:00"
# }
```

**Actions:**
1. Load previous state
2. Initialize ChromePool
3. Start TaskQueue
4. Update daemon status
5. Save state

**Raises:**
- `XDaemonError`: If startup fails

#### Stop Daemon

```python
result = await daemon.stop()
# {
#     "status": "stopped",
#     "stopped_at": "2026-01-21T10:35:45.123456+00:00"
# }
```

**Actions:**
1. Stop TaskQueue
2. Shutdown ChromePool
3. Update daemon status
4. Save state

#### Restart Daemon

```python
result = await daemon.restart()
# {
#     "status": "restarted",
#     "stopped": {...},
#     "started": {...}
# }
```

Stops then starts the daemon with 2-second pause.

#### Get Status

```python
status = await daemon.get_status()
# {
#     "daemon_status": "running",
#     "chrome_pool_healthy": true,
#     "queue_stats": {
#         "pending": 5,
#         "running": 1,
#         "completed": 10,
#         "failed": 1,
#         "total": 17
#     },
#     "uptime_seconds": 300,
#     "last_operation": {
#         "task_id": "uuid",
#         "task_type": "post_tweet",
#         "timestamp": "2026-01-21T10:35:00",
#         "success": true
#     },
#     "operations": {
#         "total": 100,
#         "successful": 80,
#         "failed": 20
#     }
# }
```

### X Operations

#### Post Tweet

```python
result = await daemon.post_tweet(
    text="Hello, X!",
    images=["C:/path/to/image.png"]  # Optional
)
# {
#     "success": true,
#     "tweet_url": "https://x.com/...",
#     "text": "Hello, X!"
# }
```

**Process:**
1. Navigate to x.com/home
2. Click compose box
3. Type tweet text
4. Upload images (if provided)
5. Click post button
6. Wait for confirmation

**Retry:** Max 2 retries on failure

#### Reply to Tweet

```python
result = await daemon.reply_to_tweet(
    tweet_url="https://x.com/user/status/12345",
    text="Great tweet!"
)
# {
#     "success": true,
#     "reply_url": "https://x.com/...",
#     "text": "Great tweet!"
# }
```

**Process:**
1. Navigate to tweet URL
2. Click reply button
3. Type reply text
4. Click post button
5. Wait for confirmation

#### Like Tweet

```python
result = await daemon.like_tweet(
    tweet_url="https://x.com/user/status/12345"
)
# {
#     "success": true,
#     "tweet_url": "https://x.com/user/status/12345"
# }
```

**Process:**
1. Navigate to tweet URL
2. Find like button
3. Click like button
4. Wait for confirmation

#### Retweet

```python
result = await daemon.retweet(
    tweet_url="https://x.com/user/status/12345"
)
# {
#     "success": true,
#     "tweet_url": "https://x.com/user/status/12345"
# }
```

**Process:**
1. Navigate to tweet URL
2. Click retweet button
3. Confirm retweet
4. Wait for confirmation

### Task Execution

#### Execute Task

```python
result = await daemon.execute_task(task)
# {
#     "success": true,
#     "tweet_url": "...",
#     "error": null
# }
```

Routes task to appropriate operation based on `task.type`:
- `"post_tweet"` → `post_tweet()`
- `"reply"` → `reply_to_tweet()`
- `"like"` → `like_tweet()`
- `"retweet"` → `retweet()`

**Called by:** TaskQueue for each queued task

**Updates:**
- Increments `total_operations`
- Increments `successful_operations` or `failed_operations`
- Updates `last_operation`
- Saves state

## FastAPI Endpoints

### Daemon Lifecycle

```
GET  /daemon/status     - Get daemon status
POST /daemon/start      - Start daemon
POST /daemon/stop       - Stop daemon
POST /daemon/restart    - Restart daemon
```

### X Operations

```
POST /x/post            - Post a tweet
  Query: text, images (optional)

POST /x/reply           - Reply to a tweet
  Query: tweet_url, text

POST /x/like            - Like a tweet
  Query: tweet_url

POST /x/retweet         - Retweet a tweet
  Query: tweet_url
```

## Playwright Selectors

X.com element selectors (may need adjustment):

```python
SELECTORS = {
    "tweet_compose": 'div[data-testid="tweetTextarea_0"]',
    "post_button": 'div[data-testid="tweetButtonInline"]',
    "reply_button": 'div[data-testid="reply"]',
    "like_button": 'div[data-testid="like"]',
    "retweet_button": 'div[data-testid="retweet"]',
    "retweet_confirm": 'div[data-testid="retweetConfirm"]',
    "tweet_text": 'div[data-testid="tweetText"]',
    "upload_button": 'input[data-testid="fileInput"]',
}
```

**Note:** X.com may change these selectors. Retry logic handles failures.

## Integration Flow

```
1. User calls /x/post endpoint (or adds task to queue)
   ↓
2. If direct call: XDaemon.post_tweet()
   If queued: TaskQueue → XDaemon.execute_task() → XDaemon.post_tweet()
   ↓
3. XDaemon gets page from ChromePool
   ↓
4. Playwright automation executes
   ↓
5. Retry logic handles failures (max 2 retries)
   ↓
6. Result returned
   ↓
7. Statistics updated
   ↓
8. State saved to disk
```

## Error Handling

### Retry Logic

All X operations retry up to 2 times:

```python
for attempt in range(1, max_retries + 1):
    try:
        # Perform operation
        return {"success": True, ...}
    except Exception as e:
        if attempt == max_retries:
            return {"success": False, "error": str(e)}
        await asyncio.sleep(2)  # Wait before retry
```

### Error Types

- **PlaywrightTimeoutError**: Element not found (selector issue)
- **ChromePoolError**: Browser unavailable
- **XDaemonError**: Daemon operation failed

### Graceful Degradation

- If ChromePool fails, daemon logs error but continues
- If TaskQueue fails, daemon saves state and shuts down
- State persistence ensures recovery on restart

## State Persistence

State saved to `C:\XHive\data\daemon_state.json`:

```json
{
  "status": "stopped",
  "started_at": "2026-01-21T10:30:45.123456+00:00",
  "stopped_at": "2026-01-21T10:35:45.123456+00:00",
  "total_operations": 100,
  "successful_operations": 80,
  "failed_operations": 20,
  "last_operation": {
    "task_id": "uuid",
    "task_type": "post_tweet",
    "timestamp": "2026-01-21T10:35:00",
    "success": true
  }
}
```

**Auto-saved:**
- On daemon start
- On daemon stop
- After each operation

**Auto-loaded:**
- On daemon start (preserves stats across restarts)

## Configuration

From `config.py`:

```python
LOCK_PATH = r"C:\XHive\locks\x_session.lock"
DATA_PATH = r"C:\XHive\data"
BROWSER_DATA_DIR = r"C:\XHive\browser_data"
CHROME_HEADLESS = False
```

Daemon-specific settings (in x_daemon.py):

```python
max_retries = 2                  # Max retry attempts per operation
operation_timeout = 30           # Seconds for operation timeout
element_wait_timeout = 10000     # Milliseconds for element wait
```

## Health Monitoring

Daemon monitors:
- **ChromePool health**: `chrome_pool.is_healthy()`
- **TaskQueue status**: `task_queue.get_queue_status()`
- **Uptime**: Seconds since daemon start
- **Operations**: Total/successful/failed counts
- **Last operation**: Most recent task executed

## Usage Example

```python
import asyncio
from x_daemon import XDaemon

async def main():
    daemon = XDaemon()
    
    try:
        # Start daemon
        await daemon.start()
        
        # Post a tweet
        result = await daemon.post_tweet("Hello from X-Daemon!")
        print(f"Tweet result: {result}")
        
        # Get status
        status = await daemon.get_status()
        print(f"Daemon uptime: {status['uptime_seconds']}s")
        
    finally:
        await daemon.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing

Run test script:

```bash
cd C:\XHive\X-Hive\apps\worker
python test_x_daemon.py
```

Test coverage:
- Singleton pattern
- Lifecycle methods (start/stop/restart)
- State persistence (save/load)
- Status retrieval
- Error handling

## Integration with TaskQueue

TaskQueue automatically routes tasks to XDaemon:

```python
# In task_queue.py
from x_daemon import XDaemon

daemon = XDaemon()
result = await daemon.execute_task(task)
```

Task types supported:
- `"post_tweet"` → payload: `{"text": str, "images": list}`
- `"reply"` → payload: `{"tweet_url": str, "text": str}`
- `"like"` → payload: `{"tweet_url": str}`
- `"retweet"` → payload: `{"tweet_url": str}`

## Logging

All operations are logged:

```
🚀 Starting X-Daemon...
✅ ChromePool started
✅ TaskQueue started
✅ X-Daemon started successfully
🎯 Executing task: uuid | Type: post_tweet
📝 Posting tweet (attempt 1/2)
✅ Tweet posted successfully
🛑 Stopping X-Daemon...
✅ X-Daemon stopped successfully
```

## Performance Notes

- **First operation**: ~5-10s (browser navigation)
- **Subsequent operations**: ~2-5s (page already loaded)
- **Retry delay**: 2 seconds between attempts
- **State save**: <100ms (async file write)

## Troubleshooting

### Selectors not working
- X.com may have changed element attributes
- Update `SELECTORS` dictionary with new values
- Check browser console for correct selectors

### Operations timing out
- Increase `element_wait_timeout`
- Check internet connection
- Verify X.com is accessible

### Daemon won't start
- Check ChromePool initialization
- Verify TaskQueue is available
- Check logs for specific error

### State not persisting
- Verify `C:\XHive\data` directory exists
- Check file permissions on daemon_state.json
- Ensure `_save_state()` is called

## References

- [Playwright Python Documentation](https://playwright.dev/python/)
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [X.com (Twitter) Web App](https://x.com)
