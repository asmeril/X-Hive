import asyncio
import logging
from posting.auto_poster import get_auto_poster

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_auto_poster():
    """
    Test auto-poster:
    1. Check for due posts
    2. Post any due tweets
    3. Show results
    """
    
    print("\n" + "="*80)
    print("AUTO-POSTER TEST (ONE-TIME CHECK)")
    print("="*80 + "\n")
    
    auto_poster = get_auto_poster()
    
    print("🔄 Running one-time check for due posts...\n")
    
    await auto_poster.run_once()
    
    print("\n" + "="*80)
    print("✅ AUTO-POSTER TEST COMPLETE")
    print("="*80 + "\n")
    
    print("To run as background service:")
    print("  python posting/auto_poster.py\n")


if __name__ == "__main__":
    asyncio.run(test_auto_poster())
