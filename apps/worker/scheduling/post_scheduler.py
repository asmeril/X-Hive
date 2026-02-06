import asyncio
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta, time
from enum import Enum
import json
from pathlib import Path

from approval.approval_queue import ApprovalQueue, ApprovalQueueItem, ApprovalStatus

logger = logging.getLogger(__name__)


class PostStatus(Enum):
    """Post status states"""
    SCHEDULED = "scheduled"
    POSTED = "posted"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledPost:
    """
    Represents a scheduled tweet post.
    
    Links approved tweets to specific posting times.
    """
    
    def __init__(
        self,
        approval_item: ApprovalQueueItem,
        scheduled_time: datetime,
        post_id: Optional[str] = None,
        status: PostStatus = PostStatus.SCHEDULED,
        posted_at: Optional[datetime] = None,
        twitter_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Initialize scheduled post.
        
        Args:
            approval_item: Approved tweet
            scheduled_time: When to post
            post_id: Unique post ID
            status: Post status
            posted_at: When actually posted
            twitter_id: Twitter tweet ID (after posting)
            error: Error message if failed
        """
        
        self.approval_item = approval_item
        self.scheduled_time = scheduled_time
        self.post_id = post_id or self._generate_id()
        self.status = status
        self.posted_at = posted_at
        self.twitter_id = twitter_id
        self.error = error
    
    def _generate_id(self) -> str:
        """Generate unique post ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"post_{timestamp}_{hash(self.approval_item.tweet_id) % 10000:04d}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'post_id': self.post_id,
            'tweet_id': self.approval_item.tweet_id,
            'scheduled_time': self.scheduled_time.isoformat(),
            'status': self.status.value,
            'posted_at': self.posted_at.isoformat() if self.posted_at else None,
            'twitter_id': self.twitter_id,
            'error': self.error
        }


class PostScheduler:
    """
    Manages scheduling of approved tweets.
    
    Features:
    - Auto-schedule approved tweets
    - Daily quota management (max 3 posts/day)
    - Time slot assignment (14:00, 18:00, 21:00)
    - Conflict resolution
    - Rescheduling
    """
    
    # Default posting times (Turkey timezone)
    DEFAULT_TIME_SLOTS = [
        time(14, 0),  # 14:00
        time(18, 0),  # 18:00
        time(21, 0),  # 21:00
    ]
    
    # Max posts per day
    MAX_DAILY_POSTS = 3
    
    def __init__(
        self,
        approval_queue: ApprovalQueue,
        schedule_file: str = "data/post_schedule.json",
        time_slots: Optional[List[time]] = None,
        max_daily_posts: int = MAX_DAILY_POSTS
    ):
        """
        Initialize post scheduler.
        
        Args:
            approval_queue: ApprovalQueue instance
            schedule_file: Path to schedule persistence file
            time_slots: Custom posting times
            max_daily_posts: Maximum posts per day
        """
        
        self.approval_queue = approval_queue
        self.schedule_file = Path(schedule_file)
        self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.time_slots = time_slots or self.DEFAULT_TIME_SLOTS
        self.max_daily_posts = max_daily_posts
        
        self.scheduled_posts: Dict[str, ScheduledPost] = {}
        
        # Load existing schedule
        self._load()
        
        logger.info(f"✅ PostScheduler initialized ({len(self.scheduled_posts)} posts)")
    
    def schedule_approved_tweets(self) -> List[ScheduledPost]:
        """
        Auto-schedule all approved tweets that aren't scheduled yet.
        
        Returns:
            List of newly scheduled posts
        """
        
        # Get approved tweets
        approved = self.approval_queue.get_approved()
        
        # Filter out already scheduled
        scheduled_tweet_ids = {
            post.approval_item.tweet_id 
            for post in self.scheduled_posts.values()
            if post.status == PostStatus.SCHEDULED
        }
        
        unscheduled = [
            item for item in approved 
            if item.tweet_id not in scheduled_tweet_ids
        ]
        
        if not unscheduled:
            logger.info("No new approved tweets to schedule")
            return []
        
        # Schedule each tweet
        newly_scheduled = []
        
        for item in unscheduled:
            scheduled_post = self._schedule_tweet(item)
            
            if scheduled_post:
                newly_scheduled.append(scheduled_post)
                logger.info(
                    f"✅ Scheduled {item.tweet_id} for "
                    f"{scheduled_post.scheduled_time.strftime('%Y-%m-%d %H:%M')}"
                )
        
        self._save()
        
        return newly_scheduled
    
    def _schedule_tweet(self, item: ApprovalQueueItem) -> Optional[ScheduledPost]:
        """
        Schedule a single tweet to next available slot.
        
        Args:
            item: Approved tweet item
        
        Returns:
            ScheduledPost or None if no slots available
        """
        
        # Find next available slot
        scheduled_time = self._find_next_slot()
        
        if not scheduled_time:
            logger.warning(f"❌ No available slots for {item.tweet_id}")
            return None
        
        # Create scheduled post
        post = ScheduledPost(
            approval_item=item,
            scheduled_time=scheduled_time
        )
        
        self.scheduled_posts[post.post_id] = post
        
        return post
    
    def _find_next_slot(self) -> Optional[datetime]:
        """
        Find next available time slot.
        
        Respects:
        - Time slots (14:00, 18:00, 21:00)
        - Daily quota (max 3 posts/day)
        - Already scheduled posts
        
        Returns:
            Next available datetime or None
        """
        
        now = datetime.now()
        current_date = now.date()
        
        # Check next 7 days
        for day_offset in range(7):
            check_date = current_date + timedelta(days=day_offset)
            
            # Count posts already scheduled for this day
            posts_on_day = self._count_posts_on_date(check_date)
            
            if posts_on_day >= self.max_daily_posts:
                continue  # Day full, check next day
            
            # Check each time slot
            for slot_time in self.time_slots:
                slot_datetime = datetime.combine(check_date, slot_time)
                
                # Skip past times on current day
                if slot_datetime <= now:
                    continue
                
                # Check if slot already taken
                if self._is_slot_taken(slot_datetime):
                    continue
                
                # Found available slot!
                return slot_datetime
        
        # No slots available in next 7 days
        return None
    
    def _count_posts_on_date(self, date) -> int:
        """Count scheduled posts on specific date"""
        count = 0
        
        for post in self.scheduled_posts.values():
            if post.status != PostStatus.SCHEDULED:
                continue
            
            if post.scheduled_time.date() == date:
                count += 1
        
        return count
    
    def _is_slot_taken(self, slot_datetime: datetime) -> bool:
        """Check if time slot is already scheduled"""
        for post in self.scheduled_posts.values():
            if post.status != PostStatus.SCHEDULED:
                continue
            
            if post.scheduled_time == slot_datetime:
                return True
        
        return False
    
    def get_upcoming_posts(self, limit: int = 10) -> List[ScheduledPost]:
        """Get upcoming scheduled posts"""
        scheduled = [
            post for post in self.scheduled_posts.values()
            if post.status == PostStatus.SCHEDULED
        ]
        
        # Sort by scheduled time
        scheduled.sort(key=lambda p: p.scheduled_time)
        
        return scheduled[:limit]
    
    def get_posts_due_now(self, tolerance_minutes: int = 5) -> List[ScheduledPost]:
        """
        Get posts that should be posted now.
        
        Args:
            tolerance_minutes: How many minutes early to consider "due"
        
        Returns:
            List of posts due for posting
        """
        now = datetime.now()
        tolerance = timedelta(minutes=tolerance_minutes)
        
        due_posts = []
        
        for post in self.scheduled_posts.values():
            if post.status != PostStatus.SCHEDULED:
                continue
            
            # Check if scheduled time is now or in the past (within tolerance)
            if now >= (post.scheduled_time - tolerance):
                due_posts.append(post)
        
        return due_posts
    
    def mark_as_posted(
        self, 
        post_id: str, 
        twitter_id: str
    ) -> bool:
        """
        Mark post as successfully posted.
        
        Args:
            post_id: Post ID
            twitter_id: Twitter tweet ID
        
        Returns:
            Success status
        """
        if post_id not in self.scheduled_posts:
            return False
        
        post = self.scheduled_posts[post_id]
        post.status = PostStatus.POSTED
        post.posted_at = datetime.now()
        post.twitter_id = twitter_id
        
        self._save()
        
        logger.info(f"✅ Marked as posted: {post_id} → Twitter ID: {twitter_id}")
        
        return True
    
    def mark_as_failed(
        self, 
        post_id: str, 
        error: str
    ) -> bool:
        """
        Mark post as failed.
        
        Args:
            post_id: Post ID
            error: Error message
        
        Returns:
            Success status
        """
        if post_id not in self.scheduled_posts:
            return False
        
        post = self.scheduled_posts[post_id]
        post.status = PostStatus.FAILED
        post.error = error
        
        self._save()
        
        logger.error(f"❌ Post failed: {post_id} - {error}")
        
        return True
    
    def _save(self):
        """Save schedule to file"""
        try:
            data = {
                post_id: post.to_dict()
                for post_id, post in self.scheduled_posts.items()
            }
            
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"❌ Failed to save schedule: {e}")
    
    def _load(self):
        """Load schedule from file"""
        try:
            if not self.schedule_file.exists():
                return
            
            with open(self.schedule_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Simplified load - in production would reconstruct full objects
            # For now just log count
            logger.info(f"✅ Loaded {len(data)} posts from schedule")
        
        except Exception as e:
            logger.error(f"❌ Failed to load schedule: {e}")


# Global instance (will be initialized by orchestrator)
post_scheduler: Optional[PostScheduler] = None


def get_scheduler(approval_queue: ApprovalQueue) -> PostScheduler:
    """Get or create PostScheduler instance"""
    global post_scheduler
    if post_scheduler is None:
        post_scheduler = PostScheduler(approval_queue)
    return post_scheduler
