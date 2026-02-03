"""
Test Telegram Approval Bot
"""

import asyncio
import logging
from telegram_bot import TelegramApprovalBot, ApprovalStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_approval_request():
    """Test sending approval request"""
    
    bot = TelegramApprovalBot()
    
    try:
        # Start bot
        logger.info("🚀 Starting Telegram bot...")
        await bot.start()
        
        # Send test approval request
        logger.info("📤 Sending test approval request...")
        result = await bot.request_approval(
            draft_id="test_draft_001",
            text="🚀 This is a test post from X-Hive!\n\nTesting the approval workflow. Please click a button.",
            risk_level="low",
            timeout_seconds=300  # 5 minutes
        )
        
        # Print result
        logger.info(f"✅ Approval result: {result}")
        
        if result["status"] == ApprovalStatus.APPROVED:
            logger.info("🎉 Draft APPROVED! Ready to post.")
        elif result["status"] == ApprovalStatus.SKIPPED:
            logger.info("⏭️ Draft SKIPPED. Discarding.")
        elif result["status"] == ApprovalStatus.TIMEOUT:
            logger.info("⏰ Approval TIMEOUT. No decision made.")
        else:
            logger.info(f"✏️ Draft EDITED: {result['status']}")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
    
    finally:
        # Stop bot
        logger.info("🛑 Stopping bot...")
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(test_approval_request())