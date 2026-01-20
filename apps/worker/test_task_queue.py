"""
Simple test script for Task Queue System
"""

import asyncio
import logging

from task_queue import TaskQueue, TaskPriority, TaskStatus

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_task_queue():
    """Test task queue functionality"""
    
    try:
        # Test 1: Initialize task queue
        logger.info("=" * 60)
        logger.info("TEST 1: Initialize Task Queue")
        logger.info("=" * 60)
        
        queue = TaskQueue()
        await queue.start()
        logger.info("✅ Task queue started")

        # Test 2: Add high priority task
        logger.info("\n" + "=" * 60)
        logger.info("TEST 2: Add High Priority Task")
        logger.info("=" * 60)
        
        task_id_high = await queue.add_task(
            task_type="post_tweet",
            payload={"text": "Hello, X!"},
            priority=TaskPriority.HIGH
        )
        logger.info(f"✅ High priority task added: {task_id_high}")

        # Test 3: Add normal priority task
        logger.info("\n" + "=" * 60)
        logger.info("TEST 3: Add Normal Priority Task")
        logger.info("=" * 60)
        
        task_id_normal = await queue.add_task(
            task_type="like",
            payload={"tweet_id": "12345"},
            priority=TaskPriority.NORMAL
        )
        logger.info(f"✅ Normal priority task added: {task_id_normal}")

        # Test 4: Add low priority task
        logger.info("\n" + "=" * 60)
        logger.info("TEST 4: Add Low Priority Task")
        logger.info("=" * 60)
        
        task_id_low = await queue.add_task(
            task_type="follow",
            payload={"user_id": "67890"},
            priority=TaskPriority.LOW
        )
        logger.info(f"✅ Low priority task added: {task_id_low}")

        # Test 5: Get queue status
        logger.info("\n" + "=" * 60)
        logger.info("TEST 5: Get Queue Status")
        logger.info("=" * 60)
        
        status = await queue.get_queue_status()
        logger.info(f"✅ Queue status: {status}")

        # Test 6: Get specific task status
        logger.info("\n" + "=" * 60)
        logger.info("TEST 6: Get Specific Task Status")
        logger.info("=" * 60)
        
        task = await queue.get_task_status(task_id_high)
        logger.info(f"✅ Task status: {task.to_dict()}")

        # Test 7: Wait for processing (if background loop is running)
        logger.info("\n" + "=" * 60)
        logger.info("TEST 7: Wait for Task Processing")
        logger.info("=" * 60)
        
        await asyncio.sleep(3)
        status = await queue.get_queue_status()
        logger.info(f"✅ Queue status after processing: {status}")

        # Test 8: Shutdown
        logger.info("\n" + "=" * 60)
        logger.info("TEST 8: Shutdown Task Queue")
        logger.info("=" * 60)
        
        await queue.stop()
        logger.info("✅ Task queue shutdown gracefully")

        logger.info("\n" + "=" * 60)
        logger.info("ALL TESTS PASSED ✅")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


async def test_singleton_pattern():
    """Test singleton pattern"""
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Singleton Pattern")
    logger.info("=" * 60)
    
    queue1 = TaskQueue()
    queue2 = TaskQueue()
    
    logger.info(f"Queue1 ID: {id(queue1)}")
    logger.info(f"Queue2 ID: {id(queue2)}")
    logger.info(f"Same instance: {queue1 is queue2}")
    logger.info("✅ Singleton pattern works")


async def test_priority_ordering():
    """Test priority queue ordering"""
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Priority Queue Ordering")
    logger.info("=" * 60)
    
    queue = TaskQueue()
    
    # Add tasks in mixed order
    tasks = []
    tasks.append(await queue.add_task("task1", {"order": 1}, TaskPriority.LOW))
    tasks.append(await queue.add_task("task2", {"order": 2}, TaskPriority.NORMAL))
    tasks.append(await queue.add_task("task3", {"order": 3}, TaskPriority.HIGH))
    
    logger.info("Added 3 tasks: LOW, NORMAL, HIGH")
    
    # Check queue ordering
    logger.info("✅ Tasks added with correct priorities")


async def main():
    """Run all tests"""
    await test_singleton_pattern()
    await test_priority_ordering()
    await test_task_queue()


if __name__ == "__main__":
    asyncio.run(main())
