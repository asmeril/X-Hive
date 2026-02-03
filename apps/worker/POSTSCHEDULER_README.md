POSTSCHEDULER_README.md

# PostScheduler - Quick Start Guide

## What is PostScheduler?

PostScheduler is an automated daily post scheduler for X-Hive that:
- Schedules posts at configurable times (default: 9 AM, 2 PM, 8 PM)
- Integrates with ContentGenerator for Telegram approval
- Supports manual post triggering
- Provides dynamic rescheduling
- Uses APScheduler with CronTrigger for reliable scheduling

## 📦 Installation

```bash
# Update requirements (already done)
pip install -r requirements.txt

# Or install APScheduler directly
pip install apscheduler
```

## 🚀 Quick Start

### Most Basic Usage
```python
import asyncio
from post_scheduler import PostScheduler

async def main():
    scheduler = PostScheduler()
    await scheduler.start()
    
    # Scheduler is now running with default times (9 AM, 2 PM, 8 PM)
    # Posts will be scheduled and sent for Telegram approval
    
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await scheduler.stop()

asyncio.run(main())
```

### Using Singleton (Recommended for Apps)
```python
from post_scheduler import get_scheduler, shutdown_scheduler

# In app startup
scheduler = await get_scheduler()
await scheduler.start()

# In app shutdown
await shutdown_scheduler()
```

### With Custom Times
```python
from datetime import time
from post_scheduler import PostScheduler

scheduler = PostScheduler(
    post_times=[time(8, 0), time(13, 0), time(19, 0)]
)
await scheduler.start()
```

## 📝 Common Tasks

### Trigger a Manual Post
```python
# With custom text
result = await scheduler.trigger_manual_post("Breaking news! 🔥")

# With auto-generated greeting
result = await scheduler.trigger_manual_post()

# Check result
print(f"Status: {result['status']}")  # "posted", "skipped", "timeout", etc.
```

### View Upcoming Posts
```python
upcoming = scheduler.get_next_scheduled_posts()
for post in upcoming:
    print(f"{post['time']} at {post['next_run_time']}")
```

### Reschedule Posts
```python
from datetime import time

new_times = [time(7, 0), time(12, 0), time(18, 0), time(21, 0)]
success = scheduler.reschedule(new_times)

if success:
    print("✅ Schedule updated!")
```

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `POST_SCHEDULER.md` | Complete documentation (350+ lines) |
| `POSTSCHEDULER_QUICKREF.md` | Quick reference guide |
| `IMPLEMENTATION_SUMMARY.md` | Detailed implementation info |
| `post_scheduler_examples.py` | 9 working examples |
| `REQUIREMENTS_CHECKLIST.md` | Requirements verification |

## 🧪 Testing

```bash
# Run all tests
pytest test_post_scheduler.py -v

# Run specific test
pytest test_post_scheduler.py::TestPostScheduler::test_init_default_times -v

# With coverage report
pytest test_post_scheduler.py --cov=post_scheduler
```

## 📖 Examples

See `post_scheduler_examples.py` for 9 complete, working examples:
1. Basic usage
2. Custom times
3. Custom content generator
4. Manual posts
5. Rescheduling
6. Singleton pattern
7. App integration
8. Error handling
9. Monitoring

Run examples:
```bash
python post_scheduler_examples.py
```

## 🏗️ FastAPI Integration

```python
from fastapi import FastAPI
from datetime import time
from post_scheduler import get_scheduler, shutdown_scheduler

app = FastAPI()

@app.on_event("startup")
async def startup():
    scheduler = await get_scheduler()
    await scheduler.start()
    print("✅ PostScheduler started")

@app.on_event("shutdown")
async def shutdown():
    await shutdown_scheduler()
    print("✅ PostScheduler shut down")

@app.post("/posts/manual")
async def post_manually(text: str):
    """Manually trigger a post"""
    scheduler = await get_scheduler()
    result = await scheduler.trigger_manual_post(text)
    return result

@app.get("/posts/upcoming")
async def list_upcoming():
    """Get list of upcoming scheduled posts"""
    scheduler = await get_scheduler()
    return scheduler.get_next_scheduled_posts()

@app.put("/posts/reschedule")
async def reschedule_posts(times: list):
    """Update post schedule with new times
    
    times: list of strings in "HH:MM" format
    Example: ["08:00", "13:00", "19:00"]
    """
    from datetime import time as time_obj
    
    scheduler = await get_scheduler()
    new_times = [time_obj(*map(int, t.split(':'))) for t in times]
    success = scheduler.reschedule(new_times)
    return {"success": success}
```

## 🎯 Default Behavior

- **Post Times**: 9:00 AM, 2:00 PM, 8:00 PM
- **Content**: Time-based greetings (morning/afternoon/evening)
- **Approval**: Telegram bot approval required
- **Timeout**: 1 hour for scheduled, 30 min for manual
- **High-Risk**: Auto-skipped
- **Logging**: Emoji-enhanced INFO level

## ⚙️ Configuration

Change defaults by passing to constructor:

```python
from datetime import time
from post_scheduler import PostScheduler

def my_content_gen(period: str) -> str:
    return f"Custom {period} post content"

scheduler = PostScheduler(
    post_times=[time(10, 0), time(15, 0)],  # Custom times
    content_generator_func=my_content_gen    # Custom content
)
```

## 📊 Return Values

All methods return dictionaries:

```python
{
    "status": "posted",           # posted | skipped | timeout | auto_skipped | failed
    "draft_id": "abc123def",      # Internal draft ID
    "task_id": "task_001",        # Queue task ID (if posted)
    "risk_level": "low",          # low | medium | high
    "timestamp": "2026-02-04T...", # ISO format timestamp
    "scheduled": True,            # True for jobs, absent for manual
    "manual": True                # True for manual posts, absent for jobs
}
```

## 🔍 Monitoring

Watch scheduler logs:
```bash
# All scheduler activity
grep "PostScheduler\|scheduled" logs.txt

# Just posts
grep "📤\|✅\|❌" logs.txt

# With timestamps
tail -f logs.txt | grep "PostScheduler"
```

Key log emojis:
- ⏱️ Initialization
- 🚀 Startup
- 📅 Job scheduled
- 🎬 Job running
- 📤 Post completed
- ✅ Success
- ❌ Error
- ⏰ Timeout
- ⏭️ Skipped

## ❓ FAQ

**Q: How do I change post times?**
A: Use `scheduler.reschedule([time(10, 0), ...])` or stop/restart with new times.

**Q: What if a post fails?**
A: All errors are logged. Failed posts don't block other jobs. Check logs for details.

**Q: Can I trigger posts manually?**
A: Yes! Use `scheduler.trigger_manual_post(text)` to post anytime.

**Q: How long is the approval timeout?**
A: 1 hour for scheduled posts, 30 minutes for manual posts.

**Q: What's auto-skipped?**
A: High-risk content (politics, crypto, etc.) is auto-skipped. Change with `auto_skip_high_risk=False`.

**Q: Can I run multiple schedulers?**
A: Yes, but use singleton pattern to avoid conflicts: `await get_scheduler()`

## 🔧 Troubleshooting

**Posts not appearing?**
- Check Telegram bot token in .env
- Verify chat_id is correct
- Check approval in Telegram

**Schedule not working?**
- Ensure `await scheduler.start()` was called
- Check that `is_running` is True
- Verify post_times are valid `datetime.time` objects

**High-risk posts being skipped?**
- Review ContentGenerator.assess_risk() for keyword lists
- Set `auto_skip_high_risk=False` if desired

**Can't reschedule?**
- Scheduler must be running
- Try stopping and restarting instead

## 📝 Next Steps

1. **Read Full Docs**: Open `POST_SCHEDULER.md`
2. **Try Examples**: Run `python post_scheduler_examples.py`
3. **Run Tests**: Execute `pytest test_post_scheduler.py -v`
4. **Integrate**: Add to your FastAPI app (see example above)
5. **Monitor**: Check logs while running

## 📦 Files Overview

```
✅ post_scheduler.py              # Main implementation (471 lines)
✅ test_post_scheduler.py         # Test suite (395 lines, 18 tests)
✅ POST_SCHEDULER.md              # Full documentation (350+ lines)
✅ POSTSCHEDULER_QUICKREF.md      # Quick reference
✅ IMPLEMENTATION_SUMMARY.md      # Technical details
✅ post_scheduler_examples.py     # 9 working examples (300+ lines)
✅ REQUIREMENTS_CHECKLIST.md      # Requirements verified
✅ POSTSCHEDULER_README.md        # This file
```

## 💡 Pro Tips

1. **Use Singleton**: Better for apps - `await get_scheduler()`
2. **Watch Logs**: Monitor emoji logs in real-time: `grep "📤"` 
3. **Test First**: Run examples before integrating
4. **Custom Content**: Write your own generator function
5. **Error Monitoring**: All errors are logged with tracebacks
6. **Schedule Early**: Set up on app startup

## 🎓 Learn More

- **Full Docs**: `POST_SCHEDULER.md`
- **Quick Ref**: `POSTSCHEDULER_QUICKREF.md`
- **Examples**: `post_scheduler_examples.py`
- **Tests**: `test_post_scheduler.py`
- **Tech Details**: `IMPLEMENTATION_SUMMARY.md`

---

**Ready to schedule your posts? Start with the quick start example above!** 🚀

For complete documentation, see `POST_SCHEDULER.md`
