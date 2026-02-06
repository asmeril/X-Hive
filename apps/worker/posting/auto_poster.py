import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta
import signal
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scheduling.post_scheduler import get_scheduler, PostStatus
from approval.approval_queue import approval_queue
from posting.twitter_poster import get_twitter_poster

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutoPoster:
    """
    Background worker for automatic tweet posting.
    
    Features:
    - Checks for due posts every minute
    - Posts tweets at scheduled time
    - Updates post status
    - Retries on failure
    - Graceful shutdown
    """
    
    def __init__(
        self,
        check_interval: int = 60,  # Check every 60 seconds
        retry_delay: int = 300,    # Retry after 5 minutes
        max_retries: int = 3
    ):
        """
        Initialize auto-poster.
        
        Args:
            check_interval: Seconds between checks
            retry_delay: Seconds to wait before retry
            max_retries: Maximum retry attempts
        """
        
        self.check_interval = check_interval
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        
        self.scheduler = get_scheduler(approval_queue)
        self.twitter_poster = get_twitter_poster()
        
        self.running = False
        self.retry_count = {}  # Track retries per post_id
        
        logger.info("✅ AutoPoster initialized")
        logger.info(f"⏰ Check interval: {check_interval}s")
        logger.info(f"🔄 Retry delay: {retry_delay}s")
        logger.info(f"🔁 Max retries: {max_retries}")
    
    async def start(self):
        """
        Start the auto-poster background worker.
        
        Runs continuously until stopped.
        """
        
        logger.info("🚀 Starting AutoPoster worker...")
        
        # Verify Twitter credentials first
        if not self.twitter_poster.verify_credentials():
            logger.error("❌ Twitter credentials invalid. Cannot start worker.")
            return
        
        self.running = True
        
        logger.info("✅ AutoPoster worker started!")
        logger.info(f"⏰ Checking for due posts every {self.check_interval}s")
        
        try:
            while self.running:
                try:
                    await self._check_and_post()
                except Exception as e:
                    logger.error(f"❌ Error in worker loop: {e}")
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
        
        except asyncio.CancelledError:
            logger.info("🛑 AutoPoster worker cancelled")
        
        finally:
            logger.info("👋 AutoPoster worker stopped")
    
    def stop(self):
        """Stop the auto-poster worker"""
        logger.info("🛑 Stopping AutoPoster worker...")
        self.running = False
    
    async def _check_and_post(self):
        """
        Check for due posts and post them to Twitter.
        """
        
        # Get posts due now (within 5 minutes)
        due_posts = self.scheduler.get_posts_due_now(tolerance_minutes=5)
        
        if not due_posts:
            logger.debug("No posts due right now")
            return
        
        logger.info(f"📋 Found {len(due_posts)} post(s) due for posting")
        
        for post in due_posts:
            try:
                await self._post_tweet(post)
            except Exception as e:
                logger.error(f"❌ Error posting {post.post_id}: {e}")
    
    async def _post_tweet(self, post):
        """
        Post a single tweet to Twitter.
        
        Args:
            post: ScheduledPost object
        """
        
        post_id = post.post_id
        tweet_text = post.approval_item.generated_tweet
        tweet_url = post.approval_item.content_item.url
        
        # Combine tweet text and URL
        full_tweet = f"{tweet_text}\n{tweet_url}"
        
        # Check if already posted
        if post.status == PostStatus.POSTED:
            logger.debug(f"Post {post_id} already posted, skipping")
            return
        
        # Check retry limit
        retry_count = self.retry_count.get(post_id, 0)
        
        if retry_count >= self.max_retries:
            logger.error(
                f"❌ Post {post_id} exceeded max retries ({self.max_retries}). "
                f"Marking as failed."
            )
            self.scheduler.mark_as_failed(
                post_id,
                f"Exceeded max retries ({self.max_retries})"
            )
            return
        
        logger.info(f"📤 Posting tweet: {post_id}")
        logger.info(f"   Scheduled: {post.scheduled_time.strftime('%Y-%m-%d %H:%M')}")
        logger.info(f"   Text: {tweet_text[:50]}...")
        
        # Post to Twitter
        result = self.twitter_poster.post_tweet(full_tweet)
        
        if result:
            # Success!
            twitter_id = result['id']
            
            logger.info(f"✅ Tweet posted successfully!")
            logger.info(f"   Twitter ID: {twitter_id}")
            logger.info(f"   URL: {result['url']}")
            
            # Update post status
            self.scheduler.mark_as_posted(post_id, twitter_id)
            
            # Clear retry count
            if post_id in self.retry_count:
                del self.retry_count[post_id]
        
        else:
            # Failed
            retry_count += 1
            self.retry_count[post_id] = retry_count
            
            logger.error(f"❌ Failed to post tweet {post_id}")
            logger.info(f"🔄 Retry {retry_count}/{self.max_retries}")
            
            if retry_count >= self.max_retries:
                self.scheduler.mark_as_failed(
                    post_id,
                    f"Failed after {retry_count} retries"
                )
    
    async def run_once(self):
        """
        Run one check cycle (useful for testing).
        """
        logger.info("🔄 Running one-time check...")
        await self._check_and_post()
        logger.info("✅ One-time check complete")


# Global instance
_auto_poster: Optional[AutoPoster] = None


def get_auto_poster() -> AutoPoster:
    """Get or create global AutoPoster instance"""
    global _auto_poster
    
    if _auto_poster is None:
        _auto_poster = AutoPoster()
    
    return _auto_poster


async def main():
    """
    Main entry point for running auto-poster as standalone service.
    """
    
    auto_poster = get_auto_poster()
    
    # Setup graceful shutdown
    def signal_handler(sig, frame):
        logger.info(f"\n🛑 Received signal {sig}, shutting down...")
        auto_poster.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start worker
    await auto_poster.start()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("X-HIVE AUTO-POSTER WORKER")
    print("="*80 + "\n")
    print("🤖 Starting automatic tweet posting service...")
    print("⏰ Will check for due posts every minute")
    print("🐦 Will post to Twitter at scheduled times")
    print("\n Press Ctrl+C to stop\n")
    print("="*80 + "\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
