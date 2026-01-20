# Task Queue System

Sequential task execution with lock management and ChromePool integration for X-HIVE worker.

## Overview

The Task Queue System provides:
- **Priority-based task execution** (HIGH/NORMAL/LOW)
- **Sequential processing** with lock awareness
- **ChromePool integration** for persistent browser access
- **Task history persistence** to JSON file
- **Background processing loop** with graceful shutdown
- **Comprehensive error handling** and logging

## Features

✅ **Priority Queue** - Tasks executed by priority (high → normal → low)  
✅ **Lock Integration** - Respects existing LockManager  
✅ **Sequential Execution** - One task at a time (lock-safe)  
✅ **Browser Integration** - Uses ChromePool for page access  
✅ **History Persistence** - Saves task history to disk  
✅ **Background Processing** - Async task loop  
✅ **Graceful Shutdown** - Cleans up and saves state  
✅ **Singleton Pattern** - Only one queue instance  

## Architecture

```
TaskQueue (Singleton)
├── task_queue: asyncio.PriorityQueue
│   └── Stores TaskItem objects by priority
├── tasks: Dict[str, TaskItem]
│   └── In-memory task storage
├── task_history: List[TaskItem]
│   └── Completed/failed tasks
├── _process_queue(): Background loop
│   ├── Get next task from queue
│   ├── Acquire lock
│   ├── Get page from ChromePool
│   ├── Execute task
│   ├── Update status
│   └── Release lock
└── History persistence
    └── C:\XHive\data\task_history.json
```

## Data Models

### TaskStatus

```python
PENDING = "pending"      # Waiting in queue
RUNNING = "running"      # Currently executing
COMPLETED = "completed"  # Successfully executed
FAILED = "failed"        # Execution failed
```

### TaskPriority

```python
HIGH = 0        # Execute first
NORMAL = 1      # Execute second
LOW = 2         # Execute last
```

### TaskItem

```python
@dataclass
class TaskItem:
    id: str                        # UUID4 identifier
    type: str                      # Task type (e.g., "post_tweet")
    payload: Dict                  # Operation-specific data
    priority: int                  # Priority level (0-2)
    status: str                    # Current status
    created_at: datetime           # Creation timestamp
    completed_at: Optional[datetime]  # Completion timestamp
    error: Optional[str]           # Error message if failed
```

## API Reference

### Task Management

#### Add Task

```python
task_id = await queue.add_task(
    task_type="post_tweet",
    payload={"text": "Hello, X!"},
    priority=TaskPriority.NORMAL
)
```

**Args:**
- `task_type` (str): Task identifier (e.g., "post_tweet", "like", "reply")
- `payload` (dict): Operation-specific data
- `priority` (int): 0=HIGH, 1=NORMAL, 2=LOW (default: NORMAL)

**Returns:**
- `str`: Task ID (UUID)

**Raises:**
- `TaskQueueError`: If task creation fails

#### Get Task Status

```python
task = await queue.get_task_status(task_id)
if task:
    print(task.status)  # "pending", "running", "completed", "failed"
    print(task.error)   # Error message if failed
```

**Args:**
- `task_id` (str): Task identifier

**Returns:**
- `TaskItem`: Task object if found, None otherwise

#### Get Queue Status

```python
stats = await queue.get_queue_status()
# {
#     "pending": 5,
#     "running": 1,
#     "completed": 10,
#     "failed": 1,
#     "total": 17
# }
```

**Returns:**
- `dict`: Statistics by task status

### Lifecycle Management

#### Start Queue

```python
await queue.start()
```

Starts the background task processor loop. Loads task history from disk.

#### Stop Queue

```python
await queue.stop()
```

Stops background processing gracefully, saves task history.

#### Context Manager

```python
async with TaskQueue() as queue:
    task_id = await queue.add_task(...)
    # Auto-shutdown on exit
```

## FastAPI Endpoints

### Add Task

```
POST /tasks/add
Query Parameters:
  - task_type: str (e.g., "post_tweet")
  - payload: dict (JSON)
  - priority: int (0-2, default: 1)

Response:
{
  "status": "ok",
  "task_id": "uuid",
  "message": "Task added: post_tweet"
}
```

### Get Task Status

```
GET /tasks/status/{task_id}

Response:
{
  "status": "ok",
  "task": {
    "id": "uuid",
    "type": "post_tweet",
    "payload": {...},
    "priority": 1,
    "status": "completed",
    "created_at": "2026-01-21T10:30:45.123456",
    "completed_at": "2026-01-21T10:30:50.654321",
    "error": null
  }
}
```

### Get Queue Status

```
GET /tasks/queue-status

Response:
{
  "status": "ok",
  "queue": {
    "pending": 5,
    "running": 1,
    "completed": 10,
    "failed": 1,
    "total": 17
  }
}
```

## Integration with FastAPI Lifespan

The task queue is automatically initialized and shutdown through FastAPI's lifespan context manager:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await task_queue.start()
    yield
    # Shutdown
    await task_queue.stop()
```

## Task Execution Flow

```
1. User calls add_task(type, payload, priority)
   ↓
2. TaskItem created with PENDING status
   ↓
3. Task added to priority queue
   ↓
4. Background loop gets next task
   ↓
5. Task status → RUNNING
   ↓
6. LockManager.acquire_lock()
   ↓
7. ChromePool.get_page()
   ↓
8. Execute task (type-specific handler)
   ↓
9. Update status → COMPLETED or FAILED
   ↓
10. LockManager.release_lock()
   ↓
11. Task saved to history on shutdown
```

## Task Types (Extensible)

Current placeholders:
- `post_tweet` - Post a new tweet
- `reply` - Reply to a tweet
- `like` - Like a tweet
- `retweet` - Retweet a tweet
- `follow` - Follow a user

Each task type has a handler in `_execute_task()`:

```python
async def _execute_task(self, task: TaskItem, page):
    if task.type == "post_tweet":
        text = task.payload.get("text")
        media = task.payload.get("media", [])
        # Implementation
    elif task.type == "reply":
        tweet_id = task.payload.get("tweet_id")
        reply_text = task.payload.get("text")
        # Implementation
    # ... more task types
```

## Lock Integration

Each task execution is protected by the lock:

```
1. Acquire lock (wait up to 180 seconds)
2. If successful:
   - Execute task
   - Release lock
3. If timeout:
   - Re-queue task
   - Continue to next task
```

This ensures X operations don't conflict with other processes.

## Cookie Persistence

Tasks maintain session state through ChromePool's cookie persistence:

```
1. On startup: Load cookies from C:\XHive\data\x_cookies.json
2. During tasks: Use persistent page context
3. On shutdown: Save current cookies to disk
```

This keeps the browser session logged into X.com across restarts.

## Task History

Task history is persisted to `C:\XHive\data\task_history.json`:

```json
{
  "saved_at": "2026-01-21T10:35:45.123456",
  "total_tasks": 100,
  "tasks": [
    {
      "id": "uuid",
      "type": "post_tweet",
      "payload": {...},
      "priority": 1,
      "status": "completed",
      "created_at": "2026-01-21T10:30:45.123456",
      "completed_at": "2026-01-21T10:30:50.654321",
      "error": null
    },
    ...
  ]
}
```

**Features:**
- Max 1000 tasks stored (older tasks rotated)
- Auto-loaded on startup
- Auto-saved on shutdown
- Includes completed and failed tasks

## Error Handling

### Task Execution Errors

```python
try:
    await self._execute_task(task, page)
    task.status = TaskStatus.COMPLETED
except Exception as e:
    task.status = TaskStatus.FAILED
    task.error = str(e)
    task.completed_at = datetime.now(...)
```

### Lock Acquisition Errors

If lock cannot be acquired, the task is re-queued:

```python
try:
    lock_manager.acquire_lock()
except Exception as e:
    await self.task_queue.put(task)
    task.status = TaskStatus.PENDING
    continue
```

### ChromePool Errors

If page is unavailable, task fails gracefully:

```python
try:
    page = await self.chrome_pool.get_page()
except Exception as e:
    task.status = TaskStatus.FAILED
    task.error = f"ChromePool error: {e}"
```

## Performance Characteristics

- **Task Addition**: O(log n) - Priority queue insertion
- **Task Processing**: Sequential (one task at a time)
- **Lock Contention**: Respects 180-second timeout
- **Memory**: In-memory queue + history (capped at 1000 tasks)
- **Disk I/O**: History save/load on startup/shutdown

## Configuration

Settings from `config.py`:

```python
LOCK_PATH = r"C:\XHive\locks\x_session.lock"
DATA_PATH = r"C:\XHive\data"  # Where task_history.json is stored
BROWSER_DATA_DIR = r"C:\XHive\browser_data"
CHROME_HEADLESS = False
```

## Logging

All operations are logged:

```
✅ Task added: {task_id} | Type: {type} | Priority: {priority}
🔄 Processing task: {task_id} | Type: {type}
🔒 Lock acquired for task {task_id}
✅ Task completed: {task_id}
❌ Task execution failed: {error}
🔓 Lock released for task {task_id}
✅ Saved N tasks to task_history.json
```

## Testing

Run test script:

```bash
cd C:\XHive\X-Hive\apps\worker
python test_task_queue.py
```

Test coverage:
- Singleton pattern
- Task priority ordering
- Queue status retrieval
- Task history persistence
- Error handling

## Usage Example

```python
import asyncio
from task_queue import TaskQueue, TaskPriority

async def main():
    queue = TaskQueue()
    
    try:
        # Start queue
        await queue.start()
        
        # Add tasks
        task_id = await queue.add_task(
            task_type="post_tweet",
            payload={"text": "Hello, X!"},
            priority=TaskPriority.HIGH
        )
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Check status
        task = await queue.get_task_status(task_id)
        print(f"Task status: {task.status}")
        
        # Get queue stats
        stats = await queue.get_queue_status()
        print(f"Queue: {stats}")
        
    finally:
        await queue.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Integration with X-Daemon

The Task Queue is used by X-Daemon:

```python
from task_queue import TaskQueue

async def create_tweet():
    queue = TaskQueue()
    task_id = await queue.add_task(
        task_type="post_tweet",
        payload={"text": "Tweeting via X-Daemon"},
        priority=TaskPriority.HIGH
    )
    return task_id
```

## References

- [asyncio PriorityQueue](https://docs.python.org/3/library/asyncio-queue.html#asyncio.PriorityQueue)
- [Dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
