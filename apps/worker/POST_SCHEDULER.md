POST_SCHEDULER.md

# PostScheduler - X-Hive Automated Posting System

## Overview

`PostScheduler` is a robust scheduler for automating daily posts on X (Twitter) with Telegram approval workflow integration. It uses **APScheduler** with `AsyncIOScheduler` and `CronTrigger` to schedule posts at configurable times, typically throughout the day.

## Features

- ✅ **Daily Scheduled Posts**: Configurable post times (default: 9 AM, 2 PM, 8 PM)
- ✅ **Time-Based Greeting Content**: Automatic morning, afternoon, and evening posts
- ✅ **Telegram Approval Workflow**: Integration with ContentGenerator for human approval
- ✅ **Manual Post Triggering**: Execute posts outside the schedule
- ✅ **Dynamic Rescheduling**: Change post times without restarting
- ✅ **Comprehensive Logging**: Emoji-enabled logs for easy monitoring
- ✅ **Graceful Shutdown**: Proper cleanup of scheduler and resources
- ✅ **Singleton Pattern**: Global access via `get_scheduler()` and `shutdown_scheduler()`
- ✅ **Error Handling**: Try-except blocks with detailed error logging
- ✅ **Timeout Management**: 1 hour for scheduled posts, 30 min for manual posts
- ✅ **Type Hints**: Full type annotations for IDE support

## Installation

1. **Add APScheduler to requirements.txt** (already done):
   ```
   apscheduler
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Basic Usage

```python
from post_scheduler import PostScheduler, get_scheduler, shutdown_scheduler
from datetime import time
import asyncio

async def main():
    # Method 1: Create instance directly
    scheduler = PostScheduler()
    await scheduler.start()
    
    # Method 2: Use singleton pattern
    scheduler = await get_scheduler()
    await scheduler.start()
    
    # Keep running...
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await scheduler.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom Post Times

```python
from datetime import time

custom_times = [
    time(7, 0),    # 7 AM
    time(12, 30),  # 12:30 PM
    time(18, 0),   # 6 PM
    time(21, 0)    # 9 PM
]

scheduler = PostScheduler(post_times=custom_times)
await scheduler.start()
```

### Custom Content Generator

```python
def my_content_generator(time_period: str) -> str:
    """Custom post generator"""
    content = {
        "morning": "🌅 Rise and shine! New day, new opportunities.",
        "afternoon": "☀️ Afternoon vibes! Keep grinding.",
        "evening": "🌙 Evening reflections. What did you accomplish today?"
    }
    return content.get(time_period, "Hello world!")

scheduler = PostScheduler(
    post_times=[time(9, 0), time(18, 0)],
    content_generator_func=my_content_generator
)
await scheduler.start()
```

### Manual Post Triggering

```python
# Trigger with custom text
result = await scheduler.trigger_manual_post(
    text="Breaking news! Check this out! 🔥"
)
print(f"Post status: {result['status']}")

# Trigger with auto-generated content
result = await scheduler.trigger_manual_post()
```

### Get Upcoming Posts

```python
upcoming = scheduler.get_next_scheduled_posts()
for post in upcoming:
    print(f"{post['time']}: {post['next_run_time']}")
```

### Reschedule Posts

```python
new_times = [time(8, 0), time(13, 0), time(19, 0)]
success = scheduler.reschedule(new_times)

if success:
    print("Schedule updated!")
else:
    print("Failed to reschedule")
```

## Class Reference

### PostScheduler

#### Initialization

```python
PostScheduler(
    post_times: Optional[List[time]] = None,
    content_generator_func: Optional[Callable] = None
)
```

**Parameters:**
- `post_times`: List of `datetime.time` objects for daily posts. Default: `[9:00, 14:00, 20:00]`
- `content_generator_func`: Function that takes time period string ("morning"/"afternoon"/"evening") and returns post text. Default: time-based greeting generator

#### Methods

##### `async start() -> None`
Initialize and start the scheduler.
- Initializes ContentGenerator
- Starts ContentGenerator service  
- Creates CronTrigger jobs for each post time
- Starts AsyncIOScheduler

##### `async stop() -> None`
Shutdown scheduler gracefully.
- Cancels pending jobs
- Shuts down AsyncIOScheduler
- Stops ContentGenerator

##### `async _scheduled_post_job() -> Dict[str, Any]`
Internal job executed at scheduled times.
- Generates time-based greeting content
- Submits for approval (1 hour timeout)
- Returns result dict with status, draft_id, task_id, risk_level, timestamp, scheduled flag

**Return Format:**
```python
{
    "status": "posted" | "skipped" | "timeout" | "auto_skipped" | "failed",
    "draft_id": str,
    "task_id": str | None,
    "risk_level": "low" | "medium" | "high",
    "timestamp": str (ISO format),
    "scheduled": True
}
```

##### `def _default_post_generator(time_period: str) -> str`
Generate default time-based greeting posts.
- "morning" (6-12): 🌅 Good morning post
- "afternoon" (12-18): ☀️ Good afternoon post
- "evening" (18-6): 🌙 Good evening post

##### `async trigger_manual_post(text: Optional[str] = None) -> Dict[str, Any]`
Manually trigger a post outside the schedule.
- Submits custom or auto-generated text for approval
- 30 minute timeout for manual posts
- Same return format as scheduled_post_job

**Parameters:**
- `text`: Custom post content. If None, generates default for current time period.

##### `def get_next_scheduled_posts() -> List[Dict[str, Any]]`
Get upcoming scheduled posts.

**Return Format:**
```python
[
    {
        "time": str,              # e.g., "Post at 09:00"
        "job_id": str,           # e.g., "scheduled_post_09_00"
        "next_run_time": str,    # ISO format datetime
        "timezone": str          # e.g., "UTC"
    },
    ...
]
```

##### `def reschedule(new_post_times: List[time]) -> bool`
Update post schedule.
- Removes existing jobs
- Creates new jobs with updated times
- Returns True on success, False otherwise

**Parameters:**
- `new_post_times`: New list of `datetime.time` objects

#### Properties

- `post_times: List[time]` - Current post times
- `is_running: bool` - Scheduler running status
- `content_generator: Optional[ContentGenerator]` - Content generator instance
- `scheduler: AsyncIOScheduler` - Underlying APScheduler instance

### Singleton Functions

#### `async get_scheduler(...) -> PostScheduler`
Get or create singleton PostScheduler instance.

**Parameters:**
- `post_times`: Used only if creating new instance
- `content_generator_func`: Used only if creating new instance

**Returns:** PostScheduler singleton instance

#### `async shutdown_scheduler() -> None`
Shutdown the singleton PostScheduler instance.
- Gracefully stops scheduler
- Clears singleton reference

## Logging

All operations use emoji-enhanced logging at INFO level. Examples:

```
⏱️ PostScheduler initialized | Post times: ['09:00', '14:00', '20:00']
🚀 PostScheduler started | 3 jobs scheduled
📅 Scheduled job: scheduled_post_09_00 at 09:00
🎬 Running scheduled post job at 09:00 (morning)
📤 Scheduled post job completed | Status: posted | Draft: abc12def
⏭️ Draft skipped by user: abc12def
⏰ Draft timeout: abc12def
❌ Auto-skipped high-risk content: abc12def
🌙 Good evening! Wrapping up the day...
✅ PostScheduler stopped gracefully
```

## Timeout Configuration

- **Scheduled Posts**: 1 hour (3600 seconds) - Telegram approval timeout
- **Manual Posts**: 30 minutes (1800 seconds) - Faster feedback for manual triggers

## Integration with ContentGenerator

PostScheduler automatically:
1. Initializes ContentGenerator on start
2. Generates post content (custom or default)
3. Submits to ContentGenerator.create_post_with_approval()
4. Auto-skips high-risk content
5. Handles approval decisions (posted/skipped/timeout)
6. Queues approved posts to TaskQueue

## Error Handling

All methods include try-except blocks with:
- Detailed error logging at ERROR level
- `exc_info=True` for traceback details
- Graceful fallback responses
- Prevents scheduler crash from individual post failures

## Architecture

```
PostScheduler
├── AsyncIOScheduler (APScheduler)
│   └── CronTrigger jobs (one per post time)
├── ContentGenerator
│   ├── TelegramApprovalBot (for approval)
│   └── TaskQueue (for queuing approved posts)
└── Singleton Pattern
    ├── get_scheduler()
    └── shutdown_scheduler()
```

## Testing

Comprehensive test suite in `test_post_scheduler.py`:

```bash
# Run all tests
pytest test_post_scheduler.py -v

# Run specific test
pytest test_post_scheduler.py::TestPostScheduler::test_init_default_times -v

# Run with coverage
pytest test_post_scheduler.py --cov=post_scheduler
```

Test coverage includes:
- ✅ Initialization (default and custom)
- ✅ Time period detection
- ✅ Default content generation
- ✅ Scheduler start/stop
- ✅ Scheduled post jobs
- ✅ Manual post triggering
- ✅ Rescheduling
- ✅ Singleton pattern
- ✅ Error handling
- ✅ Integration workflows

## Best Practices

1. **Use Singleton Pattern**:
   ```python
   scheduler = await get_scheduler()
   # ... use scheduler ...
   await shutdown_scheduler()  # On app shutdown
   ```

2. **Proper Shutdown**:
   ```python
   try:
       scheduler = await get_scheduler()
       await scheduler.start()
       # ... run app ...
   finally:
       await shutdown_scheduler()
   ```

3. **Custom Content Generator**:
   ```python
   def smart_generator(period):
       if period == "morning":
           return "Morning market analysis..."
       # ... more logic ...
   ```

4. **Monitor Logs**:
   ```bash
   # Tail logs to see scheduler activity
   tail -f logs/app.log | grep "📤\|❌\|⏰"
   ```

## Troubleshooting

### Scheduler not starting
- Check ContentGenerator initialization
- Verify Telegram bot token in .env
- Check for port conflicts

### Posts not being scheduled
- Verify post_times are valid `datetime.time` objects
- Check APScheduler logging
- Confirm scheduler.is_running is True

### Approval timeouts
- Increase timeout_seconds in method calls
- Check Telegram bot connection
- Verify chat_id in Telegram bot

### High-risk content auto-skipped
- Review content for high-risk keywords
- Set auto_skip_high_risk=False if desired
- Check risk assessment in ContentGenerator.assess_risk()

## Performance

- **Memory**: ~5-10 MB per scheduler instance
- **CPU**: Minimal when idle, event-driven on job execution
- **Concurrency**: Async/await for non-blocking operations
- **Scalability**: Supports multiple instances with different schedules

## Future Enhancements

- [ ] Database persistence of schedule
- [ ] Web UI for schedule management
- [ ] Advanced content generation with AI
- [ ] A/B testing of post times
- [ ] Analytics integration
- [ ] Multi-account support
- [ ] Rate limiting per account
- [ ] Custom validation rules
