"""
Test Content Generator with Telegram Approval
"""

import asyncio
import logging

from content_generator import ContentGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_single_post():
    """Test single post approval"""
    
    generator = ContentGenerator()
    
    try:
        await generator.start()
        
        # Test post
        result = await generator.create_post_with_approval(
            text="🚀 Testing X-Hive approval system!\n\nThis post should appear in Telegram for approval.",
            auto_skip_high_risk=True,
            timeout_seconds=300  # 5 minutes
        )
        
        logger.info(f"📊 Result: {result}")
        
    finally:
        await generator.stop()


async def test_daily_posts():
    """Test daily 3-post generation"""
    
    generator = ContentGenerator()
    
    try:
        await generator.start()
        
        # Custom post generator
        def my_post_generator(index):
            posts = [
                "🌅 Good morning! Starting the day with some automation.",
                "📈 Mid-day update: Testing X-Hive workflow system.",
                "🌙 Evening wrap-up: All systems operational!"
            ]
            return posts[index] if index < len(posts) else f"Post #{index+1}"
        
        # Generate 3 daily posts
        summary = await generator.generate_daily_posts(
            target_count=3,
            post_generator_func=my_post_generator
        )
        
        logger.info(f"📊 Daily Summary: {summary}")
        
    finally:
        await generator.stop()


if __name__ == "__main__":
    # Test single post
    # asyncio.run(test_single_post())
    
    # Test daily posts (3 posts)
    asyncio.run(test_daily_posts())