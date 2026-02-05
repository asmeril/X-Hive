#!/usr/bin/env python3
"""
Safe startup test - no Telegram imports
Tests ChromePool, TaskQueue, and basic orchestration
"""

import sys
import os
import asyncio
import logging

# Setup Python event loop for Windows
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add worker path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import core components (skip Telegram)
from orchestrator import Orchestrator


async def main():
    """Test orchestrator startup"""
    logger.info("=" * 60)
    logger.info("🧪 X-Hive Safe Startup Test (No Telegram)")
    logger.info("=" * 60)
    
    try:
        # Initialize orchestrator
        logger.info("\n[1] Initializing orchestrator...")
        orchestrator = Orchestrator()
        
        # Start orchestrator
        logger.info("\n[2] Starting orchestrator...")
        await orchestrator.start()
        
        logger.info("\n[3] System initialized successfully")
        
        logger.info("\n[4] Queuing test post...")
        post_data = await orchestrator.post_now(
            content="🧪 Test post from safe startup"
        )
        post_id = post_data.get('post_id', 'unknown')
        logger.info(f"✅ Post queued: {post_id}")
        
        # Wait a bit
        logger.info("\n⏳ Waiting 5 seconds for processing...")
        await asyncio.sleep(5)
        
        logger.info("\n[5] Shutting down...")
        await orchestrator.shutdown()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Safe startup test PASSED")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
