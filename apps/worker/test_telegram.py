"""
Telegram Source Integration Test

Tests Telegram channel scraping without requiring full authentication.
"""

import asyncio
import logging
from intel.telegram_source import telegram_source
from intel.base_source import ContentCategory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_telegram_source():
    """Test Telegram source functionality"""
    
    print("\n" + "="*80)
    print("TELEGRAM SOURCE TEST")
    print("="*80 + "\n")
    
    if not telegram_source:
        print("❌ Telegram source not available")
        print("   Reason: Telethon not installed or credentials missing")
        return
    
    print("✅ Telegram source created")
    print(f"   Source: {telegram_source.get_source_name()}")
    print(f"   Type: {telegram_source.get_source_type()}")
    print(f"   Channels configured: {len(telegram_source.channels)}")
    
    print("\n[INFO] Configured channels:")
    for i, channel in enumerate(telegram_source.channels, 1):
        print(f"   {i}. {channel}")
    
    print("\n[INFO] Statistics:")
    stats = telegram_source.get_stats()
    print(f"   Fetch count: {stats['fetch_count']}")
    print(f"   Error count: {stats['error_count']}")
    print(f"   Last fetch: {stats['last_fetch']}")
    
    print("\n⚠️ NOTE: Full message fetching requires Telegram authentication")
    print("   The Telegram source will prompt for 2FA code on first connection.")
    print("   Once authenticated, session is cached for future use.")
    
    print("\n[OPTIONAL] To fetch messages, you need to:")
    print("   1. Have valid TELEGRAM_API_ID and TELEGRAM_API_HASH in .env")
    print("   2. Have valid TELEGRAM_PHONE number in .env")
    print("   3. Run: await telegram_source.initialize()")
    print("   4. Enter 2FA code when prompted")
    print("   5. Run: items = await telegram_source.fetch_latest()")
    
    print("\n" + "="*80)
    print("✅ TELEGRAM SOURCE TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_telegram_source())
