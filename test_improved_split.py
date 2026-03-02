"""
Test improved X.com character counting and thread splitting
"""
import re

def count_x_characters(text):
    """Count characters using X.com rules"""
    emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF]'
    emojis = len(re.findall(emoji_pattern, text))
    
    url_pattern = r'https?://\S+|www\.\S+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
    urls = re.findall(url_pattern, text)
    url_chars = len(urls) * 23
    
    text_without_urls = re.sub(url_pattern, '', text)
    text_without_emojis = re.sub(emoji_pattern, '', text_without_urls)
    regular_chars = len(text_without_emojis)
    
    return emojis * 2 + url_chars + regular_chars

def split_for_thread(text):
    """Split text like the improved XHive algorithm"""
    chunks = []
    remaining = text
    
    while remaining:
        if count_x_characters(remaining) <= 250:
            chunks.append(remaining)
            break
        
        # Find best split point - start conservative
        split_pos = min(150, len(remaining))  # Very conservative start
        
        # Gradually increase split position until we hit our limit
        while split_pos < len(remaining):
            test_chunk = remaining[:split_pos]
            test_chars = count_x_characters(test_chunk)
            if test_chars > 250:
                split_pos -= 10  # Step back to safe zone
                break
            if test_chars > 220:  # Slow down near limit
                split_pos += 2
            else:
                split_pos += 15  # Bigger steps when safe
        
        # Fine-tune at sentence boundaries
        for end_char in ['. ', '\n\n', '\n', '? ', '! ', ', ']:
            pos = remaining.rfind(end_char, max(50, split_pos - 50), split_pos + 20)
            if pos > 50:
                split_pos = pos + len(end_char)
                break
        
        chunks.append(remaining[:split_pos].strip())
        remaining = remaining[split_pos:].strip()
    
    return chunks

# Test research tweet
research_tweet = """🔬 Yeni araştırmamızda yapay zeka modellerinin finansal piyasalardaki etkilerini inceledik. 

📊 Ana bulgular:
• GPT-4 ve benzeri modeller algoritmik ticaret stratejilerini %23 iyileştiriyor
• Risk analizi süreçleri 3x hızlanıyor  
• Piyasa volatilitesi tahmini %15 daha doğru

🎯 Portföy yönetimi alanında en büyük değişim: manuel analiz döneminin sonu.

#AI #Fintech #Research #TradingBot #PortfolyoYonetimi #YapayZeka""".strip()

print(f"📏 Original: {count_x_characters(research_tweet)} X-characters")
print()

chunks = split_for_thread(research_tweet)
total = len(chunks)

print(f"📝 Split into {total} chunks:")
print("=" * 60)

for i, chunk in enumerate(chunks, 1):
    # Add thread numbering
    if i == 1:
        final_chunk = f"{chunk}\n\n🧵 {i}/{total}"
    else:
        final_chunk = f"🧵 {i}/{total}\n\n{chunk}"
    
    x_chars = count_x_characters(final_chunk)
    status = "✅" if x_chars <= 280 else "❌"
    
    print(f"Thread {i}: {status} {x_chars}/280 X-chars")
    print(f"Content: {final_chunk[:50]}...")
    print("-" * 40)