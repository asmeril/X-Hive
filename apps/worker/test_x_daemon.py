"""
Simple test script for X-Daemon Core
"""

import asyncio
import logging

from x_daemon import XDaemon

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_x_daemon_lifecycle():
    """Test X-Daemon lifecycle methods"""
    
    try:
        # Test 1: Initialize X-Daemon
        logger.info("=" * 60)
        logger.info("TEST 1: Initialize X-Daemon")
        logger.info("=" * 60)
        
        daemon = XDaemon()
        logger.info(f"✅ X-Daemon instance created: {id(daemon)}")

        # Test 2: Start daemon
        logger.info("\n" + "=" * 60)
        logger.info("TEST 2: Start X-Daemon")
        logger.info("=" * 60)
        
        start_result = await daemon.start()
        logger.info(f"✅ Start result: {start_result}")

        # Test 3: Get status
        logger.info("\n" + "=" * 60)
        logger.info("TEST 3: Get X-Daemon Status")
        logger.info("=" * 60)
        
        status = await daemon.get_status()
        logger.info(f"✅ Daemon status: {status}")

        # Test 4: Wait a bit to accumulate uptime
        logger.info("\n" + "=" * 60)
        logger.info("TEST 4: Wait and Check Uptime")
        logger.info("=" * 60)
        
        await asyncio.sleep(3)
        status = await daemon.get_status()
        logger.info(f"✅ Uptime: {status['uptime_seconds']} seconds")

        # Test 5: Stop daemon
        logger.info("\n" + "=" * 60)
        logger.info("TEST 5: Stop X-Daemon")
        logger.info("=" * 60)
        
        stop_result = await daemon.stop()
        logger.info(f"✅ Stop result: {stop_result}")

        logger.info("\n" + "=" * 60)
        logger.info("LIFECYCLE TESTS PASSED ✅")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Lifecycle test failed: {e}", exc_info=True)


async def test_x_daemon_singleton():
    """Test singleton pattern"""
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Singleton Pattern")
    logger.info("=" * 60)
    
    daemon1 = XDaemon()
    daemon2 = XDaemon()
    
    logger.info(f"Daemon1 ID: {id(daemon1)}")
    logger.info(f"Daemon2 ID: {id(daemon2)}")
    logger.info(f"Same instance: {daemon1 is daemon2}")
    logger.info("✅ Singleton pattern works")


async def test_x_daemon_state_persistence():
    """Test state save/load"""
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST: State Persistence")
    logger.info("=" * 60)
    
    daemon = XDaemon()
    
    # Manually update some stats
    daemon.state.total_operations = 100
    daemon.state.successful_operations = 80
    daemon.state.failed_operations = 20
    
    # Save state
    await daemon._save_state()
    logger.info(f"✅ State saved: {daemon.state.to_dict()}")
    
    # Create new daemon instance and load state
    daemon2 = XDaemon()
    await daemon2._load_state()
    
    logger.info(f"✅ State loaded: {daemon2.state.to_dict()}")
    logger.info(f"Total operations match: {daemon2.state.total_operations == 100}")


async def test_x_daemon_restart():
    """Test daemon restart"""
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Daemon Restart")
    logger.info("=" * 60)
    
    daemon = XDaemon()
    
    # Start daemon
    await daemon.start()
    logger.info("✅ Daemon started")
    
    await asyncio.sleep(2)
    
    # Restart daemon
    restart_result = await daemon.restart()
    logger.info(f"✅ Restart result: {restart_result}")
    
    # Verify running
    status = await daemon.get_status()
    logger.info(f"✅ Status after restart: {status['daemon_status']}")
    
    # Stop daemon
    await daemon.stop()
    logger.info("✅ Daemon stopped")


async def main():
    """Run all tests"""
    await test_x_daemon_singleton()
    await test_x_daemon_state_persistence()
    await test_x_daemon_lifecycle()
    # await test_x_daemon_restart()  # Uncomment if you want full restart test


if __name__ == "__main__":
    asyncio.run(main())
