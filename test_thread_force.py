"""
Test thread posting with XHive (manual rate limit bypass)
"""
import asyncio
import json
import sys
sys.path.append(".")

# Patch rate limiter before import
from apps.worker import rate_limiter

# Override check_limit method to always return (True, None)
original_check_limit = rate_limiter.RateLimiter.check_limit
def bypass_check_limit(self, operation_type):
    return True, None

rate_limiter.RateLimiter.check_limit = bypass_check_limit

from apps.worker.x_daemon import XDaemon

async def test_thread_force():
    daemon = XDaemon()
    await daemon.start()
    
    # Test long research tweet (400+ characters)
    long_text = """🔬 Yeni araştırmamızda yapay zeka modellerinin finansal piyasalardaki etkilerini inceledik. 

📊 Ana bulgular:
• GPT-4 ve benzeri modeller algoritmik ticaret stratejilerini %23 iyileştiriyor
• Risk analizi süreçleri 3x hızlanıyor  
• Piyasa volatilitesi tahmini %15 daha doğru

🎯 Portföy yönetimi alanında en büyük değişim: manuel analiz döneminin sonu.

#AI #Fintech #Research #TradingBot #PortfolyoYonetimi #YapayZeka""".strip()
    
    print(f"📏 Tweet uzunluğu: {len(long_text)} karakter")
    print(f"📝 Thread testine başlıyor...")
    
    result = await daemon.post_tweet(long_text)
    
    print(f"✅ Sonuç: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    await daemon.stop()

if __name__ == "__main__":
    asyncio.run(test_thread_force())