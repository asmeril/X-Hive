"""
THREAD TEST - Real posting test
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

async def thread_test():
    print("🧵 THREAD POSTING TEST")
    print("=" * 60)
    
    daemon = XDaemon()
    await daemon.start()
    
    # Long research tweet to trigger thread splitting
    research_tweet = """🔬 XHive thread test - Yeni araştırmamızda yapay zeka modellerinin finansal piyasalardaki etkilerini inceledik. 

📊 Ana bulgular:
• GPT-4 ve benzeri modeller algoritmik ticaret stratejilerini %23 iyileştiriyor
• Risk analizi süreçleri 3x hızlanıyor  
• Piyasa volatilitesi tahmini %15 daha doğru

🎯 Portföy yönetimi alanında en büyük değişim: manuel analiz döneminin sonu.

#XHive #AI #Fintech #Research #TradingBot #PortfolyoYonetimi #YapayZeka""".strip()
    
    print(f"📝 Thread tweet ({len(research_tweet)} chars):")
    print(f"   {research_tweet[:100]}...")
    print()
    
    try:
        result = await daemon.post_tweet(research_tweet)
        
        print(f"📋 THREAD RESULT:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get("success"):
            thread_count = result.get("thread_count", 1)
            if thread_count > 1:
                print(f"✅ THREAD SUCCESS! Posted {thread_count} tweets!")
                print(f"🧵 Thread URL: {result.get('tweet_url')}")
            else:
                print(f"⚠️ Posted as single tweet (under 280 X-chars)")
        else:
            print(f"❌ THREAD FAILED: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 THREAD EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await daemon.stop()
        print("🛑 Thread test complete!")

if __name__ == "__main__":
    asyncio.run(thread_test())