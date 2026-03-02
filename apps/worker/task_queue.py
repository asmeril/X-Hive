"""
Task Queue System for X-HIVE
Sequential task execution with lock management and ChromePool integration.
"""

import asyncio
import sys
import json
import logging
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum

# Windows fix for Playwright subprocess on Python 3.12+ (must be before chrome_pool import)
# Python 3.12+ changed asyncio subprocess handling, try ProactorEventLoopPolicy first
if sys.platform == "win32" and sys.version_info >= (3, 12):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from config import settings
from lock_manager import LockManager
from chrome_pool import ChromePool

logger = logging.getLogger(__name__)

# Dead Letter Queue file path
DLQ_FILE = Path(settings.DATA_PATH) / "dead_letter_queue.json"



class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(int, Enum):
    """Task priority levels"""
    HIGH = 0
    NORMAL = 1
    LOW = 2


@dataclass
class TaskItem:
    """
    Task item representation with retry support
    
    Attributes:
        id: Unique task identifier (UUID4)
        type: Task type (e.g., "post_tweet", "reply", "like")
        payload: Operation-specific data
        priority: Priority level (0=high, 1=normal, 2=low)
        status: Current task status
        created_at: Task creation timestamp
        completed_at: Task completion timestamp (if completed)
        error: Error message (if failed)
        max_retries: Maximum retry attempts (default: 3)
        retry_count: Current retry attempt count
        last_error: Last error message from failed attempt
        retry_delay: Delay between retries in seconds (default: 60)
        scheduled_time: When task should be executed (for delayed retries)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    payload: Dict = field(default_factory=dict)
    priority: int = TaskPriority.NORMAL
    status: str = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(datetime.now().astimezone().tzinfo))
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    max_retries: int = 3
    retry_count: int = 0
    last_error: str = ""
    retry_delay: float = 60.0
    scheduled_time: Optional[datetime] = None

    def __lt__(self, other):
        """Enable priority queue comparison (lower priority value = higher priority)"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at < other.created_at

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "type": self.type,
            "payload": self.payload,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "last_error": self.last_error,
            "retry_delay": self.retry_delay,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
        }


class TaskQueueError(Exception):
    """Task queue operation error"""
    pass


class TaskQueue:
    """
    Singleton Task Queue for sequential X operations.
    
    Features:
    - Priority-based task execution (high/normal/low)
    - Lock-aware execution (integrates with LockManager)
    - ChromePool integration for page access
    - Task history persistence
    - Background processor loop
    - Graceful shutdown with task history save
    """

    _instance: Optional["TaskQueue"] = None
    _lock = asyncio.Lock()

    def __new__(cls) -> "TaskQueue":
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize task queue"""
        if hasattr(self, "_initialized"):
            return

        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.tasks: Dict[str, TaskItem] = {}  # Task storage by ID
        self.task_history: List[TaskItem] = []  # Completed/failed tasks history
        self.failed_tasks: List[TaskItem] = []  # Permanently failed tasks (for manual retry)
        self.lock_manager = LockManager(
            lock_path=settings.LOCK_PATH,
            timeout=180,
            stale=600,
        )
        self.chrome_pool = ChromePool()
        
        # Configuration
        self.history_path = Path(settings.DATA_PATH) / "task_history.json"
        self.max_history = 1000
        self.process_interval = 1.0  # Sleep between queue checks (seconds)
        
        # State
        self._processor_task: Optional[asyncio.Task] = None
        self._running = False
        self._initialized = True

        logger.info("TaskQueue initialized")

    async def add_task(
        self, 
        task_type: str, 
        payload: Dict, 
        priority: int = TaskPriority.NORMAL
    ) -> str:
        """
        Add a new task to the queue.
        
        Args:
            task_type: Task type identifier (e.g., "post_tweet")
            payload: Operation-specific data dictionary
            priority: Priority level (0=high, 1=normal, 2=low)
            
        Returns:
            Task ID (UUID string)
            
        Raises:
            TaskQueueError: If task creation fails
        """
        try:
            task = TaskItem(
                type=task_type,
                payload=payload,
                priority=priority,
                status=TaskStatus.PENDING,
            )
            
            self.tasks[task.id] = task
            await self.task_queue.put(task)
            
            logger.info(
                f"✅ Task added: {task.id} | Type: {task_type} | Priority: {priority}"
            )
            return task.id

        except Exception as e:
            logger.error(f"Failed to add task: {e}")
            raise TaskQueueError(f"Failed to add task: {e}")

    async def get_task_status(self, task_id: str) -> Optional[TaskItem]:
        """
        Get status of a specific task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            TaskItem if found, None otherwise
        """
        return self.tasks.get(task_id)

    async def get_queue_status(self) -> Dict[str, int]:
        """
        Get current queue statistics.
        
        Returns:
            Dictionary with counts of tasks by status:
            {
                "pending": int,
                "running": int,
                "completed": int,
                "failed": int,
                "total": int
            }
        """
        stats = {
            "pending": sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
            "running": sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING),
            "completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED),
        }
        stats["total"] = sum(stats.values())
        return stats

    async def _process_queue(self) -> None:
        """
        Background worker loop for task processing.
        
        Continuously:
        1. Gets tasks from queue
        2. Acquires lock
        3. Executes task via XDaemon
        4. Updates status with retry logic
        5. Releases lock
        """
        logger.info("📋 Task queue processor started")
        
        while self._running:
            try:
                # Try to get next task (non-blocking with timeout)
                try:
                    task = self.task_queue.get_nowait()
                except asyncio.QueueEmpty:
                    # No tasks, wait before checking again
                    await asyncio.sleep(self.process_interval)
                    continue

                logger.info(f"🔄 Processing task: {task.id} | Type: {task.type}")
                task.status = TaskStatus.RUNNING
                
                try:
                    # Acquire lock before accessing browser
                    try:
                        self.lock_manager.acquire_lock()
                        logger.debug(f"🔒 Lock acquired for task {task.id}")
                    except Exception as e:
                        logger.warning(f"⚠️  Lock acquisition failed for task {task.id}: {e}")
                        # Re-queue task on lock failure
                        task.status = TaskStatus.PENDING
                        await self.task_queue.put(task)
                        continue

                    try:
                        # Process task with retry logic
                        await self._process_task(task)
                        
                    finally:
                        # Always release lock
                        try:
                            self.lock_manager.release_lock()
                            logger.debug(f"🔓 Lock released for task {task.id}")
                        except Exception as e:
                            logger.warning(f"⚠️  Lock release error for task {task.id}: {e}")

                except asyncio.CancelledError:
                    logger.info("📋 Task queue processor cancelled")
                    raise

                except Exception as e:
                    logger.error(f"Unexpected error processing task {task.id}: {e}", exc_info=True)
                    task.status = TaskStatus.FAILED
                    task.last_error = f"Unexpected error: {e}"
                    task.completed_at = datetime.now(
                        datetime.now().astimezone().tzinfo
                    )

            except asyncio.CancelledError:
                logger.info("📋 Task queue processor shutting down")
                break

            except Exception as e:
                logger.error(f"Task queue processor error: {e}", exc_info=True)
                await asyncio.sleep(self.process_interval)

    async def _process_task(self, task: TaskItem) -> None:
        """
        Process a single task with exponential backoff retry logic.
        
        Handles:
        - Successful task execution
        - Transient failures with automatic retry
        - Permanent failures after max retries
        - Task state persistence
        
        Args:
            task: TaskItem to process
        """
        try:
            logger.info(
                f"📋 Executing task: {task.id} | Type: {task.type} "
                f"(attempt {task.retry_count + 1}/{task.max_retries + 1})"
            )
            
            # Execute task via XDaemon
            from x_daemon import XDaemon
            
            daemon = XDaemon()
            result = await daemon.execute_task(task)

            # Task succeeded
            if result.get("success"):
                task.status = TaskStatus.COMPLETED
                logger.info(f"✅ Task completed: {task.id}")
            else:
                # API returned failure
                raise Exception(result.get("error", "Unknown error"))
            
            task.completed_at = datetime.now(datetime.now().astimezone().tzinfo)
            
        except Exception as e:
            error_msg = str(e)
            task.last_error = error_msg
            task.retry_count += 1
            
            # Check if we should retry
            if task.retry_count < task.max_retries:
                # Calculate retry delay with exponential backoff
                retry_delay = task.retry_delay * (2 ** (task.retry_count - 1))
                
                logger.warning(
                    f"⚠️ Task failed (attempt {task.retry_count}/{task.max_retries}): {error_msg}\n"
                    f"   ⏳ Retrying in {retry_delay:.0f}s..."
                )
                
                # Re-queue task with delay
                task.status = TaskStatus.PENDING
                task.scheduled_time = datetime.now(datetime.now().astimezone().tzinfo) + timedelta(seconds=retry_delay)
                await self.task_queue.put(task)
                
            else:
                # Max retries exceeded - permanently failed
                task.status = TaskStatus.FAILED
                self.failed_tasks.append(task)
                # Save to Dead Letter Queue
                await self._save_to_dlq(task)
                
                
                logger.error(
                    f"❌ Task permanently failed after {task.max_retries} retries: {task.id}\n"
                    f"   Final error: {error_msg}"
                )
        
        finally:
            # Always save state
            await self._save_task_history()

    async def _save_to_dlq(self, task: TaskItem) -> None:
        """
        Save permanently failed task to Dead Letter Queue file.
        
        Args:
            task: Failed task to save
        """
        
        try:
            # Load existing DLQ
            dlq_tasks = []
            if DLQ_FILE.exists():
                with open(DLQ_FILE, 'r', encoding='utf-8') as f:
                    dlq_data = json.load(f)
                    dlq_tasks = dlq_data.get('tasks', [])
            
            # Add new failed task
            dlq_tasks.append({
                'task_id': task.id,
                'type': task.type,
                'priority': task.priority,
                'created_at': task.created_at.isoformat(),
                'failed_at': datetime.now().isoformat(),
                'retry_count': task.retry_count,
                'last_error': task.last_error,
                'payload': task.payload
            })
            
            # Save to file
            DLQ_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(DLQ_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'tasks': dlq_tasks,
                    'total_count': len(dlq_tasks),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💀 Task saved to DLQ: {task.id} | Error: {task.last_error}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save task to DLQ: {e}")

    async def start(self) -> None:
        """
        Start the background task queue processor and auto-start ChromePool browser.
        
        Raises:
            TaskQueueError: If queue is already running
        """
        if self._running:
            logger.warning("Task queue already running")
            return

        self._running = True
        
        # START CHROMEPOOL BROWSER (non-fatal — Chrome may not be installed yet)
        if self.chrome_pool and not self.chrome_pool.browser:
            logger.info("🌐 Starting ChromePool browser...")
            try:
                await self.chrome_pool.initialize()
                logger.info("✅ ChromePool browser started")
            except Exception as e:
                logger.warning(
                    f"⚠️ ChromePool unavailable in TaskQueue: {e}\n"
                    "Task queue will run without Chrome (Twitter tasks will fail gracefully)."
                )
        
        # Load task history
        await self._load_task_history()
        logger.info(f"✅ Loaded {len(self.task_history)} tasks from history")
        
        # Create and start processor task
        self._processor_task = asyncio.create_task(self._process_queue())
        logger.info("🎯 Task queue processor started")
        
        logger.info("✅ Task queue started")

    async def stop(self) -> None:
        """
        Stop the task queue processor gracefully.
        
        Saves task history and cancels background tasks.
        """
        logger.info("Stopping task queue...")
        
        self._running = False

        if self._processor_task and not self._processor_task.done():
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        # Save task history
        await self._save_task_history()
        
        logger.info("✅ Task queue stopped")

    async def _save_task_history(self) -> None:
        """
        Save completed/failed tasks to JSON file.
        
        Maintains history of last N tasks (default 1000).
        """
        try:
            # Get completed and failed tasks
            completed_tasks = [
                t for t in self.tasks.values()
                if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
            ]

            # Combine with existing history
            all_history = self.task_history + completed_tasks
            
            # Keep only latest N tasks
            if len(all_history) > self.max_history:
                all_history = all_history[-self.max_history:]

            # Convert to dictionaries for JSON
            history_data = {
                "saved_at": datetime.now(
                    datetime.now().astimezone().tzinfo
                ).isoformat(),
                "total_tasks": len(all_history),
                "tasks": [t.to_dict() for t in all_history],
            }

            self.history_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.history_path, "w") as f:
                json.dump(history_data, f, indent=2)

            logger.info(
                f"✅ Saved {len(all_history)} tasks to {self.history_path}"
            )

        except Exception as e:
            logger.error(f"Failed to save task history: {e}")

    async def _load_task_history(self) -> None:
        """
        Load task history from JSON file.
        
        Used on startup to restore previous tasks.
        """
        try:
            if not self.history_path.exists():
                logger.debug(f"No task history found at {self.history_path}")
                return

            with open(self.history_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            
            # Handle empty file
            if not content:
                logger.info("Task history file empty, initializing...")
                self.task_history = []
                return
            
            data = json.loads(content)
            tasks_data = data.get("tasks", [])

            if not tasks_data:
                logger.debug("No tasks in history file")
                return

            # Parse tasks from history
            for task_dict in tasks_data:
                try:
                    task = TaskItem(
                        id=task_dict.get("id"),
                        type=task_dict.get("type"),
                        payload=task_dict.get("payload", {}),
                        priority=task_dict.get("priority", TaskPriority.NORMAL),
                        status=task_dict.get("status", TaskStatus.PENDING),
                        created_at=datetime.fromisoformat(
                            task_dict.get("created_at", datetime.now().isoformat())
                        ),
                        completed_at=(
                            datetime.fromisoformat(task_dict["completed_at"])
                            if task_dict.get("completed_at")
                            else None
                        ),
                        error=task_dict.get("error"),
                    )
                    self.task_history.append(task)
                except Exception as e:
                    logger.warning(f"Failed to parse task from history: {e}")

            logger.info(f"✅ Loaded {len(self.task_history)} tasks from history")

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid task history JSON, resetting: {e}")
            self.task_history = []
            await self._save_task_history()  # Save empty array
        
        except Exception as e:
            logger.error(f"Failed to load task history: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

    def get_failed_tasks(self) -> List[TaskItem]:
        """
        Get list of permanently failed tasks.
        
        Returns:
            List of TaskItem objects that failed after max retries
        """
        return self.failed_tasks.copy()

    async def retry_failed_task(self, task_id: str) -> bool:
        """
        Manually retry a failed task.
        
        Resets retry counter and re-queues the task for execution.
        
        Args:
            task_id: Task ID to retry
        
        Returns:
            True if task was found and re-queued, False otherwise
        """
        for task in self.failed_tasks:
            if task.id == task_id:
                # Reset retry counter and re-queue
                task.retry_count = 0
                task.last_error = ""
                task.status = TaskStatus.PENDING
                task.scheduled_time = datetime.now(datetime.now().astimezone().tzinfo)
                
                self.failed_tasks.remove(task)
                await self.task_queue.put(task)
                
                logger.info(f"🔄 Manually retrying failed task: {task_id}")
                await self._save_task_history()
                return True
        
        logger.warning(f"⚠️ Failed task not found: {task_id}")
        return False

    def get_dlq_tasks(self) -> List[dict]:
        """
        Get all tasks in Dead Letter Queue.
        
        Returns:
            List of failed task dictionaries from DLQ file
        """
        
        if not DLQ_FILE.exists():
            return []
        
        try:
            with open(DLQ_FILE, 'r', encoding='utf-8') as f:
                dlq_data = json.load(f)
                return dlq_data.get('tasks', [])
        except Exception as e:
            logger.error(f"❌ Failed to read DLQ: {e}")
            return []

    async def clear_dlq(self) -> bool:
        """
        Clear Dead Letter Queue file.
        
        Returns:
            True if DLQ was cleared, False if already empty or error occurred
        """
        
        if not DLQ_FILE.exists():
            logger.info("📋 DLQ already empty")
            return False
        
        try:
            DLQ_FILE.unlink()
            logger.info("🗑️ Dead Letter Queue cleared")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to clear DLQ: {e}")
            return False

    def get_dlq_count(self) -> int:
        """Get count of tasks in Dead Letter Queue"""
        
        if not DLQ_FILE.exists():
            return 0
        
        try:
            with open(DLQ_FILE, 'r', encoding='utf-8') as f:
                dlq_data = json.load(f)
                return len(dlq_data.get('tasks', []))
        except Exception as e:
            logger.error(f"❌ Failed to count DLQ tasks: {e}")
            return 0


# Convenience functions for module-level access
async def get_task_queue() -> TaskQueue:
    """Get or create singleton task queue"""
    queue = TaskQueue()
    if not queue._running:
        await queue.start()
    return queue


async def shutdown_task_queue() -> None:
    """Shutdown the task queue"""
    queue = TaskQueue()
    await queue.stop()
