"""
X-Daemon Core for X-HIVE
Main orchestrator for ChromePool, TaskQueue, and X (Twitter) operations.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List, Any

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from config import settings
from chrome_pool import ChromePool
from task_queue import TaskQueue, TaskItem, TaskStatus
from lock_manager import LockManager
from rate_limiter import get_rate_limiter, OperationType
from human_behavior import HumanBehavior

logger = logging.getLogger(__name__)


@dataclass
class DaemonState:
    """
    X-Daemon state representation
    
    Attributes:
        status: Daemon status ("running" or "stopped")
        started_at: Daemon start timestamp
        stopped_at: Daemon stop timestamp
        total_operations: Total number of operations executed
        successful_operations: Number of successful operations
        failed_operations: Number of failed operations
    """
    status: str = "stopped"
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "total_operations": self.total_operations,
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
        }


class XDaemonError(Exception):
    """X-Daemon operation error"""
    pass


class XDaemon:
    """
    X-Daemon Core Orchestrator
    
    Main daemon that orchestrates:
    - ChromePool (persistent browser management)
    - TaskQueue (sequential task execution)
    - LockManager (file-based locking)
    - X operations (post, reply, like, retweet)
    
    Features:
    - Singleton pattern
    - Lifecycle management (start/stop/restart)
    - X operation implementations with retry logic
    - Health monitoring
    - State persistence
    """

    _instance: Optional["XDaemon"] = None
    _lock = asyncio.Lock()

    # X.com Playwright selectors
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

    def __new__(cls) -> "XDaemon":
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize X-Daemon"""
        if hasattr(self, "_initialized"):
            return

        self.chrome_pool = ChromePool()
        self.task_queue = TaskQueue()
        self.lock_manager = LockManager(
            lock_path=settings.LOCK_PATH,
            timeout=180,
            stale=600,
        )
        
        # SAFETY: Rate limiter integration
        self.rate_limiter = get_rate_limiter()

        # State management
        self.state = DaemonState()
        self.state_path = Path(settings.DATA_PATH) / "daemon_state.json"
        self.last_operation: Optional[Dict] = None

        # Configuration
        self.max_retries = 2
        self.operation_timeout = 30  # seconds
        self.element_wait_timeout = 10000  # milliseconds

        self._initialized = True
        logger.info("XDaemon initialized")
    
    async def _safety_check(self, operation_type: OperationType) -> None:
        """
        🛡️ CRITICAL SAFETY CHECK - Run before EVERY X operation.
        
        Checks:
        1. Rate limit compliance
        2. Forces human behavior delay
        
        Args:
            operation_type: Type of operation to check
            
        Raises:
            XDaemonError: If operation is blocked by rate limiter
        """
        # Check rate limit
        allowed, reason = self.rate_limiter.check_limit(operation_type)
        if not allowed:
            logger.error(f"🚫 RATE LIMIT BLOCKED: {reason}")
            raise XDaemonError(f"Rate limit exceeded: {reason}")
        
        # Add mandatory human behavior delay
        await HumanBehavior.random_delay()
        logger.info(f"🛡️ Safety check passed for {operation_type.value}")

    async def start(self) -> Dict:
        """
        Start the X-Daemon.
        
        Starts ChromePool and TaskQueue, initializes daemon state.
        
        Returns:
            dict: {"status": "running", "started_at": timestamp}
            
        Raises:
            XDaemonError: If startup fails
        """
        async with self._lock:
            if self.state.status == "running":
                logger.warning("X-Daemon already running")
                return {"status": "running", "message": "Already running"}

            try:
                logger.info("🚀 Starting X-Daemon...")

                # Load previous state
                await self._load_state()

                # Start ChromePool (non-fatal — Chrome may not be installed yet)
                try:
                    await self.chrome_pool.initialize()
                    logger.info("✅ ChromePool started")
                except Exception as e:
                    logger.warning(
                        f"⚠️ ChromePool unavailable (Chrome/Playwright not installed?): {e}\n"
                        "Daemon will run in limited mode — Twitter posting disabled."
                    )
                    # Continue without Chrome; Twitter operations will fail gracefully

                # Start TaskQueue (non-fatal)
                try:
                    await self.task_queue.start()
                    logger.info("✅ TaskQueue started")
                except Exception as e:
                    logger.warning(f"⚠️ TaskQueue unavailable: {e}\nDaemon will run in limited mode.")

                # Update daemon state
                self.state.status = "running"
                self.state.started_at = datetime.now(timezone.utc)
                self.state.stopped_at = None

                await self._save_state()

                logger.info("✅ X-Daemon started successfully")
                return {
                    "status": "running",
                    "started_at": self.state.started_at.isoformat(),
                }

            except Exception as e:
                logger.error(f"X-Daemon startup failed: {e}")
                self.state.status = "stopped"
                raise XDaemonError(f"Startup failed: {e}")

    async def stop(self) -> Dict:
        """
        Stop the X-Daemon gracefully.
        
        Stops TaskQueue and ChromePool, saves state.
        
        Returns:
            dict: {"status": "stopped", "stopped_at": timestamp}
        """
        async with self._lock:
            if self.state.status == "stopped":
                logger.warning("X-Daemon already stopped")
                return {"status": "stopped", "message": "Already stopped"}

            try:
                logger.info("🛑 Stopping X-Daemon...")

                # Stop TaskQueue
                try:
                    await self.task_queue.stop()
                    logger.info("✅ TaskQueue stopped")
                except Exception as e:
                    logger.warning(f"TaskQueue shutdown warning: {e}")

                # Stop ChromePool
                try:
                    await self.chrome_pool.shutdown()
                    logger.info("✅ ChromePool stopped")
                except Exception as e:
                    logger.warning(f"ChromePool shutdown warning: {e}")

                # Update daemon state
                self.state.status = "stopped"
                self.state.stopped_at = datetime.now(timezone.utc)

                await self._save_state()

                logger.info("✅ X-Daemon stopped successfully")
                return {
                    "status": "stopped",
                    "stopped_at": self.state.stopped_at.isoformat(),
                }

            except Exception as e:
                logger.error(f"X-Daemon shutdown error: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                }

    async def restart(self) -> Dict:
        """
        Restart the X-Daemon.
        
        Stops then starts the daemon.
        
        Returns:
            dict: Restart status
        """
        logger.info("🔄 Restarting X-Daemon...")
        
        stop_result = await self.stop()
        await asyncio.sleep(2)  # Brief pause between stop/start
        start_result = await self.start()
        
        return {
            "status": "restarted",
            "stopped": stop_result,
            "started": start_result,
        }

    async def get_status(self) -> Dict:
        """
        Get current daemon status.
        
        Returns:
            dict: {
                "daemon_status": "running" | "stopped",
                "chrome_pool_healthy": bool,
                "queue_stats": {...},
                "uptime_seconds": int,
                "last_operation": {...},
                "operations": {
                    "total": int,
                    "successful": int,
                    "failed": int
                }
            }
        """
        # Calculate uptime
        uptime_seconds = 0
        if self.state.status == "running" and self.state.started_at:
            uptime_seconds = int(
                (datetime.now(timezone.utc) - self.state.started_at).total_seconds()
            )

        # Check ChromePool health
        chrome_healthy = False
        try:
            chrome_healthy = await self.chrome_pool.is_healthy()
        except Exception as e:
            logger.warning(f"ChromePool health check failed: {e}")

        # Get queue stats
        queue_stats = {}
        try:
            queue_stats = await self.task_queue.get_queue_status()
        except Exception as e:
            logger.warning(f"TaskQueue status retrieval failed: {e}")

        return {
            "daemon_status": self.state.status,
            "chrome_pool_healthy": chrome_healthy,
            "queue_stats": queue_stats,
            "uptime_seconds": uptime_seconds,
            "last_operation": self.last_operation,
            "operations": {
                "total": self.state.total_operations,
                "successful": self.state.successful_operations,
                "failed": self.state.failed_operations,
            },
        }

    async def execute_task(self, task: TaskItem) -> Dict:
        """
        Execute a task by routing to the appropriate operation.
        
        Called by TaskQueue for each queued task.
        
        Args:
            task: TaskItem to execute
            
        Returns:
            dict: Operation result
        """
        logger.info(f"🎯 Executing task: {task.id} | Type: {task.type}")

        try:
            task_type = task.type
            payload = task.payload

            # Route to appropriate operation
            if task_type == "post_tweet":
                text = payload.get("text", "")
                images = payload.get("images", [])
                result = await self.post_tweet(text, images)

            elif task_type == "reply":
                tweet_url = payload.get("tweet_url", "")
                text = payload.get("text", "")
                result = await self.reply_to_tweet(tweet_url, text)

            elif task_type == "like":
                tweet_url = payload.get("tweet_url", "")
                result = await self.like_tweet(tweet_url)

            elif task_type == "retweet":
                tweet_url = payload.get("tweet_url", "")
                result = await self.retweet(tweet_url)

            elif task_type == "quote_tweet":
                tweet_url = payload.get("tweet_url", "")
                text = payload.get("text", "")
                images = payload.get("images")
                result = await self.quote_tweet(tweet_url, text, images)

            else:
                raise XDaemonError(f"Unknown task type: {task_type}")

            # Update statistics
            self.state.total_operations += 1
            if result.get("success"):
                self.state.successful_operations += 1
            else:
                self.state.failed_operations += 1

            # Track last operation
            self.last_operation = {
                "task_id": task.id,
                "task_type": task_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "success": result.get("success"),
            }

            await self._save_state()

            return result

        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            self.state.total_operations += 1
            self.state.failed_operations += 1
            await self._save_state()
            return {
                "success": False,
                "error": str(e),
            }

    async def post_tweet(self, text: str, images: Optional[List[str]] = None) -> Dict:
        """
        Post a tweet on X.com.
        
        Args:
            text: Tweet text content
            images: Optional list of image file paths
            
        Returns:
            dict: {
                "success": bool,
                "tweet_url": str (if successful),
                "error": str (if failed)
            }
        """
        # 🛡️ CRITICAL: Safety check BEFORE operation
        await self._safety_check(OperationType.TWEET)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"📝 Posting tweet (attempt {attempt}/{self.max_retries})")

                page = await self.chrome_pool.get_page()

                # Navigate to X.com
                await page.goto("https://x.com/home", wait_until="domcontentloaded")
                await HumanBehavior.simulate_page_load_wait()  # Human delay

                # Find and click compose box
                compose_box = await self._wait_for_element(
                    page, self.SELECTORS["tweet_compose"]
                )
                await compose_box.click()
                await HumanBehavior.random_micro_pause()  # Human delay

                # Type tweet text with human-like speed
                await HumanBehavior.type_like_human(page, self.SELECTORS["tweet_compose"], text)

                # Upload images if provided
                if images:
                    for image_path in images:
                        try:
                            upload_input = await page.locator(
                                self.SELECTORS["upload_button"]
                            ).first
                            await upload_input.set_input_files(image_path)
                            await asyncio.sleep(1)
                        except Exception as e:
                            logger.warning(f"Image upload failed: {e}")

                # Click post button
                post_button = await self._wait_for_element(
                    page, self.SELECTORS["post_button"]
                )
                await HumanBehavior.simulate_thinking()  # Think before posting
                await post_button.click()

                # Wait for post confirmation
                await HumanBehavior.anti_detection_delay()  # Anti-detection delay

                logger.info("✅ Tweet posted successfully")
                
                # 🛡️ CRITICAL: Record operation for rate limiting
                self.rate_limiter.record_operation(OperationType.TWEET)
                
                return {
                    "success": True,
                    "tweet_url": page.url,  # URL after posting
                    "text": text,
                }

            except PlaywrightTimeoutError as e:
                logger.warning(f"Tweet post timeout (attempt {attempt}): {e}")
                if attempt == self.max_retries:
                    return {
                        "success": False,
                        "error": f"Timeout after {self.max_retries} attempts",
                    }
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Tweet post failed (attempt {attempt}): {e}")
                if attempt == self.max_retries:
                    return {
                        "success": False,
                        "error": str(e),
                    }
                await asyncio.sleep(2)

    async def reply_to_tweet(self, tweet_url: str, text: str) -> Dict:
        """
        Reply to a tweet on X.com.
        
        Args:
            tweet_url: URL of the tweet to reply to
            text: Reply text content
            
        Returns:
            dict: {
                "success": bool,
                "reply_url": str (if successful),
                "error": str (if failed)
            }
        """
        # 🛡️ CRITICAL: Safety check BEFORE operation
        await self._safety_check(OperationType.REPLY)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"💬 Replying to tweet (attempt {attempt}/{self.max_retries})")

                page = await self.chrome_pool.get_page()

                # Navigate to tweet
                await page.goto(tweet_url, wait_until="domcontentloaded")
                await asyncio.sleep(2)

                # Click reply button
                reply_button = await self._wait_for_element(
                    page, self.SELECTORS["reply_button"]
                )
                await reply_button.click()
                await asyncio.sleep(1)

                # Type reply text
                compose_box = await self._wait_for_element(
                    page, self.SELECTORS["tweet_compose"]
                )
                await compose_box.fill(text)
                await asyncio.sleep(1)

                # Click reply post button
                post_button = await self._wait_for_element(
                    page, self.SELECTORS["post_button"]
                )
                await post_button.click()

                # Wait for confirmation
                await HumanBehavior.anti_detection_delay()

                logger.info("✅ Reply posted successfully")
                
                # 🛡️ CRITICAL: Record operation for rate limiting
                self.rate_limiter.record_operation(OperationType.REPLY)
                
                return {
                    "success": True,
                    "reply_url": page.url,
                    "text": text,
                }

            except PlaywrightTimeoutError as e:
                logger.warning(f"Reply timeout (attempt {attempt}): {e}")
                if attempt == self.max_retries:
                    return {
                        "success": False,
                        "error": f"Timeout after {self.max_retries} attempts",
                    }
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Reply failed (attempt {attempt}): {e}")
                if attempt == self.max_retries:
                    return {
                        "success": False,
                        "error": str(e),
                    }
                await asyncio.sleep(2)

    async def like_tweet(self, tweet_url: str) -> Dict:
        """
        Like a tweet on X.com.
        
        Args:
            tweet_url: URL of the tweet to like
            
        Returns:
            dict: {
                "success": bool,
                "error": str (if failed)
            }
        """
        # 🛡️ CRITICAL: Safety check BEFORE operation
        await self._safety_check(OperationType.LIKE)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"❤️  Liking tweet (attempt {attempt}/{self.max_retries})")

                page = await self.chrome_pool.get_page()

                # Navigate to tweet
                await page.goto(tweet_url, wait_until="domcontentloaded")
                await HumanBehavior.simulate_page_load_wait()

                # Find and click like button
                like_button = await self._wait_for_element(
                    page, self.SELECTORS["like_button"]
                )
                await HumanBehavior.simulate_thinking()
                await like_button.click()
                await HumanBehavior.anti_detection_delay()

                logger.info("✅ Tweet liked successfully")
                
                # 🛡️ CRITICAL: Record operation for rate limiting
                self.rate_limiter.record_operation(OperationType.LIKE)
                
                return {
                    "success": True,
                    "tweet_url": tweet_url,
                }

            except PlaywrightTimeoutError as e:
                logger.warning(f"Like timeout (attempt {attempt}): {e}")
                if attempt == self.max_retries:
                    return {
                        "success": False,
                        "error": f"Timeout after {self.max_retries} attempts",
                    }
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Like failed (attempt {attempt}): {e}")
                if attempt == self.max_retries:
                    return {
                        "success": False,
                        "error": str(e),
                    }
                await asyncio.sleep(2)

    async def retweet(self, tweet_url: str) -> Dict:
        """
        Retweet a tweet on X.com.
        
        Args:
            tweet_url: URL of the tweet to retweet
            
        Returns:
            dict: {
                "success": bool,
                "error": str (if failed)
            }
        """
        # 🛡️ CRITICAL: Safety check BEFORE operation
        await self._safety_check(OperationType.RETWEET)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"🔁 Retweeting (attempt {attempt}/{self.max_retries})")

                page = await self.chrome_pool.get_page()

                # Navigate to tweet
                await page.goto(tweet_url, wait_until="domcontentloaded")
                await HumanBehavior.simulate_page_load_wait()

                # Click retweet button
                retweet_button = await self._wait_for_element(
                    page, self.SELECTORS["retweet_button"]
                )
                await retweet_button.click()
                await asyncio.sleep(1)

                # Confirm retweet
                confirm_button = await self._wait_for_element(
                    page, self.SELECTORS["retweet_confirm"]
                )
                await confirm_button.click()
                await asyncio.sleep(1)
                logger.info("✅ Retweet successful")
                
                # 🛡️ CRITICAL: Record operation for rate limiting
                self.rate_limiter.record_operation(OperationType.RETWEET)
                
                return {
                    "success": True,
                    "tweet_url": tweet_url,
                }

            except PlaywrightTimeoutError as e:
                logger.warning(f"Retweet timeout (attempt {attempt}): {e}")
                if attempt == self.max_retries:
                    return {
                        "success": False,
                        "error": f"Timeout after {self.max_retries} attempts",
                    }
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Retweet failed (attempt {attempt}): {e}")
                if attempt == self.max_retries:
                    return {
                        "success": False,
                        "error": str(e),
                    }
                await asyncio.sleep(2)

    async def quote_tweet(
        self, 
        tweet_url: str, 
        text: str, 
        images: Optional[List[str]] = None
    ) -> Dict:
        """
        Quote tweet (retweet with comment) on X.com.
        
        Args:
            tweet_url: URL of the tweet to quote
            text: Your comment text
            images: Optional list of image file paths
            
        Returns:
            dict: {
                "success": bool,
                "quote_tweet_url": str (if successful),
                "error": str (if failed)
            }
        """
        # 🛡️ CRITICAL: Safety check BEFORE operation
        await self._safety_check(OperationType.QUOTE)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"💬 Quote tweeting (attempt {attempt}/{self.max_retries})")

                page = await self.chrome_pool.get_page()

                # Navigate to tweet
                await page.goto(tweet_url, wait_until="domcontentloaded")
                await HumanBehavior.simulate_page_load_wait()

                # Click retweet button
                retweet_button = await self._wait_for_element(
                    page, self.SELECTORS["retweet_button"]
                )
                await retweet_button.click()
                await asyncio.sleep(1)

                # Click "Quote Tweet" option in the menu
                # Note: This selector may need adjustment based on X.com's actual structure
                try:
                    quote_option = await self._wait_for_element(
                        page, 'a[href*="/compose/tweet"]', timeout=5000
                    )
                    await quote_option.click()
                except PlaywrightTimeoutError:
                    # Fallback: try alternative selector
                    quote_option = await self._wait_for_element(
                        page, 'div[role="menuitem"]', timeout=5000
                    )
                    # Get all menu items and click the second one (Quote Tweet)
                    menu_items = await page.locator('div[role="menuitem"]').all()
                    if len(menu_items) >= 2:
                        await menu_items[1].click()
                    else:
                        await quote_option.click()

                await asyncio.sleep(2)

                # Wait for compose dialog to open
                compose_box = await self._wait_for_element(
                    page, self.SELECTORS["tweet_compose"]
                )
                
                # Type quote comment
                await compose_box.fill(text)
                await asyncio.sleep(1)

                # Upload images if provided
                if images:
                    for image_path in images:
                        try:
                            upload_input = await page.locator(
                                self.SELECTORS["upload_button"]
                            ).first
                            await upload_input.set_input_files(image_path)
                            await asyncio.sleep(1)
                        except Exception as e:
                            logger.warning(f"Image upload failed: {e}")

                # Click post button (different selector for quote tweets)
                try:
                    post_button = await self._wait_for_element(
                        page, 'div[data-testid="tweetButton"]'
                    )
                except PlaywrightTimeoutError:
                    # Fallback to inline button
                    post_button = await self._wait_for_element(
                        page, self.SELECTORS["post_button"]
                    )
                
                await HumanBehavior.simulate_thinking()
                await post_button.click()

                # Wait for post confirmation
                await HumanBehavior.anti_detection_delay()

                logger.info("✅ Quote tweet posted successfully")
                
                # 🛡️ CRITICAL: Record operation for rate limiting
                self.rate_limiter.record_operation(OperationType.QUOTE)
                
                return {
                    "success": True,
                    "quote_tweet_url": page.url,  # URL after posting
                    "text": text,
                }

            except PlaywrightTimeoutError as e:
                logger.warning(f"Quote tweet timeout (attempt {attempt}): {e}")
                if attempt == self.max_retries:
                    return {
                        "success": False,
                        "error": f"Timeout after {self.max_retries} attempts",
                    }
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Quote tweet failed (attempt {attempt}): {e}")
                if attempt == self.max_retries:
                    return {
                        "success": False,
                        "error": str(e),
                    }
                await asyncio.sleep(2)

    async def _wait_for_element(self, page: Page, selector: str, timeout: int = None):
        """
        Wait for an element to be visible and return it.
        
        Args:
            page: Playwright page instance
            selector: CSS selector
            timeout: Wait timeout in milliseconds (default: self.element_wait_timeout)
            
        Returns:
            Locator: Element locator
            
        Raises:
            PlaywrightTimeoutError: If element not found within timeout
        """
        timeout = timeout or self.element_wait_timeout
        
        try:
            element = page.locator(selector).first
            await element.wait_for(state="visible", timeout=timeout)
            return element
        except PlaywrightTimeoutError:
            logger.error(f"Element not found: {selector} (timeout: {timeout}ms)")
            raise

    async def _save_state(self) -> None:
        """
        Save daemon state to JSON file.
        
        Path: C:\XHive\data\daemon_state.json
        """
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)

            state_data = self.state.to_dict()
            state_data["last_operation"] = self.last_operation

            with open(self.state_path, "w") as f:
                json.dump(state_data, f, indent=2)

            logger.debug(f"State saved to {self.state_path}")

        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    async def _load_state(self) -> None:
        """
        Load daemon state from JSON file.
        
        Path: C:\XHive\data\daemon_state.json
        """
        try:
            if not self.state_path.exists():
                logger.debug(f"No state file found at {self.state_path}")
                return

            with open(self.state_path, "r") as f:
                data = json.load(f)

            # Restore state (but keep status as stopped on load)
            self.state.total_operations = data.get("total_operations", 0)
            self.state.successful_operations = data.get("successful_operations", 0)
            self.state.failed_operations = data.get("failed_operations", 0)
            self.last_operation = data.get("last_operation")

            logger.info(
                f"✅ State loaded: {self.state.total_operations} total operations"
            )

        except Exception as e:
            logger.error(f"Failed to load state: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()


# Convenience functions for module-level access
async def get_x_daemon() -> XDaemon:
    """Get or create singleton X-Daemon"""
    daemon = XDaemon()
    if daemon.state.status != "running":
        await daemon.start()
    return daemon


async def shutdown_x_daemon() -> None:
    """Shutdown the X-Daemon"""
    daemon = XDaemon()
    await daemon.stop()
