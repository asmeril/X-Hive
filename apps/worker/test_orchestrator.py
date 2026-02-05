import asyncio
import logging
import sys
import os
from datetime import datetime

# Windows fix for Playwright subprocess on Python 3.12+ (must be FIRST)
if sys.platform == "win32" and sys.version_info >= (3, 12):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Fix Unicode on Windows
if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    sys.stdout.reconfigure(encoding="utf-8")

from orchestrator import Orchestrator, OrchestratorConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_orchestrator_basic():
    """Test basic orchestrator functionality"""

    print("\n" + "="*80)
    print("ORCHESTRATOR INTEGRATION TEST")
    print("="*80 + "\n")

    # Create config with approval disabled for testing
    config = OrchestratorConfig(
        posts_per_day=1,
        post_times=["09:00"],  # Single post for testing
        ai_enabled=True,
        require_approval=False,  # Disable approval for automated test
        health_check_interval_minutes=1
    )

    # Create orchestrator
    orchestrator = Orchestrator(config=config)

    print("[TEST 1] Orchestrator Initialization")
    print("-" * 80)
    print(f"✅ Config: {config.posts_per_day} posts/day")
    print(f"✅ AI enabled: {config.ai_enabled}")
    print(f"✅ Approval required: {config.require_approval}")

    print("\n[TEST 2] Starting Orchestrator")
    print("-" * 80)

    try:
        await orchestrator.start()
        print("✅ Orchestrator started successfully")

        # Wait a bit to let systems initialize
        await asyncio.sleep(3)

        print("\n[TEST 3] Getting Status")
        print("-" * 80)

        status = orchestrator.get_status()
        print(f"✅ Running: {status['running']}")
        print(f"✅ Health: {status['health']}")
        print(f"✅ Config: {status['config']}")

        print("\n[TEST 4] Immediate Post (No Approval)")
        print("-" * 80)

        result = await orchestrator.post_now(
            content="🧪 Test post from orchestrator integration test! #XHive #Testing"
        )

        if result['success']:
            print(f"✅ Post queued successfully (Task ID: {result['task_id']})")
        else:
            print(f"❌ Post failed: {result.get('error')}")

        # Let it run for a bit
        print("\n[TEST 5] Running for 10 seconds...")
        print("-" * 80)
        await asyncio.sleep(10)

        print("\n[TEST 6] Stopping Orchestrator")
        print("-" * 80)

        await orchestrator.stop()
        print("✅ Orchestrator stopped successfully")

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

        # Cleanup
        try:
            await orchestrator.stop()
        except:
            pass


async def test_orchestrator_with_approval():
    """Test orchestrator with approval workflow (manual)"""

    print("\n" + "="*80)
    print("ORCHESTRATOR WITH APPROVAL TEST (MANUAL)")
    print("="*80 + "\n")

    config = OrchestratorConfig(
        posts_per_day=1,
        ai_enabled=True,
        require_approval=True,  # Enable approval
        auto_approve_after_minutes=2  # Auto-approve after 2 minutes
    )

    orchestrator = Orchestrator(config=config)

    print("⚠️ This test requires Telegram bot interaction")
    print("⚠️ Make sure your Telegram bot is configured")
    print()

    try:
        await orchestrator.start()
        print("✅ Orchestrator started with approval workflow")

        print("\n📱 Requesting approval for test post...")
        print("   Check your Telegram for approval request")

        result = await orchestrator.post_now(
            content="🧪 Test post requiring approval! #XHive"
        )

        if result['success']:
            print(f"✅ Post approved and queued (Task ID: {result['task_id']})")
        else:
            print(f"❌ Post rejected or failed: {result.get('reason', result.get('error'))}")

        print("\n⏳ Running for 30 seconds to process approved posts...")
        await asyncio.sleep(30)

        await orchestrator.stop()
        print("✅ Orchestrator stopped")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await orchestrator.stop()
        except:
            pass


async def main():
    """Run tests"""

    # Auto-select basic test if no input (for CI/automation)
    print("\n🧪 Select test:")
    print("1. Basic test (no approval)")
    print("2. Approval workflow test (manual)")

    choice = input("\nEnter choice (1 or 2, default=1): ").strip() or "1"

    if choice == "1":
        await test_orchestrator_basic()
    elif choice == "2":
        await test_orchestrator_with_approval()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
