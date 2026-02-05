"""
Infrastructure Test Suite for X-HIVE

Tests critical fixes:
1. Gemini API with new google.genai package (no FutureWarning)
2. ChromePool auto-initialization in TaskQueue
3. Path warnings in x_daemon.py

Run with: python.exe test_infrastructure.py
"""

import asyncio
import logging
import sys
import warnings
import os
from datetime import datetime

# Windows fix for Playwright subprocess on Python 3.12+ (must be FIRST)
if sys.platform == "win32" and sys.version_info >= (3, 12):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test results tracking
test_results = {
    "test_gemini_api": {"status": "PENDING", "error": None},
    "test_chrome_pool_auto_start": {"status": "PENDING", "error": None},
    "test_path_warnings": {"status": "PENDING", "error": None},
}


async def test_gemini_api() -> bool:
    """
    Test 1: Gemini API Integration
    
    Validates:
    - AIContentGenerator imports without FutureWarning
    - google.genai package is used (not deprecated google.generativeai)
    - Can generate a post successfully
    - Response is valid and non-empty
    """
    logger.info("\n" + "=" * 80)
    logger.info("[TEST 1] Gemini API with google.genai Package")
    logger.info("=" * 80)
    
    try:
        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Import AIContentGenerator
            logger.info("Importing AIContentGenerator...")
            from ai_content_generator import AIContentGenerator
            logger.info("✅ AIContentGenerator imported successfully")
            
            # Check for FutureWarning
            future_warnings = [warning for warning in w if issubclass(warning.category, FutureWarning)]
            if future_warnings:
                logger.error(f"❌ FutureWarning detected: {future_warnings[0].message}")
                test_results["test_gemini_api"]["status"] = "FAILED"
                test_results["test_gemini_api"]["error"] = f"FutureWarning: {future_warnings[0].message}"
                return False
            
            logger.info("✅ No FutureWarning detected (using new google.genai)")
        
        # Initialize generator
        logger.info("Initializing AIContentGenerator...")
        generator = AIContentGenerator()
        logger.info("✅ Generator initialized")
        
        # Generate a test post
        logger.info("Generating test post...")
        post = await generator.generate_post(
            topic="X-HIVE Infrastructure Test",
            style="professional",
            max_length=280
        )
        
        if not post:
            logger.error("❌ Empty post response")
            test_results["test_gemini_api"]["status"] = "FAILED"
            test_results["test_gemini_api"]["error"] = "Empty post response"
            return False
        
        logger.info(f"✅ Post generated successfully ({len(post)} chars)")
        logger.info(f"   Post preview: {post[:100]}...")
        
        test_results["test_gemini_api"]["status"] = "PASSED"
        logger.info("✅ TEST 1 PASSED: Gemini API working correctly")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        test_results["test_gemini_api"]["status"] = "FAILED"
        test_results["test_gemini_api"]["error"] = f"ImportError: {e}"
        return False
        
    except Exception as e:
        logger.error(f"❌ Test error: {e}", exc_info=True)
        test_results["test_gemini_api"]["status"] = "FAILED"
        test_results["test_gemini_api"]["error"] = f"Exception: {e}"
        return False


async def test_chrome_pool_auto_start() -> bool:
    """
    Test 2: ChromePool Auto-Initialization
    
    Validates:
    - TaskQueue can be imported
    - TaskQueue.start() initializes ChromePool
    - ChromePool._initialized becomes True
    - TaskQueue can be stopped gracefully
    
    Note: May timeout on actual browser launch, but we check initialization flag
    """
    logger.info("\n" + "=" * 80)
    logger.info("[TEST 2] ChromePool Auto-Initialization in TaskQueue")
    logger.info("=" * 80)
    
    try:
        # Import TaskQueue
        logger.info("Importing TaskQueue...")
        from task_queue import TaskQueue
        logger.info("✅ TaskQueue imported successfully")
        
        # Get TaskQueue singleton
        logger.info("Creating TaskQueue instance...")
        task_queue = TaskQueue()
        logger.info("✅ TaskQueue instance created")
        
        # Check ChromePool before start
        logger.info(f"ChromePool._initialized before start: {task_queue.chrome_pool._initialized}")
        
        # Start TaskQueue with timeout (it will try to launch browser)
        logger.info("Starting TaskQueue (this will attempt to initialize ChromePool)...")
        
        try:
            # Use asyncio.wait_for with short timeout to avoid hanging
            await asyncio.wait_for(task_queue.start(), timeout=5)
        except asyncio.TimeoutError:
            # Start may timeout on browser launch, but that's OK - check if init was attempted
            logger.warning("⚠️  TaskQueue.start() timeout (expected for browser launch)")
        except Exception as e:
            # Some errors are expected (browser issues), but initialization should have been attempted
            logger.warning(f"⚠️  TaskQueue.start() error (expected): {e}")
        
        # Check ChromePool initialization flag
        if task_queue.chrome_pool._initialized:
            logger.info("✅ ChromePool._initialized is True")
            logger.info("✅ ChromePool was auto-initialized by TaskQueue")
            test_results["test_chrome_pool_auto_start"]["status"] = "PASSED"
            
            # Try to stop gracefully
            try:
                await task_queue.stop()
                logger.info("✅ TaskQueue stopped gracefully")
            except Exception as e:
                logger.warning(f"⚠️  TaskQueue.stop() warning: {e}")
            
            logger.info("✅ TEST 2 PASSED: ChromePool auto-initialization working")
            return True
        else:
            logger.error("❌ ChromePool._initialized is still False")
            logger.error("❌ ChromePool was NOT initialized by TaskQueue")
            test_results["test_chrome_pool_auto_start"]["status"] = "FAILED"
            test_results["test_chrome_pool_auto_start"]["error"] = "ChromePool not initialized"
            return False
            
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        test_results["test_chrome_pool_auto_start"]["status"] = "FAILED"
        test_results["test_chrome_pool_auto_start"]["error"] = f"ImportError: {e}"
        return False
        
    except Exception as e:
        logger.error(f"❌ Test error: {e}", exc_info=True)
        test_results["test_chrome_pool_auto_start"]["status"] = "FAILED"
        test_results["test_chrome_pool_auto_start"]["error"] = f"Exception: {e}"
        return False


def test_path_warnings() -> bool:
    """
    Test 3: Path Warnings in x_daemon.py
    
    Validates:
    - x_daemon.py imports without SyntaxWarning for paths
    - No raw string (r"...") issues
    - All Windows paths are properly handled
    
    Note: This is a synchronous test
    """
    logger.info("\n" + "=" * 80)
    logger.info("[TEST 3] Path Warnings in x_daemon.py")
    logger.info("=" * 80)
    
    try:
        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Import x_daemon
            logger.info("Importing x_daemon...")
            import x_daemon
            logger.info("✅ x_daemon imported successfully")
            
            # Check for SyntaxWarning related to invalid escape sequences
            syntax_warnings = [
                warning for warning in w 
                if issubclass(warning.category, (SyntaxWarning, DeprecationWarning))
                and ('escape' in str(warning.message).lower() or 'path' in str(warning.message).lower())
            ]
            
            if syntax_warnings:
                logger.error(f"❌ Path-related warnings detected:")
                for warning in syntax_warnings:
                    logger.error(f"   - {warning.category.__name__}: {warning.message}")
                test_results["test_path_warnings"]["status"] = "FAILED"
                test_results["test_path_warnings"]["error"] = f"Found {len(syntax_warnings)} warnings"
                return False
            
            logger.info("✅ No SyntaxWarning or DeprecationWarning detected")
        
        # Additional validation: check if module has expected attributes
        if hasattr(x_daemon, 'XDaemon'):
            logger.info("✅ x_daemon.XDaemon class present")
        else:
            logger.error("❌ x_daemon.XDaemon class not found")
            return False
        
        test_results["test_path_warnings"]["status"] = "PASSED"
        logger.info("✅ TEST 3 PASSED: No path warnings detected")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        test_results["test_path_warnings"]["status"] = "FAILED"
        test_results["test_path_warnings"]["error"] = f"ImportError: {e}"
        return False
        
    except Exception as e:
        logger.error(f"❌ Test error: {e}", exc_info=True)
        test_results["test_path_warnings"]["status"] = "FAILED"
        test_results["test_path_warnings"]["error"] = f"Exception: {e}"
        return False


async def run_all_tests():
    """Run all infrastructure tests"""
    logger.info("\n")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 20 + "X-HIVE INFRASTRUCTURE TEST SUITE" + " " * 25 + "║")
    logger.info("║" + " " * 25 + f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + " " * 26 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    
    # Run async tests
    logger.info("\n🚀 Running async tests...")
    result1 = await test_gemini_api()
    result2 = await test_chrome_pool_auto_start()
    
    # Run sync test
    logger.info("\n🚀 Running sync tests...")
    result3 = test_path_warnings()
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 80)
    
    for test_name, result in test_results.items():
        status = result["status"]
        status_symbol = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "⏳"
        logger.info(f"{status_symbol} {test_name}: {status}")
        if result["error"]:
            logger.info(f"   Error: {result['error']}")
    
    # Overall result
    passed = sum(1 for r in test_results.values() if r["status"] == "PASSED")
    total = len(test_results)
    
    logger.info("\n" + "=" * 80)
    logger.info(f"OVERALL: {passed}/{total} tests passed")
    logger.info("=" * 80)
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED! Infrastructure is ready for production.")
        return True
    else:
        logger.error(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
        return False


def main():
    """Main entry point"""
    try:
        # Run async tests
        success = asyncio.run(run_all_tests())
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Tests interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
