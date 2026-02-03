"""
Example usage of PostScheduler in X-Hive application

Shows how to integrate PostScheduler into the main application with
proper initialization, error handling, and shutdown.
"""

import asyncio
import logging
from datetime import time
from post_scheduler import PostScheduler, get_scheduler, shutdown_scheduler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Example 1: Basic usage with default configuration
async def example_basic():
    """Basic example with default post times and content"""
    logger.info("=== Example 1: Basic Usage ===")
    
    scheduler = PostScheduler()
    await scheduler.start()
    
    # Get upcoming posts
    upcoming = scheduler.get_next_scheduled_posts()
    logger.info(f"Scheduled posts: {upcoming}")
    
    # Run for 10 seconds then stop
    await asyncio.sleep(10)
    await scheduler.stop()


# Example 2: Custom post times
async def example_custom_times():
    """Example with custom post times"""
    logger.info("=== Example 2: Custom Post Times ===")
    
    custom_times = [
        time(7, 0),    # 7 AM
        time(12, 30),  # 12:30 PM
        time(18, 0),   # 6 PM
        time(21, 0)    # 9 PM
    ]
    
    scheduler = PostScheduler(post_times=custom_times)
    await scheduler.start()
    
    upcoming = scheduler.get_next_scheduled_posts()
    logger.info(f"Upcoming posts:")
    for post in upcoming:
        logger.info(f"  {post['time']} → {post['next_run_time']}")
    
    await asyncio.sleep(5)
    await scheduler.stop()


# Example 3: Custom content generator
async def example_custom_generator():
    """Example with custom content generation function"""
    logger.info("=== Example 3: Custom Content Generator ===")
    
    def my_content_generator(time_period: str) -> str:
        """Generate custom post content based on time of day"""
        templates = {
            "morning": (
                "🌅 Good morning! X-Hive here with your morning update.\n"
                "What's your plan for today?"
            ),
            "afternoon": (
                "☀️ Afternoon check-in! Hope you're having a productive day.\n"
                "Share your progress with us!"
            ),
            "evening": (
                "🌙 Good evening! Reflecting on the day's achievements.\n"
                "What did you accomplish? Let's discuss!"
            )
        }
        return templates.get(time_period, "Hello X-Hive community!")
    
    scheduler = PostScheduler(
        post_times=[time(9, 0), time(14, 0), time(20, 0)],
        content_generator_func=my_content_generator
    )
    await scheduler.start()
    
    # Trigger a manual post to test the generator
    logger.info("Triggering manual post to test generator...")
    result = await scheduler.trigger_manual_post()
    logger.info(f"Manual post result: {result['status']}")
    
    await asyncio.sleep(5)
    await scheduler.stop()


# Example 4: Manual post triggering
async def example_manual_posts():
    """Example of triggering posts manually"""
    logger.info("=== Example 4: Manual Post Triggering ===")
    
    scheduler = PostScheduler()
    await scheduler.start()
    
    # Trigger with custom text
    logger.info("Triggering custom manual post...")
    result1 = await scheduler.trigger_manual_post(
        text="🚀 Breaking news! Check out our latest update! #XHive"
    )
    logger.info(f"Custom post status: {result1['status']}")
    
    await asyncio.sleep(2)
    
    # Trigger with auto-generated content
    logger.info("Triggering auto-generated manual post...")
    result2 = await scheduler.trigger_manual_post()
    logger.info(f"Auto-generated post status: {result2['status']}")
    
    await asyncio.sleep(5)
    await scheduler.stop()


# Example 5: Rescheduling
async def example_rescheduling():
    """Example of rescheduling posts"""
    logger.info("=== Example 5: Rescheduling Posts ===")
    
    scheduler = PostScheduler()
    await scheduler.start()
    
    logger.info("Initial schedule:")
    for post in scheduler.get_next_scheduled_posts():
        logger.info(f"  {post['time']}")
    
    # Change the schedule
    new_times = [time(8, 0), time(13, 0), time(19, 0), time(22, 0)]
    logger.info(f"Rescheduling to: {[t.strftime('%H:%M') for t in new_times]}")
    
    success = scheduler.reschedule(new_times)
    
    if success:
        logger.info("Updated schedule:")
        for post in scheduler.get_next_scheduled_posts():
            logger.info(f"  {post['time']}")
    else:
        logger.error("Failed to reschedule")
    
    await asyncio.sleep(5)
    await scheduler.stop()


# Example 6: Singleton pattern
async def example_singleton():
    """Example using singleton pattern"""
    logger.info("=== Example 6: Singleton Pattern ===")
    
    # Get or create singleton instance
    scheduler = await get_scheduler(
        post_times=[time(10, 0), time(15, 0)]
    )
    await scheduler.start()
    
    logger.info("Singleton instance created")
    
    # In another part of code, get the same instance
    scheduler2 = await get_scheduler()
    
    assert scheduler is scheduler2, "Should be same instance!"
    logger.info("✓ Confirmed: Same singleton instance")
    
    await asyncio.sleep(5)
    
    # Shutdown singleton
    await shutdown_scheduler()
    logger.info("Singleton shut down")


# Example 7: Integration with application lifecycle
async def example_app_integration():
    """Example of integrating with FastAPI/application lifecycle"""
    logger.info("=== Example 7: Application Integration ===")
    
    scheduler = None
    
    try:
        # Initialize scheduler on app startup
        logger.info("App starting up...")
        scheduler = PostScheduler(
            post_times=[time(9, 0), time(18, 0)]
        )
        await scheduler.start()
        logger.info("✓ PostScheduler ready")
        
        # Simulate app running
        logger.info("App running... (simulating for 10 seconds)")
        await asyncio.sleep(10)
        
    except Exception as e:
        logger.error(f"Error during app execution: {e}", exc_info=True)
    
    finally:
        # Graceful shutdown
        logger.info("App shutting down...")
        if scheduler:
            await scheduler.stop()
        logger.info("✓ App shut down complete")


# Example 8: Error handling
async def example_error_handling():
    """Example showing error handling"""
    logger.info("=== Example 8: Error Handling ===")
    
    scheduler = PostScheduler()
    
    # Try to use methods before starting (should handle gracefully)
    logger.info("Testing uninitialized scheduler...")
    
    result = await scheduler.trigger_manual_post()
    logger.info(f"Manual post result: {result['status']} (expected: failed)")
    
    # Stop without starting
    logger.info("Testing stop without start...")
    await scheduler.stop()
    logger.info("✓ No error on stop")
    
    # Now start properly
    logger.info("Starting scheduler properly...")
    await scheduler.start()
    logger.info("✓ Scheduler started")
    
    # Test reschedule
    success = scheduler.reschedule([time(11, 0)])
    logger.info(f"Reschedule result: {'success' if success else 'failed'}")
    
    await asyncio.sleep(5)
    await scheduler.stop()


# Example 9: Monitoring scheduled posts
async def example_monitoring():
    """Example of monitoring scheduled posts"""
    logger.info("=== Example 9: Monitoring Posts ===")
    
    scheduler = PostScheduler()
    await scheduler.start()
    
    logger.info("Monitoring scheduled posts for 10 seconds...")
    
    for i in range(5):
        upcoming = scheduler.get_next_scheduled_posts()
        logger.info(f"\n[Check {i+1}] Upcoming posts:")
        for post in upcoming:
            logger.info(
                f"  {post['time']:20} → {post['next_run_time']}"
            )
        await asyncio.sleep(2)
    
    await scheduler.stop()


async def main():
    """Run all examples"""
    examples = [
        ("Basic Usage", example_basic),
        ("Custom Times", example_custom_times),
        ("Custom Generator", example_custom_generator),
        ("Manual Posts", example_manual_posts),
        ("Rescheduling", example_rescheduling),
        ("Singleton", example_singleton),
        ("App Integration", example_app_integration),
        ("Error Handling", example_error_handling),
        ("Monitoring", example_monitoring),
    ]
    
    logger.info("=" * 60)
    logger.info("X-Hive PostScheduler Examples")
    logger.info("=" * 60)
    
    for name, example_func in examples:
        try:
            logger.info(f"\n{'='*60}")
            await example_func()
            logger.info(f"✓ {name} completed successfully")
        except Exception as e:
            logger.error(f"✗ {name} failed: {e}", exc_info=True)
        
        await asyncio.sleep(2)
    
    logger.info("\n" + "=" * 60)
    logger.info("All examples completed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
