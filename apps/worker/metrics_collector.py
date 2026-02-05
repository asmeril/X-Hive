import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import logging

from config import settings

logger = logging.getLogger(__name__)

METRICS_FILE = Path(settings.DATA_PATH) / "metrics.json"


@dataclass
class Metric:
    """Single metric data point"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'labels': self.labels
        }


@dataclass
class MetricsSummary:
    """Aggregated metrics summary"""
    total_posts: int = 0
    successful_posts: int = 0
    failed_posts: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    dlq_tasks: int = 0
    avg_task_duration_ms: float = 0.0
    avg_ai_generation_time_ms: float = 0.0
    total_retries: int = 0
    chrome_pool_utilization: float = 0.0
    uptime_seconds: float = 0.0
    last_post_time: Optional[str] = None


class MetricsCollector:
    """
    Production metrics collector for X-Hive.

    Tracks:
    - Task execution metrics (count, duration, success rate)
    - AI generation metrics (time, token usage)
    - System metrics (uptime, resource usage)
    - Error metrics (failures, retries)
    """

    def __init__(self):
        self.metrics: List[Metric] = []
        self.start_time = datetime.now()
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self._load_metrics()

    def _load_metrics(self) -> None:
        """Load metrics from disk"""
        if not METRICS_FILE.exists():
            return

        try:
            with open(METRICS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.counters = defaultdict(int, data.get('counters', {}))
                logger.info("📊 Loaded metrics from disk")
        except Exception as e:
            logger.error(f"❌ Failed to load metrics: {e}")

    def _save_metrics(self) -> None:
        """Save metrics to disk"""
        try:
            METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(METRICS_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'counters': dict(self.counters),
                    'last_updated': datetime.now().isoformat(),
                    'uptime_seconds': self.get_uptime_seconds()
                }, f, indent=2)
            logger.debug("💾 Metrics saved to disk")
        except Exception as e:
            logger.error(f"❌ Failed to save metrics: {e}")

    def increment(self, metric_name: str, value: int = 1, **labels) -> None:
        """
        Increment a counter metric.

        Args:
            metric_name: Name of the metric (e.g., 'tasks_completed')
            value: Amount to increment by
            labels: Optional labels for the metric
        """
        key = f"{metric_name}_{json.dumps(labels, sort_keys=True)}" if labels else metric_name
        self.counters[key] += value
        self.metrics.append(Metric(
            name=metric_name,
            value=value,
            labels=labels
        ))
        self._save_metrics()

    def record_timing(self, metric_name: str, duration_ms: float, **labels) -> None:
        """
        Record a timing metric.

        Args:
            metric_name: Name of the metric (e.g., 'task_duration')
            duration_ms: Duration in milliseconds
            labels: Optional labels
        """
        key = f"{metric_name}_{json.dumps(labels, sort_keys=True)}" if labels else metric_name
        self.timers[key].append(duration_ms)
        if len(self.timers[key]) > 1000:
            self.timers[key] = self.timers[key][-1000:]
        self.metrics.append(Metric(
            name=metric_name,
            value=duration_ms,
            labels=labels
        ))

    def get_counter(self, metric_name: str) -> int:
        """Get current value of a counter"""
        return self.counters.get(metric_name, 0)

    def get_average_timing(self, metric_name: str) -> float:
        """Get average timing for a metric"""
        timings = self.timers.get(metric_name, [])
        if not timings:
            return 0.0
        return sum(timings) / len(timings)

    def get_uptime_seconds(self) -> float:
        """Get system uptime in seconds"""
        return (datetime.now() - self.start_time).total_seconds()

    def get_summary(self) -> MetricsSummary:
        """
        Get aggregated metrics summary.

        Returns:
            MetricsSummary with all current metrics
        """
        total_posts = self.get_counter('posts_attempted')
        successful_posts = self.get_counter('posts_successful')
        failed_posts = self.get_counter('posts_failed')

        total_tasks = self.get_counter('tasks_created')
        completed_tasks = self.get_counter('tasks_completed')
        failed_tasks = self.get_counter('tasks_failed')
        dlq_tasks = self.get_counter('tasks_dlq')

        return MetricsSummary(
            total_posts=total_posts,
            successful_posts=successful_posts,
            failed_posts=failed_posts,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            dlq_tasks=dlq_tasks,
            avg_task_duration_ms=self.get_average_timing('task_duration'),
            avg_ai_generation_time_ms=self.get_average_timing('ai_generation_time'),
            total_retries=self.get_counter('task_retries'),
            chrome_pool_utilization=self.get_counter('chrome_pool_utilization_pct') / 100.0,
            uptime_seconds=self.get_uptime_seconds(),
            last_post_time=self.counters.get('last_post_timestamp')
        )

    def get_metrics_report(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics report.

        Returns:
            Dictionary with all metrics and summary
        """
        summary = self.get_summary()

        post_success_rate = 0.0
        if summary.total_posts > 0:
            post_success_rate = (summary.successful_posts / summary.total_posts) * 100

        task_success_rate = 0.0
        if summary.total_tasks > 0:
            task_success_rate = (summary.completed_tasks / summary.total_tasks) * 100

        return {
            'timestamp': datetime.now().isoformat(),
            'uptime': {
                'seconds': summary.uptime_seconds,
                'human_readable': str(timedelta(seconds=int(summary.uptime_seconds)))
            },
            'posts': {
                'total': summary.total_posts,
                'successful': summary.successful_posts,
                'failed': summary.failed_posts,
                'success_rate_pct': round(post_success_rate, 2),
                'last_post': summary.last_post_time
            },
            'tasks': {
                'total': summary.total_tasks,
                'completed': summary.completed_tasks,
                'failed': summary.failed_tasks,
                'dlq': summary.dlq_tasks,
                'success_rate_pct': round(task_success_rate, 2),
                'total_retries': summary.total_retries,
                'avg_duration_ms': round(summary.avg_task_duration_ms, 2)
            },
            'ai': {
                'avg_generation_time_ms': round(summary.avg_ai_generation_time_ms, 2)
            },
            'system': {
                'chrome_pool_utilization_pct': round(summary.chrome_pool_utilization * 100, 2)
            }
        }

    def reset(self) -> None:
        """Reset all metrics"""
        self.counters.clear()
        self.timers.clear()
        self.metrics.clear()
        self.start_time = datetime.now()
        self._save_metrics()
        logger.info("🔄 Metrics reset")


metrics_collector = MetricsCollector()


def increment_counter(metric_name: str, value: int = 1, **labels):
    """Increment a counter metric"""
    metrics_collector.increment(metric_name, value, **labels)


def record_timing(metric_name: str, duration_ms: float, **labels):
    """Record a timing metric"""
    metrics_collector.record_timing(metric_name, duration_ms, **labels)


def get_metrics_report() -> Dict[str, Any]:
    """Get metrics report"""
    return metrics_collector.get_metrics_report()


EXAMPLE_USAGE = """
from metrics_collector import increment_counter, record_timing
import time

async def _process_task(self, task: TaskItem) -> None:
    start_time = time.time()

    increment_counter('tasks_created', task_type=task.type)

    try:
        # ... execute task ...

        # Success
        duration_ms = (time.time() - start_time) * 1000
        record_timing('task_duration', duration_ms, task_type=task.type)
        increment_counter('tasks_completed', task_type=task.type)

    except Exception as e:
        increment_counter('tasks_failed', task_type=task.type)
        increment_counter('task_retries')
"""
