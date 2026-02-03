"""
Integration tests for PostScheduler

Manual testing file to verify PostScheduler functionality.
Tests scheduling, manual posts, and immediate scheduling.

Note: Some tests require Telegram bot configuration.
"""

import asyncio
import logging
from datetime import datetime, time, timedelta, timezone
from post_scheduler import PostScheduler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_next_scheduled():
    """
    Test getting next scheduled posts.
    
    Verifies:
    - Scheduler initialization with default times
    - get_next_scheduled_posts() returns correct jobs
    - Formatted datetime output for all upcoming posts
    """
    logger.info("=" * 70)
    logger.info("TEST 1: test_next_scheduled()")
    logger.info("=" * 70)
    
    try:
        # Create scheduler with default times (9 AM, 2 PM, 8 PM)
        logger.info("Creating PostScheduler with default times...")
        scheduler = PostScheduler(
            post_times=[time(9, 0), time(14, 0), time(20, 0)]
        )
        logger.info(f"✅ Scheduler created with post times: {[t.strftime('%H:%M') for t in scheduler.post_times]}")
        
        # Start scheduler
        logger.info("Starting scheduler...")
        await scheduler.start()
        logger.info("✅ Scheduler started successfully")
        
        # Get next scheduled posts
        logger.info("\nFetching next scheduled posts...")
        upcoming = scheduler.get_next_scheduled_posts()
        
        if upcoming:
            logger.info(f"✅ Found {len(upcoming)} upcoming scheduled posts:\n")
            
            for i, post in enumerate(upcoming, 1):
                # Parse and format datetime
                next_run = datetime.fromisoformat(post['next_run_time'])
                formatted_time = next_run.strftime("%A, %B %d, %Y at %H:%M:%S")
                now = datetime.now(timezone.utc)
                time_until = next_run - now
                
                # Calculate hours and minutes until post
                total_seconds = int(time_until.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                
                logger.info(f"  Post #{i}")
                logger.info(f"    Time: {post['time']}")
                logger.info(f"    Job ID: {post['job_id']}")
                logger.info(f"    Next Run: {formatted_time}")
                logger.info(f"    Time Until: {hours}h {minutes}m")
                logger.info(f"    Timezone: {post['timezone']}\n")
        else:
            logger.warning("⚠️ No upcoming scheduled posts found")
        
        # Stop scheduler
        logger.info("Stopping scheduler...")
        await scheduler.stop()
        logger.info("✅ Scheduler stopped successfully")
        
        logger.info("\n✅ TEST 1 COMPLETED SUCCESSFULLY\n")
        
    except Exception as e:
        logger.error(f"❌ TEST 1 FAILED: {e}", exc_info=True)


async def test_manual_trigger():
    """
    Test manual post triggering.
    
    Verifies:
    - Scheduler initialization
    - Custom content generator function
    - trigger_manual_post() with custom content
    - Result handling and logging
    
    NOTE: Requires Telegram bot to be configured!
    """
    logger.info("=" * 70)
    logger.info("TEST 2: test_manual_trigger()")
    logger.info("=" * 70)
    logger.warning("⚠️ This test requires Telegram bot configuration!")
    
    try:
        # Define custom content generator
        def custom_generator(time_period: str) -> str:
            """Generate custom test post content"""
            templates = {
                "morning": "🌅 MORNING TEST POST: Rise and shine! This is an automated test post.",
                "afternoon": "☀️ AFTERNOON TEST POST: Mid-day energy! This is an automated test post.",
                "evening": "🌙 EVENING TEST POST: Reflect and recharge! This is an automated test post."
            }
            return templates.get(time_period, "🧪 TEST POST: Hello from PostScheduler test!")
        
        # Create scheduler with custom generator
        logger.info("Creating PostScheduler with custom content generator...")
        scheduler = PostScheduler(
            post_times=[time(9, 0), time(14, 0), time(20, 0)],
            content_generator_func=custom_generator
        )
        logger.info("✅ Scheduler created with custom generator")
        
        # Start scheduler
        logger.info("Starting scheduler...")
        await scheduler.start()
        logger.info("✅ Scheduler started successfully")
        
        # Determine current time period
        current_hour = datetime.now().hour
        if 6 <= current_hour < 12:
            time_period = "morning"
        elif 12 <= current_hour < 18:
            time_period = "afternoon"
        else:
            time_period = "evening"
        
        # Generate custom content
        custom_content = custom_generator(time_period)
        logger.info(f"\n🎬 Triggering manual post with custom content...")
        logger.info(f"   Time Period: {time_period}")
        logger.info(f"   Content: {custom_content}\n")
        
        # Trigger manual post with custom content
        result = await scheduler.trigger_manual_post(text=custom_content)
        
        # Log result
        logger.info("📋 Manual Post Result:")
        logger.info(f"   Status: {result.get('status', 'unknown')}")
        logger.info(f"   Draft ID: {result.get('draft_id', 'N/A')}")
        logger.info(f"   Task ID: {result.get('task_id', 'N/A')}")
        logger.info(f"   Risk Level: {result.get('risk_level', 'N/A')}")
        logger.info(f"   Timestamp: {result.get('timestamp', 'N/A')}")
        logger.info(f"   Manual: {result.get('manual', False)}\n")
        
        if result['status'] == 'posted':
            logger.info("✅ Post submitted successfully!")
        elif result['status'] == 'auto_skipped':
            logger.warning("⚠️ Post was auto-skipped (high-risk content)")
        elif result['status'] == 'failed':
            logger.error(f"❌ Post failed: {result.get('error', 'Unknown error')}")
        else:
            logger.info(f"⏭️ Post status: {result['status']}")
        
        # Stop scheduler
        logger.info("\nStopping scheduler...")
        await scheduler.stop()
        logger.info("✅ Scheduler stopped successfully")
        
        logger.info("\n✅ TEST 2 COMPLETED SUCCESSFULLY\n")
        
    except Exception as e:
        logger.error(f"❌ TEST 2 FAILED: {e}", exc_info=True)


async def test_immediate_schedule():
    """
    Test immediate scheduling (post in 1 minute).
    
    Verifies:
    - Scheduler with custom immediate times
    - Scheduled job execution timing
    - Logging of current and scheduled times
    
    NOTE: Requires Telegram bot to be configured!
    """
    logger.info("=" * 70)
    logger.info("TEST 3: test_immediate_schedule()")
    logger.info("=" * 70)
    logger.warning("⚠️ This test requires Telegram bot configuration!")
    logger.warning("⚠️ This test will wait 2 minutes for post to trigger")
    
    try:
        # Get current time
        now = datetime.now()
        logger.info(f"\n📅 Current Time: {now.strftime('%H:%M:%S')}")
        
        # Schedule post 1 minute from now
        scheduled_time = now + timedelta(minutes=1)
        scheduled_time_obj = scheduled_time.time()
        
        logger.info(f"📅 Scheduled Post Time: {scheduled_time.strftime('%H:%M:%S')}")
        logger.info(f"⏱️ Time Until Post: ~1 minute\n")
        
        # Create scheduler with immediate time
        logger.info("Creating PostScheduler with 1-minute-from-now schedule...")
        scheduler = PostScheduler(
            post_times=[scheduled_time_obj]
        )
        logger.info(f"✅ Scheduler created | Posting at {scheduled_time.strftime('%H:%M:%S')}")
        
        # Start scheduler
        logger.info("Starting scheduler...")
        await scheduler.start()
        logger.info("✅ Scheduler started successfully")
        
        # Get next scheduled posts
        logger.info("\n📋 Next Scheduled Posts:")
        upcoming = scheduler.get_next_scheduled_posts()
        for post in upcoming:
            next_run = datetime.fromisoformat(post['next_run_time'])
            logger.info(f"   {post['time']} → {next_run.strftime('%H:%M:%S')}")
        
        # Wait for scheduled post to trigger
        logger.info("\n⏳ Waiting for scheduled post to trigger...")
        logger.info("   (Waiting ~2 minutes for post execution)\n")
        
        # Wait 120 seconds (2 minutes) for post to execute
        wait_seconds = 120
        for i in range(wait_seconds):
            elapsed = i + 1
            remaining = wait_seconds - elapsed
            
            # Log every 10 seconds
            if (i + 1) % 10 == 0:
                logger.info(f"   ⏱️ {elapsed}s elapsed, {remaining}s remaining...")
            
            await asyncio.sleep(1)
        
        logger.info(f"✅ Wait period completed")
        
        # Check final status
        logger.info("\n📊 Final Status:")
        final_posts = scheduler.get_next_scheduled_posts()
        if final_posts:
            logger.info(f"   Still have {len(final_posts)} scheduled posts")
        else:
            logger.info("   No more scheduled posts (today's post executed)")
        
        # Stop scheduler
        logger.info("\nStopping scheduler...")
        await scheduler.stop()
        logger.info("✅ Scheduler stopped successfully")
        
        logger.info("\n✅ TEST 3 COMPLETED SUCCESSFULLY\n")
        
    except Exception as e:
        logger.error(f"❌ TEST 3 FAILED: {e}", exc_info=True)


async def main():
    """Run integration tests"""
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 68 + "║")
    logger.info("║" + "  PostScheduler Integration Tests".center(68) + "║")
    logger.info("║" + " " * 68 + "║")
    logger.info("╚" + "=" * 68 + "╝\n")
    
    # Run test_next_scheduled by default (doesn't require Telegram)
    await test_next_scheduled()
    
    # Uncomment below to run tests that require Telegram bot:
    # =========================================================
    
    # await test_manual_trigger()
    # await test_immediate_schedule()
    
    # =========================================================
    
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + "All tests completed!".center(68) + "║")
    logger.info("║" + " " * 68 + "║")
    logger.info("║" + "Run tests that require Telegram by uncommenting them.".center(68) + "║")
    logger.info("╚" + "=" * 68 + "╝\n")


if __name__ == "__main__":
    asyncio.run(main())
