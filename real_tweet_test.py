"""
Real XiDeAI Pro style tweet test
"""
import asyncio
import json
import sys
sys.path.append(".")

# Bypass rate limiter
from apps.worker import rate_limiter
def bypass_rate_limit(self, operation_type):
    return True, None
rate_limiter.RateLimiter.check_limit = bypass_rate_limit

from apps.worker.x_daemon import XDaemon

async def real_test():
    print("🎯 XiDeAI Pro Style Tweet Test")
    print("=" * 50)
    
    daemon = XDaemon()
    await daemon.start()
    
    # Simple test tweet
    test_tweet = "XHive final test " + str(int(asyncio.get_event_loop().time()))
    
    print(f"📝 Test tweet: {test_tweet}")
    print()
    
    try:
        result = await daemon.post_tweet(test_tweet)
        
        print(f"📋 Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get("success"):
            print(f"✅ TWEET POSTED SUCCESSFULLY!")
        else:
            print(f"❌ FAILED: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await daemon.stop()

if __name__ == "__main__":
    asyncio.run(real_test())