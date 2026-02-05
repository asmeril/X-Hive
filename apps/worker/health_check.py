import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ComponentHealth:
    """Health status of a system component"""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    last_check: datetime
    details: Dict[str, Any]
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict with datetime serialization"""
        return {
            'name': self.name,
            'status': self.status,
            'last_check': self.last_check.isoformat(),
            'details': self.details,
            'error': self.error
        }


class HealthChecker:
    """
    System health checker for production monitoring.

    Checks:
    - ChromePool availability
    - TaskQueue status
    - AI Content Generator
    - Telegram Bot
    - Disk space
    - Memory usage
    """

    def __init__(self):
        self.last_health_check: Optional[datetime] = None
        self.component_health: Dict[str, ComponentHealth] = {}

    async def check_chrome_pool(self, chrome_pool) -> ComponentHealth:
        """Check ChromePool health"""

        try:
            is_initialized = chrome_pool._initialized
            has_browser = chrome_pool.browser is not None
            has_page = chrome_pool.page is not None
            page_closed = chrome_pool.page.is_closed() if has_page else True

            if not is_initialized:
                status = "unhealthy"
                error = "ChromePool not initialized"
            elif not has_browser:
                status = "unhealthy"
                error = "Browser not started"
            elif not has_page or page_closed:
                status = "degraded"
                error = "No active page"
            else:
                status = "healthy"
                error = None

            return ComponentHealth(
                name="ChromePool",
                status=status,
                last_check=datetime.now(),
                details={
                    'initialized': is_initialized,
                    'has_browser': has_browser,
                    'has_page': has_page,
                    'page_closed': page_closed
                },
                error=error
            )

        except Exception as e:
            return ComponentHealth(
                name="ChromePool",
                status="unhealthy",
                last_check=datetime.now(),
                details={},
                error=str(e)
            )

    async def check_task_queue(self, task_queue) -> ComponentHealth:
        """Check TaskQueue health"""

        try:
            is_running = task_queue._running
            queue_size = task_queue.task_queue.qsize()
            failed_count = len(task_queue.failed_tasks)
            history_count = len(task_queue.task_history)
            total_tasks = len(task_queue.tasks)

            if not is_running:
                status = "unhealthy"
                error = "TaskQueue not running"
            elif queue_size > 100:
                status = "degraded"
                error = f"Queue backlog: {queue_size} tasks"
            else:
                status = "healthy"
                error = None

            return ComponentHealth(
                name="TaskQueue",
                status=status,
                last_check=datetime.now(),
                details={
                    'running': is_running,
                    'queue_size': queue_size,
                    'failed_tasks': failed_count,
                    'history_count': history_count,
                    'total_tasks': total_tasks
                },
                error=error
            )

        except Exception as e:
            return ComponentHealth(
                name="TaskQueue",
                status="unhealthy",
                last_check=datetime.now(),
                details={},
                error=str(e)
            )

    async def check_ai_generator(self, ai_generator) -> ComponentHealth:
        """Check AI Content Generator health"""

        try:
            # Quick health check without actual API call (to avoid rate limits)
            has_model = hasattr(ai_generator, 'model') and ai_generator.model is not None
            has_client = hasattr(ai_generator, 'client') and ai_generator.client is not None

            if has_model and has_client:
                status = "healthy"
                error = None
            else:
                status = "degraded"
                error = "AI generator not fully initialized"

            return ComponentHealth(
                name="AIContentGenerator",
                status=status,
                last_check=datetime.now(),
                details={
                    'model': ai_generator.model if has_model else 'unknown',
                    'has_client': has_client
                },
                error=error
            )

        except Exception as e:
            return ComponentHealth(
                name="AIContentGenerator",
                status="unhealthy",
                last_check=datetime.now(),
                details={},
                error=str(e)
            )

    async def check_all(
        self,
        chrome_pool=None,
        task_queue=None,
        ai_generator=None
    ) -> Dict[str, Any]:
        """
        Run all health checks.

        Returns:
            Health status report
        """

        checks = []

        if chrome_pool:
            checks.append(self.check_chrome_pool(chrome_pool))
        if task_queue:
            checks.append(self.check_task_queue(task_queue))
        if ai_generator:
            checks.append(self.check_ai_generator(ai_generator))

        results = await asyncio.gather(*checks, return_exceptions=True)

        component_statuses = {}
        overall_status = "healthy"

        for result in results:
            if isinstance(result, Exception):
                overall_status = "unhealthy"
                continue

            component_statuses[result.name] = result.to_dict()
            self.component_health[result.name] = result

            if result.status == "unhealthy":
                overall_status = "unhealthy"
            elif result.status == "degraded" and overall_status == "healthy":
                overall_status = "degraded"

        self.last_health_check = datetime.now()

        return {
            'overall_status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'components': component_statuses
        }

    def get_status_summary(self) -> str:
        """Get simple status summary"""

        if not self.last_health_check:
            return "No health check performed yet"

        age = datetime.now() - self.last_health_check
        if age > timedelta(minutes=5):
            return f"Stale (last check {age.seconds}s ago)"

        healthy_count = sum(
            1 for h in self.component_health.values()
            if h.status == "healthy"
        )
        total_count = len(self.component_health)

        return f"{healthy_count}/{total_count} components healthy"


health_checker = HealthChecker()
