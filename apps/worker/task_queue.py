"""
Task Queue System for X-HIVE
Sequential task execution with lock management and ChromePool integration.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum

from config import settings
from lock_manager import LockManager
from chrome_pool import ChromePool

logger = logging.getLogger(__name__)


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
    Task item representation
    
    Attributes:
        id: Unique task identifier (UUID4)
        type: Task type (e.g., "post_tweet", "reply", "like")
        payload: Operation-specific data
        priority: Priority level (0=high, 1=normal, 2=low)
        status: Current task status
        created_at: Task creation timestamp
        completed_at: Task completion timestamp (if completed)
        error: Error message (if failed)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    payload: Dict = field(default_factory=dict)
    priority: int = TaskPriority.NORMAL
    status: str = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(datetime.now().astimezone().tzinfo))
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

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
        3. Gets page from ChromePool
        4. Executes task
        5. Updates status
        6. Releases lock
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
                        await self.task_queue.put(task)
                        task.status = TaskStatus.PENDING
                        continue

                    try:
                        # Get page from ChromePool
                        page = await self.chrome_pool.get_page()

                        # Execute task (placeholder - will be implemented per task type)
                        await self._execute_task(task, page)

                        # Mark as completed
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = datetime.now(
                            datetime.now().astimezone().tzinfo
                        )
                        logger.info(f"✅ Task completed: {task.id}")

                    except Exception as e:
                        logger.error(f"❌ Task execution failed: {e}")
                        task.status = TaskStatus.FAILED
                        task.error = str(e)
                        task.completed_at = datetime.now(
                            datetime.now().astimezone().tzinfo
                        )

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
                    task.error = f"Unexpected error: {e}"
                    task.completed_at = datetime.now(
                        datetime.now().astimezone().tzinfo
                    )

            except asyncio.CancelledError:
                logger.info("📋 Task queue processor shutting down")
                break

            except Exception as e:
                logger.error(f"Task queue processor error: {e}", exc_info=True)
                await asyncio.sleep(self.process_interval)

    async def _execute_task(self, task: TaskItem, page) -> None:
        """
        Execute a specific task based on type.
        
        Args:
            task: TaskItem to execute
            page: Playwright page instance
            
        Raises:
            Exception: Task-specific errors
        """
        task_type = task.type
        payload = task.payload

        logger.debug(f"Executing task type: {task_type}")

        # Task type handlers
        if task_type == "post_tweet":
            # TODO: Implement post_tweet
            # tweet_text = payload.get("text")
            # media = payload.get("media", [])
            pass

        elif task_type == "reply":
            # TODO: Implement reply
            # tweet_id = payload.get("tweet_id")
            # reply_text = payload.get("text")
            pass

        elif task_type == "like":
            # TODO: Implement like
            # tweet_id = payload.get("tweet_id")
            pass

        elif task_type == "retweet":
            # TODO: Implement retweet
            # tweet_id = payload.get("tweet_id")
            pass

        elif task_type == "follow":
            # TODO: Implement follow
            # user_id = payload.get("user_id")
            pass

        else:
            raise TaskQueueError(f"Unknown task type: {task_type}")

    async def start(self) -> None:
        """
        Start the background task queue processor.
        
        Raises:
            TaskQueueError: If queue is already running
        """
        if self._running:
            logger.warning("Task queue already running")
            return

        self._running = True
        
        # Load task history
        await self._load_task_history()
        
        # Create and start processor task
        self._processor_task = asyncio.create_task(self._process_queue())
        
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

            with open(self.history_path, "r") as f:
                data = json.load(f)

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

        except Exception as e:
            logger.error(f"Failed to load task history: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()


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
