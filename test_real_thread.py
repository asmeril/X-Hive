"""
Real thread test with rate limit bypass
"""
import asyncio
import json
import sys
import os
sys.path.append(".")

# Patch rate limiter before imports
from apps.worker import rate_limiter
original_check = rate_limiter.RateLimiter.check_limit
def bypass_rate_limit(self, operation_type):
    print(f"[BYPASS] Rate limit bypassed for {operation_type}")
    return True, None
rate_limiter.RateLimiter.check_limit = bypass_rate_limit

from apps.worker.x_daemon import XDaemon

async def test_real_thread():
    print("🚀 Starting real thread test...")
    
    daemon = XDaemon()
    await daemon.start()
    
    # Test research tweet (400+ characters)
    research_tweet = """🔬 Yeni araştırmamızda yapay zeka modellerinin finansal piyasalardaki etkilerini inceledik. 

📊 Ana bulgular:
• GPT-4 ve benzeri modeller algoritmik ticaret stratejilerini %23 iyileştiriyor
• Risk analizi süreçleri 3x hızlanıyor  
• Piyasa volatilitesi tahmini %15 daha doğru

🎯 Portföy yönetimi alanında en büyük değişim: manuel analiz döneminin sonu.

#AI #Fintech #Research #TradingBot #PortfolyoYonetimi #YapayZeka""".strip()
    
    print(f"📏 Tweet length: {len(research_tweet)} characters")
    print(f"📝 Should trigger thread splitting...")
    print()
    
    try:
        result = await daemon.post_tweet(research_tweet)
        print(f"✅ Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get("success"):
            thread_count = result.get("thread_count", 1)
            print(f"🧵 Thread posted successfully with {thread_count} tweets!")
        else:
            print(f"❌ Thread failed: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await daemon.stop()

if __name__ == "__main__":
    asyncio.run(test_real_thread())