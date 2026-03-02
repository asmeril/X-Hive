"""
Simple thread test - check if thread splitting works
"""
import asyncio
import json
import sys
sys.path.append(".")

# Patch rate limiter
from apps.worker import rate_limiter
def bypass_check_limit(self, operation_type):
    return True, None
rate_limiter.RateLimiter.check_limit = bypass_check_limit

from apps.worker.x_daemon import XDaemon

async def test_thread_logic():
    """Test only the thread splitting logic"""
    daemon = XDaemon()
    
    # Test long research tweet (400+ characters)
    long_text = """🔬 Yeni araştırmamızda yapay zeka modellerinin finansal piyasalardaki etkilerini inceledik. 

📊 Ana bulgular:
• GPT-4 ve benzeri modeller algoritmik ticaret stratejilerini %23 iyileştiriyor
• Risk analizi süreçleri 3x hızlanıyor  
• Piyasa volatilitesi tahmini %15 daha doğru

🎯 Portföy yönetimi alanında en büyük değişim: manuel analiz döneminin sonu.

#AI #Fintech #Research #TradingBot #PortfolyoYonetimi #YapayZeka""".strip()
    
    print(f"📏 Tweet uzunluğu: {len(long_text)} karakter")
    print()
    
    # Test splitting logic manually
    chunks = []
    remaining = long_text
    
    while remaining:
        if len(remaining) <= 275:
            chunks.append(remaining)
            break
        
        # Find best split point (prefer sentence/paragraph end)
        split_pos = 275
        for end_char in ['. ', '\n\n', '\n', '. ', '? ', '! ']:
            pos = remaining.rfind(end_char, 0, 275)
            if pos > 200:  # Minimum chunk size
                split_pos = pos + len(end_char)
                break
        
        chunks.append(remaining[:split_pos].strip())
        remaining = remaining[split_pos:].strip()
    
    # Add thread numbers
    total = len(chunks)
    numbered_chunks = []
    for i, chunk in enumerate(chunks, 1):
        if i == 1:
            numbered_chunks.append(f"{chunk}\n\n🧵 {i}/{total}")
        else:
            numbered_chunks.append(f"🧵 {i}/{total}\n\n{chunk}")
    
    print(f"📝 Thread {total} parçaya bölündü:")
    print("=" * 60)
    
    for i, chunk in enumerate(numbered_chunks, 1):
        print(f"Tweet {i} ({len(chunk)} karakter):")
        print(chunk)
        print("-" * 40)
    
    return numbered_chunks

if __name__ == "__main__":
    asyncio.run(test_thread_logic())