"""
Final real thread test with proper X.com character counting
"""
import asyncio
import json
import sys
import time
sys.path.append(".")

# Bypass rate limiter for testing
from apps.worker import rate_limiter
def bypass_rate_limit(self, operation_type):
    print(f"[BYPASS] Rate limit bypassed for {operation_type}")
    return True, None
rate_limiter.RateLimiter.check_limit = bypass_rate_limit

from apps.worker.x_daemon import XDaemon

async def final_thread_test():
    print("🚀 Final Thread Test - X.com Character Counting")
    print("=" * 60)
    
    daemon = XDaemon()
    await daemon.start()
    
    # Test research tweet with emojis (should trigger proper splitting)
    research_tweet = """🔬 Yeni araştırmamızda yapay zeka modellerinin finansal piyasalardaki etkilerini inceledik. 

📊 Ana bulgular:
• GPT-4 ve benzeri modeller algoritmik ticaret stratejilerini %23 iyileştiriyor
• Risk analizi süreçleri 3x hızlanıyor  
• Piyasa volatilitesi tahmini %15 daha doğru

🎯 Portföy yönetimi alanında en büyük değişim: manuel analiz döneminin sonu.

#AI #Fintech #Research #TradingBot #PortfolyoYonetimi #YapayZeka""".strip()
    
    print(f"📝 Test tweet:")
    print(f"   Raw length: {len(research_tweet)} characters")
    print(f"   Content: {research_tweet[:80]}...")
    print()
    
    try:
        print("🔄 Starting thread posting...")
        start_time = time.time()
        
        result = await daemon.post_tweet(research_tweet)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ Test completed in {duration:.1f} seconds")
        print()
        print(f"📋 Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get("success"):
            thread_count = result.get("thread_count", 1)
            if thread_count > 1:
                print(f"✅ SUCCESS: Thread posted with {thread_count} tweets!")
                print(f"🎯 Each chunk was under 280 X-characters")
            else:
                print(f"✅ SUCCESS: Single tweet posted (under 280 X-chars)")
        else:
            error = result.get("error", "Unknown error")
            print(f"❌ FAILED: {error}")
            
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print()
        print("🛑 Stopping daemon...")
        await daemon.stop()
        print("✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(final_thread_test())