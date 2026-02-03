"""
Post Scheduler for X-Hive Automated Posting System

Schedules daily posts using APScheduler with Telegram approval workflow.
Provides methods to manage scheduled posts, trigger manual posts, and reschedule.
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Callable, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from content_generator import ContentGenerator

logger = logging.getLogger(__name__)

# Singleton scheduler instance
_scheduler_instance: Optional["PostScheduler"] = None


class PostScheduler:
    """
    Manages automated daily post scheduling with approval workflow.
    
    Schedules posts at specified times daily, integrates with ContentGenerator
    for Telegram approval workflow, and provides manual post triggering.
    
    Features:
    - Configurable post times (default: 9AM, 2PM, 8PM)
    - Time-based greeting content
    - Approval workflow integration
    - Manual post triggering
    - Graceful scheduler shutdown
    - Comprehensive logging with emojis
    - Singleton pattern for global access
    """
    
    def __init__(
        self,
        post_times: Optional[List[time]] = None,
        content_generator_func: Optional[Callable[[str], str]] = None
    ):
        """
        Initialize PostScheduler.
        
        Args:
            post_times: List of datetime.time objects for daily posts.
                       Defaults to [9:00, 14:00, 20:00]
            content_generator_func: Custom function to generate post content.
                                   Receives time period string (morning/afternoon/evening)
                                   and returns post text.
                                   Defaults to time-based greeting generator.
        """
        # Default post times: 9 AM, 2 PM, 8 PM
        self.post_times = post_times or [
            time(9, 0),    # 9:00 AM
            time(14, 0),   # 2:00 PM (14:00)
            time(20, 0)    # 8:00 PM (20:00)
        ]
        
        self.content_generator_func = (
            content_generator_func or self._default_post_generator
        )
        self.content_generator: Optional[ContentGenerator] = None
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
        logger.info(
            f"⏱️ PostScheduler initialized | "
            f"Post times: {[t.strftime('%H:%M') for t in self.post_times]}"
        )
    
    def _determine_time_period(self) -> str:
        """
        Determine current time period for content generation.
        
        Returns:
            "morning" (6-12), "afternoon" (12-18), "evening" (18-6)
        """
        current_hour = datetime.now().hour
        
        if 6 <= current_hour < 12:
            return "morning"
        elif 12 <= current_hour < 18:
            return "afternoon"
        else:
            return "evening"
    
    def _default_post_generator(self, time_period: str) -> str:
        """
        Generate default time-based greeting posts.
        
        Args:
            time_period: "morning", "afternoon", or "evening"
        
        Returns:
            Greeting post text
        """
        greetings = {
            "morning": "🌅 Good morning! Starting the day with X-Hive automated updates. Let's make today productive!",
            "afternoon": "☀️ Good afternoon! Mid-day check-in from X-Hive. Keep pushing forward!",
            "evening": "🌙 Good evening! Wrapping up the day with X-Hive insights. Stay tuned for more tomorrow!"
        }
        
        return greetings.get(time_period, greetings["afternoon"])
    
    async def start(self) -> None:
        """
        Initialize and start the scheduler.
        
        - Initializes ContentGenerator
        - Starts ContentGenerator service
        - Schedules daily post jobs
        - Starts AsyncIOScheduler
        """
        if self.is_running:
            logger.warning("⚠️ PostScheduler is already running")
            return
        
        try:
            # Initialize and start ContentGenerator
            self.content_generator = ContentGenerator()
            await self.content_generator.start()
            logger.info("📨 ContentGenerator started")
            
            # Schedule post jobs for each post time
            for post_time in self.post_times:
                # Create CronTrigger (daily at specified time)
                trigger = CronTrigger(
                    hour=post_time.hour,
                    minute=post_time.minute
                )
                
                job_id = f"scheduled_post_{post_time.hour:02d}_{post_time.minute:02d}"
                
                self.scheduler.add_job(
                    self._scheduled_post_job,
                    trigger=trigger,
                    id=job_id,
                    name=f"Post at {post_time.strftime('%H:%M')}"
                )
                
                logger.info(
                    f"📅 Scheduled job: {job_id} at {post_time.strftime('%H:%M')}"
                )
            
            # Start scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info(
                f"🚀 PostScheduler started | "
                f"{len(self.post_times)} jobs scheduled"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to start PostScheduler: {e}", exc_info=True)
            self.is_running = False
            raise
    
    async def stop(self) -> None:
        """
        Shutdown scheduler gracefully.
        
        - Cancels all pending jobs
        - Shuts down scheduler
        - Stops ContentGenerator
        """
        if not self.is_running:
            logger.warning("⚠️ PostScheduler is not running")
            return
        
        try:
            # Shutdown scheduler
            self.scheduler.shutdown(wait=True)
            logger.info("🛑 AsyncIOScheduler shut down")
            
            # Stop ContentGenerator
            if self.content_generator:
                await self.content_generator.stop()
                logger.info("📭 ContentGenerator stopped")
            
            self.is_running = False
            logger.info("✅ PostScheduler stopped gracefully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping PostScheduler: {e}", exc_info=True)
            raise
    
    async def _scheduled_post_job(self) -> Dict[str, Any]:
        """
        Job that runs at scheduled times.
        
        - Generates time-based greeting content
        - Submits to ContentGenerator approval workflow
        - Logs result
        - 1 hour timeout for approval
        
        Returns:
            {
                "status": str,
                "draft_id": str,
                "task_id": str | None,
                "risk_level": str,
                "timestamp": str,
                "scheduled": True
            }
        """
        if not self.content_generator:
            logger.error("❌ ContentGenerator not initialized")
            return {
                "status": "failed",
                "error": "ContentGenerator not initialized",
                "scheduled": True
            }
        
        try:
            current_time = datetime.now().strftime("%H:%M")
            time_period = self._determine_time_period()
            
            # Generate content
            post_text = self.content_generator_func(time_period)
            
            logger.info(
                f"🎬 Running scheduled post job at {current_time} "
                f"({time_period})"
            )
            
            # Submit for approval (1 hour timeout = 3600 seconds)
            result = await self.content_generator.create_post_with_approval(
                text=post_text,
                auto_skip_high_risk=True,
                timeout_seconds=3600
            )
            
            result["timestamp"] = datetime.now().isoformat()
            result["scheduled"] = True
            
            logger.info(
                f"📤 Scheduled post job completed | "
                f"Status: {result['status']} | Draft: {result.get('draft_id', 'N/A')}"
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"❌ Error in scheduled post job: {e}",
                exc_info=True
            )
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "scheduled": True
            }
    
    async def trigger_manual_post(
        self,
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Manually trigger a post outside the schedule.
        
        Args:
            text: Post content. If None, generates default content for current time.
        
        Returns:
            {
                "status": str,
                "draft_id": str,
                "task_id": str | None,
                "risk_level": str,
                "timestamp": str,
                "manual": True
            }
        """
        if not self.content_generator:
            logger.error("❌ ContentGenerator not initialized")
            return {
                "status": "failed",
                "error": "ContentGenerator not initialized",
                "manual": True
            }
        
        try:
            # Use provided text or generate default
            if text is None:
                time_period = self._determine_time_period()
                text = self.content_generator_func(time_period)
                logger.info(f"📝 Generated default content for {time_period}")
            
            logger.info(f"🎬 Triggering manual post | Length: {len(text)}")
            
            # Submit for approval (30 minute timeout = 1800 seconds)
            result = await self.content_generator.create_post_with_approval(
                text=text,
                auto_skip_high_risk=True,
                timeout_seconds=1800
            )
            
            result["timestamp"] = datetime.now().isoformat()
            result["manual"] = True
            
            logger.info(
                f"📤 Manual post completed | "
                f"Status: {result['status']} | Draft: {result.get('draft_id', 'N/A')}"
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"❌ Error triggering manual post: {e}",
                exc_info=True
            )
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "manual": True
            }
    
    def get_next_scheduled_posts(self) -> List[Dict[str, Any]]:
        """
        Get list of upcoming scheduled posts.
        
        Returns:
            List of dicts with keys:
            {
                "time": str (HH:MM format),
                "job_id": str,
                "next_run_time": str (ISO format),
                "timezone": str
            }
        """
        if not self.is_running or not self.scheduler.running:
            logger.warning("⚠️ Scheduler not running")
            return []
        
        upcoming_posts = []
        
        try:
            jobs = self.scheduler.get_jobs()
            
            for job in jobs:
                if job.next_run_time:
                    upcoming_posts.append({
                        "time": job.name,
                        "job_id": job.id,
                        "next_run_time": job.next_run_time.isoformat(),
                        "timezone": str(job.trigger.timezone) if hasattr(job.trigger, 'timezone') else "UTC"
                    })
            
            # Sort by next run time
            upcoming_posts.sort(
                key=lambda x: x["next_run_time"]
            )
            
            logger.info(
                f"📋 Retrieved {len(upcoming_posts)} upcoming scheduled posts"
            )
            
            return upcoming_posts
            
        except Exception as e:
            logger.error(
                f"❌ Error getting scheduled posts: {e}",
                exc_info=True
            )
            return []
    
    def reschedule(self, new_post_times: List[time]) -> bool:
        """
        Update post schedule with new times.
        
        Args:
            new_post_times: List of new datetime.time objects
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_running or not self.scheduler.running:
            logger.error("❌ Scheduler not running, cannot reschedule")
            return False
        
        try:
            logger.info(f"🔄 Rescheduling posts to: {[t.strftime('%H:%M') for t in new_post_times]}")
            
            # Remove all existing jobs
            self.scheduler.remove_all_jobs()
            logger.info("🗑️ Removed all existing jobs")
            
            # Update post times
            self.post_times = new_post_times
            
            # Reschedule jobs
            for post_time in self.post_times:
                trigger = CronTrigger(
                    hour=post_time.hour,
                    minute=post_time.minute
                )
                
                job_id = f"scheduled_post_{post_time.hour:02d}_{post_time.minute:02d}"
                
                self.scheduler.add_job(
                    self._scheduled_post_job,
                    trigger=trigger,
                    id=job_id,
                    name=f"Post at {post_time.strftime('%H:%M')}"
                )
                
                logger.info(f"📅 Rescheduled job: {job_id} at {post_time.strftime('%H:%M')}")
            
            logger.info(
                f"✅ PostScheduler rescheduled | "
                f"{len(self.post_times)} jobs"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error rescheduling posts: {e}", exc_info=True)
            return False


async def get_scheduler(
    post_times: Optional[List[time]] = None,
    content_generator_func: Optional[Callable] = None
) -> PostScheduler:
    """
    Get or create singleton PostScheduler instance.
    
    Args:
        post_times: Post times for new instance (ignored if instance exists)
        content_generator_func: Content generator for new instance (ignored if exists)
    
    Returns:
        PostScheduler singleton instance
    """
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = PostScheduler(
            post_times=post_times,
            content_generator_func=content_generator_func
        )
        logger.info("✨ PostScheduler singleton created")
    else:
        logger.info("♻️ Returning existing PostScheduler singleton")
    
    return _scheduler_instance


async def shutdown_scheduler() -> None:
    """
    Shutdown the singleton PostScheduler instance.
    
    Gracefully stops the scheduler and cleans up resources.
    """
    global _scheduler_instance
    
    if _scheduler_instance is not None:
        await _scheduler_instance.stop()
        _scheduler_instance = None
        logger.info("🧹 PostScheduler singleton shut down and cleared")
    else:
        logger.warning("⚠️ No PostScheduler instance to shut down")
