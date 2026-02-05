import asyncio
import sys
import logging
from datetime import datetime, time, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

# Windows fix for Playwright subprocess on Python 3.12+ (must be before chrome_pool import)
# Python 3.12+ changed asyncio subprocess handling, try ProactorEventLoopPolicy first
if sys.platform == "win32" and sys.version_info >= (3, 12):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Import all systems
from chrome_pool import ChromePool
from task_queue import TaskQueue, TaskItem, TaskStatus
from ai_content_generator import AIContentGenerator
from post_scheduler import PostScheduler
from approval_manager import ApprovalManager, OperationType
from health_check import health_checker
from metrics_collector import metrics_collector, increment_counter, record_timing
from structured_logger import task_logger

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    """Orchestrator configuration"""

    # Scheduling
    posts_per_day: int = 3
    post_times: list = field(default_factory=lambda: ["09:00", "14:00", "20:00"])

    # AI Generation
    ai_enabled: bool = True
    ai_topics: list = field(default_factory=lambda: [
        "Yapay zeka ve otomasyon",
        "Verimlilik ipuçları",
        "Teknoloji inovasyonu"
    ])
    ai_style: str = "professional"

    # Approval
    require_approval: bool = False  # Set to True when ApprovalManager is available
    auto_approve_after_minutes: int = 60

    # Health monitoring
    health_check_interval_minutes: int = 5


class Orchestrator:
    """
    Main orchestrator coordinating all X-Hive systems.

    Responsibilities:
    - Schedule daily posts
    - Generate AI content
    - Execute approved posts
    - Monitor system health
    - Collect metrics
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """
        Initialize orchestrator.

        Args:
            config: Orchestrator configuration
        """

        self.config = config or OrchestratorConfig()

        # Initialize components
        self.chrome_pool = ChromePool()
        self.task_queue = TaskQueue()
        self.ai_generator = AIContentGenerator()
        self.scheduler = PostScheduler()
        self.approval_manager = ApprovalManager(
            timeout_seconds=self.config.auto_approve_after_minutes * 60
        )

        # State
        self._running = False
        self._health_check_task: Optional[asyncio.Task] = None

        logger.info("🎯 Orchestrator initialized")

    async def start(self) -> None:
        """Start the orchestrator and all subsystems"""

        if self._running:
            logger.warning("⚠️ Orchestrator already running")
            return

        logger.info("🚀 Starting X-Hive Orchestrator...")

        try:
            # Set approval mode based on config
            if self.config.require_approval:
                self.approval_manager.set_mode('REQUIRED')
                logger.info("✋ Approval mode: REQUIRED")
            else:
                self.approval_manager.set_mode('DISABLED')
                logger.info("✋ Approval mode: DISABLED")

            # Start task queue (auto-starts ChromePool)
            await self.task_queue.start()

            # Start post scheduler
            await self.scheduler.start()

            # Start health monitoring
            self._health_check_task = asyncio.create_task(
                self._health_monitor_loop()
            )

            self._running = True

            logger.info("✅ Orchestrator started successfully")
            task_logger.info(
                "Orchestrator started",
                posts_per_day=self.config.posts_per_day,
                post_times=self.config.post_times,
                ai_enabled=self.config.ai_enabled,
                approval_mode=self.approval_manager.mode
            )

        except Exception as e:
            logger.error(f"❌ Failed to start orchestrator: {e}")
            raise

    async def stop(self) -> None:
        """Stop the orchestrator and all subsystems"""

        if not self._running:
            return

        logger.info("🛑 Stopping X-Hive Orchestrator...")

        # Stop health monitoring
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # Stop subsystems
        await self.scheduler.stop()
        await self.task_queue.stop()

        self._running = False

        logger.info("✅ Orchestrator stopped")
        task_logger.info("Orchestrator stopped")

    async def create_approved_post(self, content: str) -> Dict[str, Any]:
        """Helper method to create post with approval workflow if needed"""
        try:
            # Request approval if required
            if self.config.require_approval:
                approved, reason = await self.approval_manager.request_approval(
                    operation_type=OperationType.POST,
                    payload={'content': content}
                )

                if not approved:
                    logger.warning(f"❌ Post rejected: {reason}")
                    increment_counter('posts_rejected')
                    return {'success': False, 'reason': reason}

            # Add to task queue
            task_id = await self.task_queue.add_task(
                task_type="post_tweet",
                payload={'content': content}
            )

            increment_counter('posts_approved')
            return {'success': True, 'task_id': task_id}

        except Exception as e:
            logger.error(f"❌ Post creation failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _health_monitor_loop(self) -> None:
        """Continuous health monitoring loop"""

        while self._running:
            try:
                # Run health checks
                health_report = await health_checker.check_all(
                    chrome_pool=self.chrome_pool,
                    task_queue=self.task_queue,
                    ai_generator=self.ai_generator
                )

                # Log health status
                overall_status = health_report['overall_status']

                if overall_status == 'healthy':
                    logger.debug("💚 System health: HEALTHY")
                elif overall_status == 'degraded':
                    logger.warning("💛 System health: DEGRADED")
                    task_logger.warning(
                        "System degraded",
                        components=health_report['components']
                    )
                else:
                    logger.error("❤️ System health: UNHEALTHY")
                    task_logger.error(
                        "System unhealthy",
                        components=health_report['components']
                    )

                # Wait for next check
                await asyncio.sleep(self.config.health_check_interval_minutes * 60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Health check error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute

    async def post_now(self, content: str) -> Dict[str, Any]:
        """
        Post immediately (bypass scheduling).

        Args:
            content: Post content

        Returns:
            Result dictionary
        """

        try:
            # Request approval if required
            if self.config.require_approval:
                approved, reason = await self.approval_manager.request_approval(
                    operation_type=OperationType.POST,
                    payload={'content': content, 'immediate': True}
                )

                if not approved:
                    logger.warning(f"❌ Immediate post rejected: {reason}")
                    return {'success': False, 'reason': reason}

            # Create immediate task
            task_id = await self.task_queue.add_task(
                task_type="post_tweet",
                payload={'content': content, 'immediate': True}
            )

            logger.info(f"✅ Immediate post queued (ID: {task_id})")
            increment_counter('posts_immediate')

            return {'success': True, 'task_id': task_id}

        except Exception as e:
            logger.error(f"❌ Immediate post failed: {e}")
            return {'success': False, 'error': str(e)}

    def get_status(self) -> Dict[str, Any]:
        """
        Get orchestrator status.

        Returns:
            Status dictionary
        """

        return {
            'running': self._running,
            'config': {
                'posts_per_day': self.config.posts_per_day,
                'post_times': self.config.post_times,
                'ai_enabled': self.config.ai_enabled,
                'require_approval': self.config.require_approval
            },
            'metrics': metrics_collector.get_metrics_report(),
            'health': health_checker.get_status_summary()
        }


orchestrator = Orchestrator()


async def main():
    """Main entry point for X-Hive"""

    try:
        # Start orchestrator
        await orchestrator.start()

        # Keep running
        logger.info("🎯 X-Hive is running. Press Ctrl+C to stop.")

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("\n⚠️ Shutdown signal received")

    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(main())
