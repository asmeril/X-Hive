"""
Quick thread test - basic text splitting like XiDeAI Pro
"""
def split_text_simple(text, max_length=275):
    """Simple text splitting like XiDeAI Pro ThreadService.SplitText"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    remaining = text
    
    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break
        
        # Find best split point (prefer sentence/paragraph end)
        split_pos = max_length
        for end_char in ['. ', '\n\n', '\n', '? ', '! ', ', ']:
            pos = remaining.rfind(end_char, 0, max_length)
            if pos > 200:  # Minimum chunk size
                split_pos = pos + len(end_char)
                break
        
        chunks.append(remaining[:split_pos].strip())
        remaining = remaining[split_pos:].strip()
    
    return chunks

# Test long research tweet
long_text = """🔬 Yeni araştırmamızda yapay zeka modellerinin finansal piyasalardaki etkilerini inceledik. 

📊 Ana bulgular:
• GPT-4 ve benzeri modeller algoritmik ticaret stratejilerini %23 iyileştiriyor
• Risk analizi süreçleri 3x hızlanıyor  
• Piyasa volatilitesi tahmini %15 daha doğru

🎯 Portföy yönetimi alanında en büyük değişim: manuel analiz döneminin sonu.

#AI #Fintech #Research #TradingBot #PortfolyoYonetimi #YapayZeka""".strip()

print(f"📏 Orijinal uzunluk: {len(long_text)} karakter")
print()

chunks = split_text_simple(long_text, 275)
total = len(chunks)

print(f"📝 {total} parçaya bölündü:")
print("=" * 60)

for i, chunk in enumerate(chunks, 1):
    # Add thread numbering like XHive
    if i == 1:
        final_chunk = f"{chunk}\n\n🧵 {i}/{total}"
    else:
        final_chunk = f"🧵 {i}/{total}\n\n{chunk}"
    
    print(f"Tweet {i} ({len(final_chunk)} karakter):")
    print(final_chunk)
    print("-" * 40)