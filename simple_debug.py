"""
Simple debug test - single tweet with XiDeAI Pro selectors
"""
import asyncio
import json
import sys
import time
sys.path.append(".")

from apps.worker.x_daemon import XDaemon

async def debug_test():
    print("🔧 SIMPLE DEBUG TEST")
    print("=" * 50)
    
    daemon = XDaemon()
    await daemon.start()
    
    # Very simple test tweet
    test_tweet = "DEBUG test " + str(int(time.time()))
    
    print(f"📝 Simple tweet: {test_tweet}")
    print(f"📏 Length: {len(test_tweet)} chars (under 280, no thread)")
    print()
    
    try:
        result = await daemon.post_tweet(test_tweet)
        
        print(f"📋 RESULT:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get("success"):
            print(f"✅ SINGLE TWEET SUCCESS!")
        else:
            print(f"❌ FAILED: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await daemon.stop()

if __name__ == "__main__":
    asyncio.run(debug_test())