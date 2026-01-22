"""
Rate Limiter for X-Hive
Prevents excessive API usage that triggers X/Twitter bot detection.

Features:
- Per-operation rate limits (tweets, likes, retweets, replies)
- Sliding window algorithm
- Persistent storage (survives restarts)
- Automatic cooldown calculation
- Alert system for approaching limits
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from config import settings

logger = logging.getLogger(__name__)


class OperationType(str, Enum):
    """X operation types"""
    TWEET = "tweet"
    REPLY = "reply"
    QUOTE = "quote"
    LIKE = "like"
    RETWEET = "retweet"


@dataclass
class RateLimit:
    """Rate limit configuration for an operation"""
    hourly_limit: int
    daily_limit: int
    min_interval_seconds: int  # Minimum time between operations


@dataclass
class OperationRecord:
    """Single operation record"""
    operation_type: str
    timestamp: str  # ISO format
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "OperationRecord":
        return cls(**data)


class RateLimiter:
    """
    Rate limiter with persistent storage.
    
    Safety Limits (Conservative - Anti-Ban):
    - Tweets: 10/day, 3/hour, min 10min interval
    - Replies: 15/day, 5/hour, min 5min interval
    - Quotes: 8/day, 3/hour, min 10min interval
    - Likes: 50/day, 20/hour, min 2min interval
    - Retweets: 30/day, 10/hour, min 3min interval
    """
    
    # CRITICAL: These limits are INTENTIONALLY low to avoid ban
    LIMITS: Dict[OperationType, RateLimit] = {
        OperationType.TWEET: RateLimit(
            hourly_limit=3,
            daily_limit=10,
            min_interval_seconds=600  # 10 minutes
        ),
        OperationType.REPLY: RateLimit(
            hourly_limit=5,
            daily_limit=15,
            min_interval_seconds=300  # 5 minutes
        ),
        OperationType.QUOTE: RateLimit(
            hourly_limit=3,
            daily_limit=8,
            min_interval_seconds=600  # 10 minutes
        ),
        OperationType.LIKE: RateLimit(
            hourly_limit=20,
            daily_limit=50,
            min_interval_seconds=120  # 2 minutes
        ),
        OperationType.RETWEET: RateLimit(
            hourly_limit=10,
            daily_limit=30,
            min_interval_seconds=180  # 3 minutes
        ),
    }
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize rate limiter"""
        self.storage_path = Path(storage_path or settings.DATA_PATH) / "rate_limit_history.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Operation history: {operation_type: [OperationRecord]}
        self.history: Dict[str, List[OperationRecord]] = {}
        
        self._load_history()
        logger.info("🛡️ RateLimiter initialized with strict limits")
    
    def _load_history(self) -> None:
        """Load operation history from disk"""
        try:
            if not self.storage_path.exists():
                logger.info("No existing rate limit history found")
                return
            
            with open(self.storage_path, "r") as f:
                data = json.load(f)
            
            self.history = {
                op_type: [OperationRecord.from_dict(rec) for rec in records]
                for op_type, records in data.get("history", {}).items()
            }
            
            # Clean old records (older than 24 hours)
            self._cleanup_old_records()
            
            logger.info(f"📂 Loaded {sum(len(v) for v in self.history.values())} operation records")
        
        except Exception as e:
            logger.error(f"Failed to load rate limit history: {e}")
            self.history = {}
    
    def _save_history(self) -> None:
        """Save operation history to disk"""
        try:
            data = {
                "saved_at": datetime.now().isoformat(),
                "history": {
                    op_type: [rec.to_dict() for rec in records]
                    for op_type, records in self.history.items()
                }
            }
            
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.debug("💾 Rate limit history saved")
        
        except Exception as e:
            logger.error(f"Failed to save rate limit history: {e}")
    
    def _cleanup_old_records(self) -> None:
        """Remove records older than 24 hours"""
        cutoff = datetime.now() - timedelta(hours=24)
        
        for op_type in self.history:
            self.history[op_type] = [
                rec for rec in self.history[op_type]
                if datetime.fromisoformat(rec.timestamp) > cutoff
            ]
    
    def _get_recent_operations(
        self, 
        operation_type: OperationType, 
        hours: int
    ) -> List[OperationRecord]:
        """Get operations within the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        return [
            rec for rec in self.history.get(operation_type.value, [])
            if datetime.fromisoformat(rec.timestamp) > cutoff
        ]
    
    def check_limit(self, operation_type: OperationType) -> Tuple[bool, Optional[str]]:
        """
        Check if operation is allowed under current rate limits.
        
        Returns:
            (allowed: bool, reason: Optional[str])
            - (True, None) if allowed
            - (False, "reason") if blocked
        """
        limit = self.LIMITS[operation_type]
        now = datetime.now()
        
        # Check hourly limit
        hourly_ops = self._get_recent_operations(operation_type, hours=1)
        if len(hourly_ops) >= limit.hourly_limit:
            return False, f"⏰ Hourly limit reached ({limit.hourly_limit}/hour). Wait {self._calculate_cooldown(hourly_ops[0])}."
        
        # Check daily limit
        daily_ops = self._get_recent_operations(operation_type, hours=24)
        if len(daily_ops) >= limit.daily_limit:
            return False, f"📅 Daily limit reached ({limit.daily_limit}/day). Try again tomorrow."
        
        # Check minimum interval
        if daily_ops:
            last_op = daily_ops[-1]
            last_time = datetime.fromisoformat(last_op.timestamp)
            elapsed = (now - last_time).total_seconds()
            
            if elapsed < limit.min_interval_seconds:
                wait_time = int(limit.min_interval_seconds - elapsed)
                return False, f"⏱️ Too soon! Wait {wait_time}s (min interval: {limit.min_interval_seconds}s)."
        
        return True, None
    
    def _calculate_cooldown(self, oldest_record: OperationRecord) -> str:
        """Calculate human-readable cooldown time"""
        oldest_time = datetime.fromisoformat(oldest_record.timestamp)
        cooldown_time = oldest_time + timedelta(hours=1)
        remaining = (cooldown_time - datetime.now()).total_seconds()
        
        if remaining <= 0:
            return "now"
        
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"
    
    def record_operation(self, operation_type: OperationType) -> None:
        """Record a successful operation"""
        if operation_type.value not in self.history:
            self.history[operation_type.value] = []
        
        record = OperationRecord(
            operation_type=operation_type.value,
            timestamp=datetime.now().isoformat()
        )
        
        self.history[operation_type.value].append(record)
        self._save_history()
        
        logger.info(f"✅ Recorded {operation_type.value} operation")
    
    def get_usage_stats(self, operation_type: OperationType) -> Dict:
        """Get current usage statistics for an operation"""
        limit = self.LIMITS[operation_type]
        hourly_ops = self._get_recent_operations(operation_type, hours=1)
        daily_ops = self._get_recent_operations(operation_type, hours=24)
        
        # Calculate next available time
        next_available = "now"
        if daily_ops:
            last_op = daily_ops[-1]
            last_time = datetime.fromisoformat(last_op.timestamp)
            next_time = last_time + timedelta(seconds=limit.min_interval_seconds)
            remaining = (next_time - datetime.now()).total_seconds()
            
            if remaining > 0:
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                next_available = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
        
        return {
            "operation_type": operation_type.value,
            "hourly": {
                "used": len(hourly_ops),
                "limit": limit.hourly_limit,
                "remaining": limit.hourly_limit - len(hourly_ops),
                "percentage": int((len(hourly_ops) / limit.hourly_limit) * 100)
            },
            "daily": {
                "used": len(daily_ops),
                "limit": limit.daily_limit,
                "remaining": limit.daily_limit - len(daily_ops),
                "percentage": int((len(daily_ops) / limit.daily_limit) * 100)
            },
            "min_interval_seconds": limit.min_interval_seconds,
            "next_available": next_available,
            "is_at_risk": (
                len(hourly_ops) >= limit.hourly_limit * 0.8 or 
                len(daily_ops) >= limit.daily_limit * 0.8
            )
        }
    
    def get_all_stats(self) -> Dict:
        """Get usage stats for all operation types"""
        return {
            op_type.value: self.get_usage_stats(op_type)
            for op_type in OperationType
        }
    
    def reset_history(self) -> None:
        """Reset all history (use with caution!)"""
        self.history = {}
        self._save_history()
        logger.warning("⚠️ Rate limit history RESET")


# Singleton instance
_rate_limiter_instance: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get singleton rate limiter instance"""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiter()
    return _rate_limiter_instance
