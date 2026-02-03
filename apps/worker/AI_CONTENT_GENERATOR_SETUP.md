# AI Content Generator Setup Guide

## Overview
AI-powered content generator for X-Hive using Google Gemini 1.5 Flash model. Generates engaging Turkish X/Twitter posts with various styles.

## Files Created

### 1. ✅ `config.py` (Updated)
- Added `GEMINI_API_KEY` to Settings class
- Added export variable
- Added validation warning

### 2. ✅ `ai_content_generator.py` (New)
**Class: AIContentGenerator**

Methods:
- `__init__()` - Initialize Gemini API
- `async generate_post(topic, style, max_length)` - Generate single post
- `async generate_daily_posts(count, topics)` - Generate multiple posts
- `async generate_reply(original_tweet, tone)` - Generate contextual reply
- `_get_style_description(style)` - Convert style codes to Turkish

Features:
- ✅ Async/await throughout
- ✅ Turkish prompts for better quality
- ✅ Type hints everywhere
- ✅ Comprehensive emoji logging
- ✅ Error handling with fallbacks
- ✅ Auto-truncation to 280 chars

### 3. ✅ `test_ai_content.py` (New)
Test functions:
- `test_single_post()` - Test 3 different styles
- `test_daily_posts()` - Test batch generation
- `test_reply_generation()` - Test reply creation

### 4. ✅ `requirements.txt` (Updated)
Added: `google-generativeai`

## Setup Instructions

### Step 1: Install Dependencies
```bash
pip install google-generativeai
# Or install all requirements
pip install -r requirements.txt
```

### Step 2: Get Gemini API Key
1. Go to: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy your API key

### Step 3: Configure .env
Add to your `.env` file:
```env
GEMINI_API_KEY=your_api_key_here
```

### Step 4: Test the Generator
```bash
python test_ai_content.py
```

## Usage Examples

### Basic Post Generation
```python
from ai_content_generator import AIContentGenerator

generator = AIContentGenerator()

# Generate single post
post = await generator.generate_post(
    topic="Yapay zeka ve otomasyon",
    style="professional",
    max_length=280
)
print(post)
```

### Daily Posts
```python
# Generate 3 posts for daily schedule
posts = await generator.generate_daily_posts(
    count=3,
    topics=["AI trends", "Productivity tips", "Tech innovation"]
)

for i, post in enumerate(posts, 1):
    print(f"Post {i}: {post}")
```

### Reply Generation
```python
# Generate contextual reply
reply = await generator.generate_reply(
    original_tweet="Yapay zeka iş dünyasını nasıl değiştiriyor?",
    tone="friendly"
)
print(reply)
```

## Styles Available

| Style | Turkish Description | Use Case |
|-------|---------------------|----------|
| `professional` | Profesyonel ve bilgilendirici | Business updates, tech news |
| `casual` | Samimi ve rahat | Community engagement |
| `humorous` | Eğlenceli ve mizahi | Light content, jokes |
| `inspirational` | İlham verici ve motive edici | Motivational quotes |

## Reply Tones

| Tone | Turkish Description | Use Case |
|------|---------------------|----------|
| `friendly` | Samimi ve yardımsever | General engagement |
| `informative` | Bilgilendirici ve profesyonel | Educational responses |
| `witty` | Eğlenceli ve zekice | Clever comebacks |

## Integration with PostScheduler

```python
from post_scheduler import PostScheduler
from ai_content_generator import AIContentGenerator

# Custom content generator for scheduler
ai_gen = AIContentGenerator()

async def ai_content_func(time_period: str) -> str:
    """Generate AI content based on time of day"""
    topics = {
        "morning": "Günün başlangıcı ve motivasyon",
        "afternoon": "Verimlilik ve iş hayatı",
        "evening": "Günün özeti ve düşünceler"
    }
    
    topic = topics.get(time_period, "Teknoloji ve inovasyon")
    return await ai_gen.generate_post(topic=topic, style="professional")

# Use with PostScheduler
scheduler = PostScheduler(
    content_generator_func=ai_content_func
)
await scheduler.start()
```

## Configuration

### Generation Settings
In `ai_content_generator.py`:
```python
self.generation_config = {
    'temperature': 0.9,      # Creativity (0.0-1.0)
    'max_output_tokens': 300 # Maximum response length
}
```

Adjust `temperature`:
- Lower (0.3-0.5): More consistent, predictable
- Higher (0.8-1.0): More creative, varied

### Default Topics
```python
topics = [
    "Yapay zeka ve otomasyon",
    "Verimlilik ipuçları",
    "Teknoloji inovasyonu"
]
```

## Error Handling

All methods include fallback content:
```python
# If generation fails, returns:
"🤖 {topic or 'Günün özeti'}\n\n#Otomasyon #XHive"
```

Errors are logged with full traceback:
```
❌ Generation failed: [error details]
```

## Testing Output Example

```
╔============================================================╗
║                                                            ║
║      AI Content Generator Tests (Gemini)                  ║
║                                                            ║
╚============================================================╝

============================================================
TEST 1: Single Post Generation
============================================================

🎨 Generating professional post...

📝 PROFESSIONAL POST (245 chars):
🤖 Yapay zeka günlük hayatımızı nasıl etkiliyor? 
Akıllı asistanlardan otomatik önerilere, her alanda 
AI teknolojisi hayatımızı kolaylaştırıyor! 

#YapayZeka #Teknoloji

✅ Test 1 completed
```

## API Limits

**Gemini 1.5 Flash Free Tier:**
- 15 requests per minute
- 1,500 requests per day
- Rate limiting handled automatically

**Monitor usage at:**
https://aistudio.google.com/app/apikey

## Troubleshooting

### "GEMINI_API_KEY not set"
- Add `GEMINI_API_KEY=your_key` to `.env` file
- Restart application

### "Rate limit exceeded"
- Wait 1 minute between batches
- Upgrade to paid tier if needed

### "Import error: google.generativeai"
```bash
pip install google-generativeai
```

### Turkish characters not displaying
- Ensure UTF-8 encoding in terminal
- Use `chcp 65001` on Windows PowerShell

## Best Practices

1. **Use Turkish Prompts**: Better quality for Turkish content
2. **Batch Generation**: Use `generate_daily_posts()` for efficiency
3. **Error Handling**: Always have fallback content
4. **Rate Limiting**: Don't exceed 15 requests/minute
5. **Content Review**: Always review AI-generated content before posting

## Next Steps

1. ✅ Test with `python test_ai_content.py`
2. ✅ Verify Gemini API key works
3. ✅ Integrate with PostScheduler
4. ✅ Review and approve generated content
5. ✅ Monitor API usage

## Documentation

- **Gemini API Docs**: https://ai.google.dev/docs
- **Python SDK**: https://ai.google.dev/tutorials/python_quickstart
- **Model Info**: https://ai.google.dev/models/gemini

---

**Status**: ✅ All files created and ready to use!
**Model**: Gemini 1.5 Flash
**Language**: Turkish optimized
**Integration**: Ready for PostScheduler
