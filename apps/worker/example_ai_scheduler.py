"""
Example: PostScheduler with AI Content Generator

Shows how to integrate AIContentGenerator with PostScheduler
for fully automated, AI-powered daily posting.
"""

import asyncio
import logging
from datetime import time
from post_scheduler import PostScheduler, get_scheduler, shutdown_scheduler
from ai_content_generator import AIContentGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Example 1: Basic AI-powered scheduler
async def example_basic_ai_scheduler():
    """Basic example: PostScheduler with AI content generation"""
    logger.info("=" * 70)
    logger.info("EXAMPLE 1: Basic AI-Powered Scheduler")
    logger.info("=" * 70)
    
    # Initialize AI generator
    ai_gen = AIContentGenerator()
    
    # Define AI content generator function
    async def ai_content_generator(time_period: str) -> str:
        """Generate AI content based on time of day"""
        topics = {
            "morning": "Günün başlangıcı ve motivasyon",
            "afternoon": "Verimlilik ve iş hayatı ipuçları",
            "evening": "Günün özeti ve teknoloji haberleri"
        }
        
        styles = {
            "morning": "inspirational",
            "afternoon": "professional",
            "evening": "casual"
        }
        
        topic = topics.get(time_period, "Teknoloji ve inovasyon")
        style = styles.get(time_period, "professional")
        
        logger.info(f"🎨 Generating {style} post for {time_period}...")
        post = await ai_gen.generate_post(topic=topic, style=style)
        
        return post
    
    # Create scheduler with AI generator
    scheduler = PostScheduler(
        post_times=[time(9, 0), time(14, 0), time(20, 0)],
        content_generator_func=ai_content_generator
    )
    
    await scheduler.start()
    logger.info("✅ AI-powered scheduler started!")
    
    # Test manual post with AI
    logger.info("\n🎬 Testing manual AI post...")
    result = await scheduler.trigger_manual_post()
    logger.info(f"📤 Manual post result: {result['status']}")
    
    await asyncio.sleep(5)
    await scheduler.stop()
    logger.info("✅ Example 1 completed\n")


# Example 2: Advanced AI scheduler with custom topics
async def example_advanced_ai_scheduler():
    """Advanced example: Custom topics for each time slot"""
    logger.info("=" * 70)
    logger.info("EXAMPLE 2: Advanced AI Scheduler with Custom Topics")
    logger.info("=" * 70)
    
    ai_gen = AIContentGenerator()
    
    # Advanced configuration with specific topics
    time_configs = {
        "morning": {
            "topics": ["Yapay zeka haberleri", "Günün motivasyonu", "Teknoloji trendleri"],
            "style": "inspirational"
        },
        "afternoon": {
            "topics": ["Verimlilik ipuçları", "İş dünyası", "Otomasyon çözümleri"],
            "style": "professional"
        },
        "evening": {
            "topics": ["Günün özeti", "Teknoloji yorumları", "Sektör analizi"],
            "style": "casual"
        }
    }
    
    post_counter = {"morning": 0, "afternoon": 0, "evening": 0}
    
    async def advanced_ai_generator(time_period: str) -> str:
        """Generate AI content with rotating topics"""
        config = time_configs.get(time_period, time_configs["afternoon"])
        
        # Rotate through topics
        topic_index = post_counter[time_period] % len(config["topics"])
        topic = config["topics"][topic_index]
        post_counter[time_period] += 1
        
        logger.info(f"🎨 Generating {config['style']} post | Topic: {topic}")
        
        post = await ai_gen.generate_post(
            topic=topic,
            style=config["style"],
            max_length=280
        )
        
        return post
    
    scheduler = PostScheduler(
        post_times=[time(8, 0), time(13, 0), time(19, 0)],
        content_generator_func=advanced_ai_generator
    )
    
    await scheduler.start()
    logger.info("✅ Advanced AI scheduler started!")
    
    await asyncio.sleep(5)
    await scheduler.stop()
    logger.info("✅ Example 2 completed\n")


# Example 3: AI scheduler with fallback
async def example_ai_with_fallback():
    """Example with fallback to default content if AI fails"""
    logger.info("=" * 70)
    logger.info("EXAMPLE 3: AI Scheduler with Fallback")
    logger.info("=" * 70)
    
    ai_gen = AIContentGenerator()
    
    async def ai_with_fallback(time_period: str) -> str:
        """Generate AI content with fallback mechanism"""
        try:
            # Try AI generation
            topic = f"{time_period.capitalize()} teknoloji güncellemesi"
            post = await ai_gen.generate_post(topic=topic, style="professional")
            
            logger.info(f"✅ AI content generated for {time_period}")
            return post
            
        except Exception as e:
            # Fallback to default content
            logger.warning(f"⚠️ AI generation failed, using fallback: {e}")
            
            fallbacks = {
                "morning": "🌅 Günaydın! Yeni bir gün, yeni fırsatlar! #Motivasyon #XHive",
                "afternoon": "☀️ Öğleden sonra enerjisi! Verimli çalışmaya devam! #Verimlilik #XHive",
                "evening": "🌙 Güzel bir gün geçirdiniz mi? Yarın görüşmek üzere! #GünSonu #XHive"
            }
            
            return fallbacks.get(time_period, "🤖 X-Hive güncellemesi #Otomasyon")
    
    scheduler = PostScheduler(
        post_times=[time(10, 0), time(15, 0), time(21, 0)],
        content_generator_func=ai_with_fallback
    )
    
    await scheduler.start()
    logger.info("✅ AI scheduler with fallback started!")
    
    await asyncio.sleep(5)
    await scheduler.stop()
    logger.info("✅ Example 3 completed\n")


# Example 4: Singleton pattern with AI
async def example_singleton_ai():
    """Example using singleton pattern with AI generator"""
    logger.info("=" * 70)
    logger.info("EXAMPLE 4: Singleton Pattern with AI")
    logger.info("=" * 70)
    
    ai_gen = AIContentGenerator()
    
    async def simple_ai_gen(time_period: str) -> str:
        return await ai_gen.generate_post(
            topic=f"{time_period.capitalize()} update",
            style="professional"
        )
    
    # Get singleton scheduler
    scheduler = await get_scheduler(
        post_times=[time(11, 0), time(16, 0)],
        content_generator_func=simple_ai_gen
    )
    
    await scheduler.start()
    logger.info("✅ Singleton AI scheduler started!")
    
    # Trigger manual AI post
    result = await scheduler.trigger_manual_post()
    logger.info(f"📤 Manual AI post: {result['status']}")
    
    await asyncio.sleep(5)
    
    # Shutdown singleton
    await shutdown_scheduler()
    logger.info("✅ Example 4 completed\n")


# Example 5: Daily batch AI content generation
async def example_daily_batch():
    """Generate daily posts in batch and schedule them"""
    logger.info("=" * 70)
    logger.info("EXAMPLE 5: Daily Batch AI Generation")
    logger.info("=" * 70)
    
    ai_gen = AIContentGenerator()
    
    # Generate 3 posts for the day
    logger.info("📝 Generating 3 AI posts for daily schedule...")
    
    topics = [
        "Yapay zeka ve iş dünyası",
        "Otomasyon ipuçları",
        "Teknoloji haberleri"
    ]
    
    posts = await ai_gen.generate_daily_posts(count=3, topics=topics)
    
    logger.info(f"✅ Generated {len(posts)} posts\n")
    
    for i, post in enumerate(posts, 1):
        logger.info(f"Post #{i} ({len(post)} chars):")
        logger.info(f"{post}\n")
    
    # You would then feed these to PostScheduler or ContentGenerator
    logger.info("💡 These posts can now be sent to ContentGenerator for approval")
    logger.info("✅ Example 5 completed\n")


async def main():
    """Run all examples"""
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 68 + "║")
    logger.info("║" + "  PostScheduler + AI Content Generator Examples".center(68) + "║")
    logger.info("║" + " " * 68 + "║")
    logger.info("╚" + "=" * 68 + "╝\n")
    
    # Run examples
    # Note: Examples 1-4 require Telegram bot to be configured
    # Uncomment to run:
    
    # await example_basic_ai_scheduler()
    # await example_advanced_ai_scheduler()
    # await example_ai_with_fallback()
    # await example_singleton_ai()
    
    # Example 5 doesn't require Telegram (just generates content)
    await example_daily_batch()
    
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + "Examples completed!".center(68) + "║")
    logger.info("║" + " " * 68 + "║")
    logger.info("║" + "Uncomment other examples to test with Telegram bot.".center(68) + "║")
    logger.info("╚" + "=" * 68 + "╝\n")


if __name__ == "__main__":
    asyncio.run(main())
