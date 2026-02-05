#!/usr/bin/env python3
"""
Auto-run orchestrator basic test for validation
"""

import asyncio
import logging
import sys
import os

# Windows fix for Playwright subprocess on Python 3.12+ (must be FIRST)
if sys.platform == "win32" and sys.version_info >= (3, 12):
    # Try ProactorEventLoop for Python 3.14 compatibility
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except:
        # Fallback to WindowsSelectorEventLoopPolicy
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Fix Unicode on Windows
if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    sys.stdout.reconfigure(encoding="utf-8")

from test_orchestrator import test_orchestrator_basic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run basic test"""
    try:
        await test_orchestrator_basic()
        print("\n✅ Test completed successfully")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
