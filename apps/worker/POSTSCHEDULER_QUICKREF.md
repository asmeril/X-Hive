POSTSCHEDULER_QUICKREF.md

# PostScheduler Quick Reference

## Installation
```bash
pip install apscheduler
```

## Basic Usage

### Start Scheduler
```python
from post_scheduler import PostScheduler
import asyncio

async def main():
    scheduler = PostScheduler()
    await scheduler.start()
    # ... runs until stopped
    await scheduler.stop()

asyncio.run(main())
```

### Custom Times
```python
from datetime import time

scheduler = PostScheduler(
    post_times=[time(8, 0), time(14, 0), time(20, 0)]
)
await scheduler.start()
```

### Custom Content
```python
def my_gen(period):  # period: "morning", "afternoon", "evening"
    return f"🌟 Hello from {period}!"

scheduler = PostScheduler(content_generator_func=my_gen)
await scheduler.start()
```

## Common Operations

### Manual Post
```python
# With text
result = await scheduler.trigger_manual_post("Custom message")

# Auto-generated
result = await scheduler.trigger_manual_post()

# Check result
if result['status'] == 'posted':
    print(f"Posted! Task ID: {result['task_id']}")
```

### View Schedule
```python
upcoming = scheduler.get_next_scheduled_posts()
for post in upcoming:
    print(f"{post['time']} at {post['next_run_time']}")
```

### Reschedule
```python
new_times = [time(7, 0), time(12, 0), time(19, 0)]
if scheduler.reschedule(new_times):
    print("Rescheduled!")
```

## Singleton Pattern

### Get/Create Instance
```python
from post_scheduler import get_scheduler, shutdown_scheduler

scheduler = await get_scheduler()
await scheduler.start()

# Later...
scheduler = await get_scheduler()  # Same instance

# On shutdown
await shutdown_scheduler()
```

## Return Values

### trigger_manual_post() / _scheduled_post_job()
```python
{
    "status": "posted" | "skipped" | "timeout" | "auto_skipped" | "failed",
    "draft_id": str,
    "task_id": str or None,
    "risk_level": "low" | "medium" | "high",
    "timestamp": str,  # ISO format
    "scheduled": bool,  # True for jobs, False for manual
    "manual": bool     # True for manual, absent for jobs
}
```

### get_next_scheduled_posts()
```python
[
    {
        "time": "Post at 09:00",
        "job_id": "scheduled_post_09_00",
        "next_run_time": "2026-02-04T09:00:00",
        "timezone": "UTC"
    },
    ...
]
```

## Configuration

### Default Post Times
- 9:00 AM
- 2:00 PM (14:00)
- 8:00 PM (20:00)

### Timeouts
- Scheduled posts: 1 hour (3600s)
- Manual posts: 30 minutes (1800s)

### Time Periods
- Morning: 6 AM - 12 PM
- Afternoon: 12 PM - 6 PM
- Evening: 6 PM - 6 AM

## Logging

Watch scheduler activity:
```bash
# All scheduler logs
grep "PostScheduler\|scheduled_post" app.log

# Posts only
grep "📤\|✅\|❌\|⏰" app.log

# Errors only
grep "ERROR\|❌" app.log
```

Key log messages:
- `⏱️` - Initialization
- `🚀` - Startup
- `📅` - Job scheduled
- `🎬` - Job running
- `📤` - Post completed
- `✅` - Success
- `❌` - Error
- `⏰` - Timeout
- `⏭️` - Skipped
- `🛑` - Shutdown

## Error Handling

Methods automatically handle errors:
```python
result = await scheduler.trigger_manual_post()

if result['status'] == 'failed':
    print(f"Error: {result.get('error', 'Unknown')}")
```

## Properties

```python
scheduler.post_times        # List[time] - Current post times
scheduler.is_running        # bool - Scheduler running?
scheduler.content_generator # ContentGenerator | None
scheduler.scheduler         # AsyncIOScheduler instance
```

## App Integration (FastAPI)

```python
from fastapi import FastAPI
from post_scheduler import get_scheduler, shutdown_scheduler

app = FastAPI()

@app.on_event("startup")
async def startup():
    scheduler = await get_scheduler()
    await scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    await shutdown_scheduler()

@app.post("/posts/manual")
async def post_manually(text: str):
    scheduler = await get_scheduler()
    result = await scheduler.trigger_manual_post(text)
    return result

@app.get("/posts/upcoming")
async def get_upcoming():
    scheduler = await get_scheduler()
    return scheduler.get_next_scheduled_posts()

@app.put("/posts/reschedule")
async def reschedule(times: list):
    scheduler = await get_scheduler()
    success = scheduler.reschedule(times)
    return {"success": success}
```

## Testing

```bash
# Run all tests
pytest test_post_scheduler.py -v

# Specific test
pytest test_post_scheduler.py::TestPostScheduler::test_start_scheduler

# With coverage
pytest test_post_scheduler.py --cov=post_scheduler

# Run examples
python post_scheduler_examples.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "ContentGenerator not initialized" | Call `await scheduler.start()` first |
| Posts not posting | Check Telegram bot token in .env |
| High-risk posts skipped | Review keywords in ContentGenerator.assess_risk() |
| Schedule not updating | Ensure scheduler.is_running is True |
| Can't reschedule | Stop and restart scheduler |

## Files

| File | Purpose |
|------|---------|
| `post_scheduler.py` | Main implementation |
| `test_post_scheduler.py` | Test suite (18 tests) |
| `POST_SCHEDULER.md` | Full documentation |
| `post_scheduler_examples.py` | 9 usage examples |
| `IMPLEMENTATION_SUMMARY.md` | Detailed summary |
| `POSTSCHEDULER_QUICKREF.md` | This quick reference |

## Performance

- Memory: ~5-10 MB per instance
- CPU: Minimal when idle
- Async: Non-blocking
- Scalability: Many jobs supported

## Requirements

- Python 3.8+
- APScheduler
- ContentGenerator (existing)
- AsyncIO (standard library)

## Constants

```python
# Default post times (can be changed via constructor)
DEFAULT_TIMES = [time(9, 0), time(14, 0), time(20, 0)]

# Timeout values
SCHEDULED_POST_TIMEOUT = 3600      # 1 hour
MANUAL_POST_TIMEOUT = 1800         # 30 minutes

# Time periods
MORNING = "morning"      # 6 AM - 12 PM
AFTERNOON = "afternoon"  # 12 PM - 6 PM
EVENING = "evening"      # 6 PM - 6 AM
```

## Methods Summary

| Method | Async | Purpose |
|--------|-------|---------|
| `__init__()` | No | Initialize scheduler |
| `start()` | Yes | Start scheduler |
| `stop()` | Yes | Stop gracefully |
| `trigger_manual_post()` | Yes | Post outside schedule |
| `get_next_scheduled_posts()` | No | List upcoming posts |
| `reschedule()` | No | Update post times |
| `_scheduled_post_job()` | Yes | Internal job runner |
| `_default_post_generator()` | No | Generate greetings |
| `_determine_time_period()` | No | Get current period |

---

**For full documentation, see `POST_SCHEDULER.md`**  
**For examples, see `post_scheduler_examples.py`**
