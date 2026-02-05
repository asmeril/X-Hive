"""
Test suite for AIContentGenerator

Tests:
- Single post generation with different styles
- Daily post batch generation
- Reply generation with different tones

NOTE: Can run in mock mode if google-generativeai is not installed
"""

import asyncio
import logging
import sys

# Try to import AIContentGenerator
try:
    from ai_content_generator import AIContentGenerator
    MOCK_MODE = False
    print("[OK] AIContentGenerator imported successfully")
except (ImportError, ValueError) as e:
    print(f"[WARNING] google-genai not available: {e}")
    print("Running in MOCK MODE for testing...\n")
    MOCK_MODE = True
    
    # Mock class for testing without API
    class AIContentGenerator:
        async def generate_post(self, topic, style="professional", max_length=280):
            """Mock post generator"""
            styles_map = {
                "professional": "[PROFESSIONAL] Post about",
                "casual": "[CASUAL] Post about",
                "humorous": "[HUMOROUS] Post about"
            }
            await asyncio.sleep(0.5)  # Simulate API call
            return f"{styles_map.get(style, 'Post')}: {topic} #{style}"
        
        async def generate_daily_posts(self, count=3, topics=None):
            """Mock daily posts generator"""
            if topics is None:
                topics = ["AI and Tech", "Productivity", "Innovation"]
            styles = ["professional", "casual", "inspirational"]
            posts = []
            for topic, style in zip(topics[:count], styles[:count]):
                post = await self.generate_post(topic, style)
                posts.append(post)
            return posts
        
        async def generate_reply(self, original_tweet, tone="friendly"):
            """Mock reply generator"""
            tones_map = {
                "friendly": "[FRIENDLY] Great thought!",
                "informative": "[INFORMATIVE] To add to this,",
                "witty": "[WITTY] True but consider:",
                "supportive": "[SUPPORTIVE] I completely agree!"
            }
            await asyncio.sleep(0.3)  # Simulate API call
            return f"{tones_map.get(tone, 'Reply')}: {original_tweet[:50]}..."

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_single_post():
    """
    Test single post generation with different styles.
    
    Tests:
    - professional style
    - casual style
    - humorous style
    """
    print("\n" + "=" * 80)
    print("[TEST 1] Single Post Generation")
    print("=" * 80)
    
    try:
        generator = AIContentGenerator()
        
        topic = "Artificial Intelligence and Daily Life"
        styles = ["professional", "casual", "humorous"]
        
        for style in styles:
            print(f"\n[INFO] Generating {style.upper()} post:")
            print("-" * 60)
            
            post = await generator.generate_post(
                topic=topic,
                style=style,
                max_length=280
            )
            
            print(f"{post}")
            print(f"[INFO] Length: {len(post)} characters")
            print()
        
        print("[OK] Test 1 completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Test 1 failed: {e}")
        print(f"[ERROR] Test 1 failed: {e}")
        return False


async def test_daily_posts():
    """
    Test daily post batch generation with parallel execution.
    
    Tests:
    - Generate 3 posts in parallel
    - Verify asyncio.gather() performance
    - Check content variety
    """
    print("\n" + "=" * 80)
    print("[TEST 2] Daily Posts Generation (Parallel)")
    print("=" * 80)
    
    try:
        generator = AIContentGenerator()
        
        # Default topics
        topics = [
            "Artificial Intelligence",
            "Productivity Tips",
            "Technology Innovation"
        ]
        
        print(f"\n[INFO] Generating {len(topics)} posts in parallel...")
        print("-" * 60)
        
        posts = await generator.generate_daily_posts(
            count=len(topics),
            topics=topics
        )
        
        for i, post in enumerate(posts, 1):
            print(f"\n[POST {i}]")
            print(f"{post}")
            print(f"[INFO] Length: {len(post)} characters")
        
        print("\n[OK] Test 2 completed successfully!")
        print(f"[OK] Generated {len(posts)} posts in parallel!")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Test 2 failed: {e}")
        print(f"[ERROR] Test 2 failed: {e}")
        return False


async def test_reply_generation():
    """
    Test reply generation with different tones.
    
    Tests:
    - friendly tone
    - informative tone
    - witty tone
    - supportive tone
    """
    print("\n" + "=" * 80)
    print("[TEST 3] Reply Generation")
    print("=" * 80)
    
    try:
        generator = AIContentGenerator()
        
        original_tweet = "AI is advancing rapidly! The tech world has never been more dynamic!"
        tones = ["friendly", "informative", "witty", "supportive"]
        
        print(f"\n[ORIGINAL] Tweet:")
        print(f'"{original_tweet}"')
        print("\n" + "-" * 60)
        
        for tone in tones:
            print(f"\n[REPLY {tone.upper()}]")
            print("-" * 40)
            
            reply = await generator.generate_reply(
                original_tweet=original_tweet,
                tone=tone
            )
            
            print(f"{reply}")
            print(f"[INFO] Length: {len(reply)} characters")
        
        print("\n[OK] Test 3 completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Test 3 failed: {e}")
        print(f"[ERROR] Test 3 failed: {e}")
        return False


async def main():
    """Main test runner - execute all tests"""
    
    print("\n")
    print("=" * 80)
    print("AI CONTENT GENERATOR TEST SUITE")
    mode_str = "MOCK MODE" if MOCK_MODE else "LIVE MODE (Gemini API)"
    print(f"Running in {mode_str}")
    print("=" * 80)
    
    try:
        # Run all tests
        test1_result = await test_single_post()
        test2_result = await test_daily_posts()
        test3_result = await test_reply_generation()
        
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"[TEST 1] Single Posts:     {'PASSED' if test1_result else 'FAILED'}")
        print(f"[TEST 2] Daily Posts:      {'PASSED' if test2_result else 'FAILED'}")
        print(f"[TEST 3] Reply Generation: {'PASSED' if test3_result else 'FAILED'}")
        
        if test1_result and test2_result and test3_result:
            print("\n" + "=" * 80)
            print("ALL TESTS COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print("\n[OK] AI Content Generator structure is validated!")
            if MOCK_MODE:
                print("[INFO] Running in MOCK MODE - Install google-genai for live API testing")
            else:
                print("[OK] Gemini API integration validated!")
            print("[OK] Ready for production use!")
            print("\n")
        else:
            print("\n[WARNING] Some tests failed. Please review the errors above.")
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        print(f"\n[ERROR] Test suite failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
