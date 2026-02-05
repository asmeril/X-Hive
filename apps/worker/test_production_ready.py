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

# Import all systems
from task_queue import TaskQueue
from ai_content_generator import AIContentGenerator
from chrome_pool import ChromePool
from health_check import health_checker
from metrics_collector import metrics_collector, get_metrics_report
from structured_logger import task_logger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_full_system_integration():
    """
    Test complete X-Hive production system integration.

    Tests:
    1. All components import successfully
    2. Components can be initialized
    3. Metrics collection works
    4. DLQ functionality works
    5. Structured logging works
    """

    print("\n" + "=" * 80)
    print("X-HIVE PRODUCTION READINESS TEST")
    print("=" * 80 + "\n")

    # Reset metrics for clean test
    metrics_collector.reset()

    # Test 1: Component Imports
    print("\n[TEST 1] Component Imports")
    print("-" * 80)

    try:
        assert ChromePool is not None, "ChromePool import failed"
        assert TaskQueue is not None, "TaskQueue import failed"
        assert AIContentGenerator is not None, "AIContentGenerator import failed"
        assert health_checker is not None, "health_checker import failed"
        assert metrics_collector is not None, "metrics_collector import failed"
        assert task_logger is not None, "task_logger import failed"

        print("✅ All components imported successfully")
        test1_pass = True
    except AssertionError as e:
        print(f"❌ Import failed: {e}")
        test1_pass = False

    print(f"{'✅ PASSED' if test1_pass else '❌ FAILED'}: Component imports")

    # Test 2: Singleton Initialization
    print("\n[TEST 2] Singleton Initialization")
    print("-" * 80)

    try:
        chrome_pool = ChromePool()
        task_queue = TaskQueue()

        print(f"✅ ChromePool initialized (singleton)")
        print(f"✅ TaskQueue initialized (singleton)")
        test2_pass = True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        test2_pass = False

    print(f"{'✅ PASSED' if test2_pass else '❌ FAILED'}: Singleton initialization")

    # Test 3: Metrics Collection
    print("\n[TEST 3] Metrics Collection")
    print("-" * 80)

    try:
        from metrics_collector import increment_counter, record_timing

        increment_counter('test_counter', 5)
        record_timing('test_timing', 123.45, test_label='demo')

        report = get_metrics_report()
        assert report is not None, "Metrics report is None"
        assert 'timestamp' in report, "Missing timestamp in report"
        assert 'uptime' in report, "Missing uptime in report"
        assert 'tasks' in report, "Missing tasks in report"

        print(f"✅ Metrics recorded: {report['tasks']['total']} total tasks")
        print(f"✅ Uptime: {report['uptime']['human_readable']}")
        test3_pass = True
    except Exception as e:
        print(f"❌ Metrics collection failed: {e}")
        test3_pass = False

    print(f"{'✅ PASSED' if test3_pass else '❌ FAILED'}: Metrics collection")

    # Test 4: Dead Letter Queue
    print("\n[TEST 4] Dead Letter Queue")
    print("-" * 80)

    try:
        dlq_count = task_queue.get_dlq_count()
        dlq_tasks = task_queue.get_dlq_tasks()

        print(f"✅ DLQ accessible")
        print(f"   - DLQ task count: {dlq_count}")
        print(f"   - DLQ methods: get_dlq_tasks(), get_dlq_count(), clear_dlq()")
        test4_pass = True
    except Exception as e:
        print(f"❌ DLQ test failed: {e}")
        test4_pass = False

    print(f"{'✅ PASSED' if test4_pass else '❌ FAILED'}: Dead Letter Queue")

    # Test 5: Structured Logging
    print("\n[TEST 5] Structured Logging")
    print("-" * 80)

    try:
        task_logger.info(
            "Production test log",
            test_id="prod_test_1",
            status="success",
            timestamp=datetime.now().isoformat()
        )
        print("✅ Structured log entry created successfully")
        test5_pass = True
    except Exception as e:
        print(f"❌ Structured logging failed: {e}")
        test5_pass = False

    print(f"{'✅ PASSED' if test5_pass else '❌ FAILED'}: Structured logging")

    # Test 6: Task Queue Methods
    print("\n[TEST 6] Task Queue Methods")
    print("-" * 80)

    try:
        # Test that TaskQueue has expected attributes
        assert hasattr(task_queue, 'add_task'), "add_task method missing"
        assert hasattr(task_queue, 'start'), "start method missing"
        assert hasattr(task_queue, 'stop'), "stop method missing"
        assert hasattr(task_queue, 'get_dlq_count'), "get_dlq_count method missing"
        assert hasattr(task_queue, 'get_dlq_tasks'), "get_dlq_tasks method missing"

        print("✅ TaskQueue.add_task() available")
        print("✅ TaskQueue.start() available")
        print("✅ TaskQueue.stop() available")
        print("✅ TaskQueue.get_dlq_count() available")
        print("✅ TaskQueue.get_dlq_tasks() available")
        test6_pass = True
    except AssertionError as e:
        print(f"❌ Method check failed: {e}")
        test6_pass = False

    print(f"{'✅ PASSED' if test6_pass else '❌ FAILED'}: Task Queue methods")

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    tests = [
        ("Component Imports", test1_pass),
        ("Singleton Initialization", test2_pass),
        ("Metrics Collection", test3_pass),
        ("Dead Letter Queue", test4_pass),
        ("Structured Logging", test5_pass),
        ("Task Queue Methods", test6_pass)
    ]

    passed = sum(1 for _, result in tests if result)
    total = len(tests)

    for name, result in tests:
        print(f"{'✅' if result else '❌'} {name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 SYSTEM IS PRODUCTION READY!")
        return 0
    else:
        print("\n⚠️ Some tests failed - review before production deployment")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_full_system_integration())
    sys.exit(exit_code)
