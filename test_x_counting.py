"""
Test X.com character counting
"""
import re

def count_x_characters(text):
    """Count characters using X.com rules"""
    # Count emojis (2 chars each)
    emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF]'
    emojis = len(re.findall(emoji_pattern, text))
    
    # Count URLs (23 chars each)
    url_pattern = r'https?://\S+|www\.\S+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
    urls = re.findall(url_pattern, text)
    url_chars = len(urls) * 23
    
    # Count remaining characters
    text_without_urls = re.sub(url_pattern, '', text)
    text_without_emojis = re.sub(emoji_pattern, '', text_without_urls)
    regular_chars = len(text_without_emojis)
    
    total = emojis * 2 + url_chars + regular_chars
    print(f"  Emojis: {emojis} × 2 = {emojis * 2}")
    print(f"  URLs: {len(urls)} × 23 = {url_chars}")
    print(f"  Regular: {regular_chars}")
    print(f"  Total X-chars: {total}")
    return total

# Test research tweet
research_tweet = """🔬 Yeni araştırmamızda yapay zeka modellerinin finansal piyasalardaki etkilerini inceledik. 

📊 Ana bulgular:
• GPT-4 ve benzeri modeller algoritmik ticaret stratejilerini %23 iyileştiriyor
• Risk analizi süreçleri 3x hızlanıyor  
• Piyasa volatilitesi tahmini %15 daha doğru

🎯 Portföy yönetimi alanında en büyük değişim: manuel analiz döneminin sonu.

#AI #Fintech #Research #TradingBot #PortfolyoYonetimi #YapayZeka""".strip()

print(f"📏 Raw length: {len(research_tweet)} characters")
print("🧮 X.com character counting:")
x_count = count_x_characters(research_tweet)
print()
print(f"{'✅ Safe' if x_count <= 280 else '❌ Too long'} - {x_count}/280 X-characters")

# Test thread chunk with numbering
chunk1 = """🔬 Yeni araştırmamızda yapay zeka modellerinin finansal piyasalardaki etkilerini inceledik. 

📊 Ana bulgular:
• GPT-4 ve benzeri modeller algoritmik ticaret stratejilerini %23 iyileştiriyor
• Risk analizi süreçleri 3x hızlanıyor
• Piyasa volatilitesi tahmini %15 daha doğru

🧵 1/2"""

print("\n" + "="*60)
print("Thread chunk 1:")
print(f"📏 Raw length: {len(chunk1)} characters")
print("🧮 X.com character counting:")
chunk1_count = count_x_characters(chunk1)
print(f"{'✅ Safe' if chunk1_count <= 280 else '❌ Too long'} - {chunk1_count}/280 X-characters")