"""
Test script for Twitter Trends source
"""

import asyncio
import logging
import sys
import os

# Setup path
sys.path.insert(0, os.path.abspath('.'))

from intel.twitter_trends_source import TwitterTrendsSource

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_twitter_trends():
    """Test Twitter Trends source"""
    
    logger.info("=" * 60)
    logger.info("TWITTER TRENDS TEST")
    logger.info("=" * 60)
    
    try:
        # Initialize source
        source = TwitterTrendsSource(limit=20)
        
        # Fetch trends
        logger.info("\n📡 Fetching Twitter trends...")
        items = await source.fetch_latest()
        
        if not items:
            logger.warning("⚠️  No trends found - check cookies and authentication")
            return
        
        # Display results
        logger.info(f"\n✅ Found {len(items)} Twitter trends:")
        logger.info("-" * 60)
        
        for idx, item in enumerate(items, 1):
            logger.info(f"\n{idx}. {item.title}")
            logger.info(f"   URL: {item.url}")
            logger.info(f"   Category: {item.category.value}")
            logger.info(f"   Relevance: {item.relevance_score:.2f}")
            logger.info(f"   Engagement: {item.engagement_score:.2f}")
        
        logger.info("\n" + "=" * 60)
        logger.info(f"✅ Twitter Trends test completed: {len(items)} items")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_twitter_trends())
