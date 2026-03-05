import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import settings

logger = logging.getLogger(__name__)


class InteractionTracker:
    def __init__(self, file_path: Optional[str] = None):
        default_path = Path(settings.DATA_PATH) / "interaction_events.json"
        self.file_path = Path(file_path) if file_path else default_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _load(self) -> List[Dict[str, Any]]:
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, list) else []
        except Exception as error:
            logger.warning(f"InteractionTracker load failed: {error}")
            return []

    def _save(self, events: List[Dict[str, Any]]) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as file:
                json.dump(events, file, ensure_ascii=False, indent=2)
        except Exception as error:
            logger.warning(f"InteractionTracker save failed: {error}")

    def record_event(
        self,
        action: str,
        status: str,
        item_id: Optional[str] = None,
        source: str = "system",
        details: Optional[Dict[str, Any]] = None,
        viral_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        now = datetime.utcnow()
        event = {
            "event_id": f"evt_{int(now.timestamp() * 1000)}",
            "timestamp": now.isoformat() + "Z",
            "action": action,
            "status": status,
            "item_id": item_id,
            "source": source,
            "viral_score": viral_score,
            "details": details or {},
        }

        with self._lock:
            events = self._load()
            events.append(event)
            if len(events) > 3000:
                events = events[-3000:]
            self._save(events)

        return event

    @staticmethod
    def _parse_ts(value: str) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None

    def build_dashboard(self, approval_queue, limit: int = 80) -> Dict[str, Any]:
        with self._lock:
            events = self._load()

        recent_events = sorted(events, key=lambda item: item.get("timestamp", ""), reverse=True)[:limit]

        since_24h = datetime.utcnow() - timedelta(hours=24)
        events_24h = []
        for event in events:
            ts = self._parse_ts(event.get("timestamp", ""))
            if ts and ts >= since_24h:
                events_24h.append(event)

        def count(action: str, status: str) -> int:
            return sum(1 for event in events_24h if event.get("action") == action and event.get("status") == status)

        thread_started = count("thread_publish", "started")
        thread_success = count("thread_publish", "success")
        thread_failed = count("thread_publish", "failed")
        sniper_started = count("sniper", "started")
        sniper_success = count("sniper", "success")
        sniper_preview_done = count("sniper", "preview_done")
        sniper_failed = count("sniper", "failed")
        approvals = count("approval", "approved")
        rejections = count("approval", "rejected")

        thread_total_finished = thread_success + thread_failed
        thread_success_rate = round((thread_success / thread_total_finished) * 100, 1) if thread_total_finished else 0.0

        queue_items = list(approval_queue.items.values())
        total_items = len(queue_items)
        pending = sum(1 for item in queue_items if item.status.value == "pending")
        approved = sum(1 for item in queue_items if item.status.value == "approved")
        rejected = sum(1 for item in queue_items if item.status.value == "rejected")
        processed = sum(1 for item in queue_items if item.status.value == "processed")

        processed_scores = [float(getattr(item, "viral_score", 0) or 0) for item in queue_items if item.status.value == "processed"]
        pending_scores = [float(getattr(item, "viral_score", 0) or 0) for item in queue_items if item.status.value == "pending"]

        avg_processed_score = round(sum(processed_scores) / len(processed_scores), 2) if processed_scores else 0.0
        avg_pending_score = round(sum(pending_scores) / len(pending_scores), 2) if pending_scores else 0.0
        high_score_processed = sum(1 for score in processed_scores if score >= 8.0)

        return {
            "kpis": {
                "thread_started_24h": thread_started,
                "thread_success_24h": thread_success,
                "thread_failed_24h": thread_failed,
                "thread_success_rate_24h": thread_success_rate,
                "sniper_started_24h": sniper_started,
                "sniper_success_24h": sniper_success,
                "sniper_preview_done_24h": sniper_preview_done,
                "sniper_failed_24h": sniper_failed,
                "approvals_24h": approvals,
                "rejections_24h": rejections,
            },
            "queue": {
                "total": total_items,
                "pending": pending,
                "approved": approved,
                "rejected": rejected,
                "processed": processed,
            },
            "viral_proxy": {
                "avg_processed_score": avg_processed_score,
                "avg_pending_score": avg_pending_score,
                "high_score_processed": high_score_processed,
                "note": "Gerçek impression/engagement verisi yoksa bu skorlar viral potansiyel proxy'sidir.",
            },
            "recent_events": recent_events,
        }


_tracker_instance: Optional[InteractionTracker] = None


def get_interaction_tracker() -> InteractionTracker:
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = InteractionTracker()
    return _tracker_instance
