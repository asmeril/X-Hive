"""
AI Content Generator for X-Hive
Generate engaging X/Twitter posts using Google Gemini API.

Features:
- Post generation with various styles
- Batch post generation
- Contextual reply generation
- Turkish language support for better quality
- Comprehensive error handling and logging
"""

import asyncio
import logging
import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class AIContentGenerator:
    """
    Generate AI-powered content for X/Twitter posts using Google Gemini.
    
    All operations are async and support Turkish prompts for better content quality.
    """
    
    def __init__(self):
        """
        Initialize AI Content Generator with Gemini API.
        
        Raises:
            ValueError: If GEMINI_API_KEY is not set in config
        """
        if not GEMINI_API_KEY:
            raise ValueError("[ERROR] GEMINI_API_KEY not configured in .env")
        
        # Configure Gemini API client
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Model name for generation
        self.model = 'models/gemini-flash-latest'
        
        # Safety settings - more permissive for harmless content
        self.safety_settings = [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
        ]
        
        logger.info("[OK] AIContentGenerator initialized (Gemini Flash Latest)")
        
        # Default topics for daily post generation
        self.default_topics = [
            "Yapay zeka ve otomasyon",
            "Verimlilik ipuçları",
            "Teknoloji inovasyonu"
        ]
    
    async def _generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        initial_delay: float = 1.0
    ) -> str:
        """
        Generate content with exponential backoff retry logic.
        
        Handles:
        - Rate limit errors (429, quota exceeded)
        - Safety filter rejections
        - Transient network errors
        
        Args:
            prompt: The prompt to send to Gemini
            max_retries: Maximum retry attempts (default: 3)
            initial_delay: Initial delay in seconds (default: 1.0)
        
        Returns:
            Generated text
        
        Raises:
            Exception: If all retries fail
        """
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"[RETRY] Attempt {attempt + 1}/{max_retries}")
                
                # Call Gemini API
                response = await asyncio.to_thread(
                    lambda: self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.9,
                            max_output_tokens=2000,
                            top_p=0.95,
                            top_k=40,
                            safety_settings=self.safety_settings
                        )
                    )
                )
                
                # Extract text from response
                text = response.text.strip()
                logger.info(f"✅ Generated content on attempt {attempt + 1}")
                return text
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a rate limit error (429)
                if "429" in error_msg or "quota" in error_msg.lower() or "RESOURCE_EXHAUSTED" in error_msg:
                    # Gemini rate limit: minimum 15s bekleme gerekli
                    retry_delay = max(15.0, initial_delay * (2 ** attempt))
                    logger.warning(f"⏳ Rate limit hit (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay:.1f}s...")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                    
                # Check if it's a safety filter (finish_reason issue)
                elif "finish_reason" in error_msg or "Invalid operation" in error_msg:
                    logger.warning(f"⚠️ Content filtered by safety filter (attempt {attempt + 1}/{max_retries})")
                    # Try again with slight delay
                    if attempt < max_retries - 1:
                        await asyncio.sleep(initial_delay * (attempt + 1))
                    
                else:
                    # Other errors - log and retry with exponential backoff
                    logger.error(f"❌ Generation error (attempt {attempt + 1}/{max_retries}): {error_msg}")
                    if attempt < max_retries - 1:
                        retry_delay = initial_delay * (2 ** attempt)
                        await asyncio.sleep(retry_delay)
        
        # All retries failed - raise exception
        raise Exception(f"Failed to generate content after {max_retries} attempts")
    
    def _get_style_description(self, style: str) -> str:
        """
        Convert style name to Turkish description for prompt.
        
        Args:
            style: Style name (professional, casual, humorous, inspirational)
        
        Returns:
            Turkish description for the style
        """
        styles = {
            "professional": "profesyonel ve bilgilendirici",
            "casual": "samimi ve rahat",
            "humorous": "eğlenceli ve mizahi",
            "inspirational": "ilham verici ve motive edici",
            "technical": "teknik ve ayrıntılı",
            "creative": "yaratıcı ve orijinal",
        }
        
        return styles.get(style.lower(), "profesyonel ve bilgilendirici")
    
    async def generate_post(
        self,
        topic: Optional[str] = None,
        style: str = "professional",
        max_length: int = 280
    ) -> str:
        """
        Generate a single X/Twitter post with retry logic.
        
        Automatically retries with exponential backoff on:
        - Rate limit errors (429)
        - Safety filter rejections
        - Transient network errors
        
        Args:
            topic: Post topic (if None, uses generic tech topic)
            style: Writing style (professional, casual, humorous, inspirational)
            max_length: Maximum post length in characters
        
        Returns:
            Generated post text (or fallback if all retries fail)
        """
        try:
            if topic is None:
                topic = "Yapay zeka ve teknoloji"
            
            style_desc = self._get_style_description(style)
            
            prompt = f"""
Aşağıdaki konu hakkında X/Twitter için kısa, ilgi çekici bir post yaz:

Konu: {topic}
Stil: {style_desc}
Karakter limiti: {max_length} karakter

Gereklemeler:
- Kısa ve öz ol (mümkünse {max_length - 50} karakterin altında)
- Uygun emojiler ekle
- En fazla 2 hashtag kullan
- Okunması kolay olsun
- Endüstri standartlarına uy

Sadece post'u yaz, ek açıklama yapma.
"""
            
            logger.debug(f"[INFO] Generating post for topic: {topic} (style: {style})")
            
            # Use retry logic
            post_text = await self._generate_with_retry(prompt, max_retries=3, initial_delay=1.0)
            
            # Truncate if exceeds max_length
            if len(post_text) > max_length:
                logger.warning(f"[WARNING] Post exceeds {max_length} chars, truncating...")
                post_text = post_text[:max_length - 3] + "..."
            
            logger.info(f"✅ Post generated | Style: {style} | Length: {len(post_text)} chars")
            return post_text
            
        except Exception as e:
            logger.error(f"❌ Post generation failed after retries: {e}")
            
            # Return fallback post
            fallback = f"🤖 {topic or 'AI Update'}\n\n#XHive #AI"
            logger.warning(f"[WARNING] Using fallback post")
            return fallback
    
    async def generate_daily_posts(
        self,
        count: int = 3,
        topics: Optional[List[str]] = None
    ) -> List[str]:
        """
        Generate multiple posts for daily use.
        
        Uses parallel generation with asyncio.gather() for efficiency.
        
        Args:
            count: Number of posts to generate
            topics: List of topics (uses defaults if None)
        
        Returns:
            List of generated posts
        """
        if topics is None:
            topics = self.default_topics
        
        logger.info(f"[INFO] Generating {count} daily posts...")
        
        # Create tasks for parallel generation
        tasks = []
        styles = ["professional", "casual", "inspirational", "creative", "technical"]
        
        for i in range(count):
            topic = topics[i % len(topics)]
            style = styles[i % len(styles)]
            
            task = self.generate_post(
                topic=topic,
                style=style,
                max_length=280
            )
            tasks.append(task)
        
        # Run all generations in parallel
        try:
            posts = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out errors
            valid_posts = [p for p in posts if isinstance(p, str)]
            
            logger.info(f"[OK] Generated {len(valid_posts)}/{count} posts")
            return valid_posts
            
        except Exception as e:
            logger.error(f"[ERROR] Batch generation failed: {e}")
            return []
    
    async def generate_reply(
        self,
        original_tweet: str,
        tone: str = "friendly"
    ) -> str:
        """
        Generate a contextual reply to a tweet with retry logic.
        
        Automatically retries with exponential backoff on:
        - Rate limit errors (429)
        - Safety filter rejections
        - Transient network errors
        
        Args:
            original_tweet: The original tweet text to reply to
            tone: Reply tone (friendly, informative, witty, supportive)
        
        Returns:
            Generated reply text (or fallback if all retries fail)
        """
        try:
            tone_descriptions = {
                "friendly": "arkadaşça ve samimi",
                "informative": "bilgilendirici ve yararlı",
                "witty": "zekice ve eğlenceli",
                "supportive": "destekleyici ve yapıcı",
            }
            
            tone_desc = tone_descriptions.get(tone.lower(), "arkadaşça")
            
            prompt = f"""
Aşağıdaki X/Twitter post'una {tone_desc} bir cevap yaz:

Orijinal post: "{original_tweet}"

Gereklemeler:
- Kısa ve öz ol (140 karakter altında)
- Konuyla alakalı ol
- Uygun emojiler ekle
- Doğal ve samimi olsun
- Post'a değer kat

Sadece cevabı yaz, ek açıklama yapma.
"""
            
            logger.debug(f"[INFO] Generating {tone} reply...")
            
            # Use retry logic
            reply_text = await self._generate_with_retry(prompt, max_retries=3, initial_delay=1.0)
            
            # Truncate if exceeds 280
            if len(reply_text) > 280:
                reply_text = reply_text[:277] + "..."
            
            logger.info(f"✅ Reply generated | Tone: {tone} | Length: {len(reply_text)} chars")
            return reply_text
            
        except Exception as e:
            logger.error(f"❌ Reply generation failed after retries: {e}")
            
            # Fallback reply
            fallback = f"💬 Great point! {original_tweet[:40]}..."
            logger.warning(f"[WARNING] Using fallback reply")
            return fallback
        
    def _extract_content_fields(self, content_item) -> dict:
        """Extract fields from ContentItem dataclass or dict."""
        if hasattr(content_item, 'title'):
            return {
                "title": content_item.title or "",
                "url": content_item.url or "",
                "source": content_item.source_name or "Kaynak",
                "summary": content_item.ai_summary or content_item.description or "",
                "category": getattr(content_item, 'category', '') or "",
            }
        return {
            "title": content_item.get("title", ""),
            "url": content_item.get("url", ""),
            "source": content_item.get("source_name", content_item.get("source", "Kaynak")),
            "summary": content_item.get("ai_summary", content_item.get("summary", content_item.get("description", ""))),
            "category": content_item.get("category", ""),
        }

    async def generate_tweet_from_content(self, content_item) -> str:
        """
        Generate a tweet specifically based on collected intel content.
        Accepts both ContentItem dataclass and plain dict.
        """
        f = self._extract_content_fields(content_item)
        topic = f["title"]
        if f["summary"]:
            topic += f" - {f['summary'][:200]}"
            
        styled_prompt = f"""
Sen viral X/Twitter içerik yazarısın. Şu haber hakkında scroll durduracak bir Türkçe tweet yaz:

Kaynak: {f['source']}
Başlık: {f['title']}
Detay: {topic}
Link: {f['url']}

Viral tweet kuralları:
- MERAK UYANDIRAN bir açılış yaz ("Bunu biliyor muydunuz?", "X sessizce Y yaptı...", "Herkes X sanıyor ama...")
- Güçlü bir görüş/iddia belirt, tarafsız haber dili KULLANMA
- Konuşma dili kullan, resmi gazete dili değil
- 250 karakteri geçmesin
- Max 2 hashtag
- 1-2 emoji (abartma)
- Linki tweetin sonuna koy
- Sadece tweet metnini döndür, açıklama yapma
"""
        
        try:
            return await self._generate_with_retry(styled_prompt, max_retries=2, initial_delay=1.0)
        except Exception as e:
            logger.error(f"Failed to generate tweet from content: {e}")
            return f"{f['title']} detayları burada! 👇\n\n{f['url']} #Teknoloji #{f['source'].replace(' ', '')}"

    # ─── VIRAL SCORING & THREAD GENERATION ────────────────────

    async def score_viral_potential(self, items: list) -> list:
        """
        AI ile içerik listesini viral potansiyeline göre skorla.
        Her item'a 1-10 arası viral_score atar.
        En yüksek skorlular döndürülür.
        """
        if not items:
            return []

        # Başlıkları topla (max 20 item gönder, token limiti için)
        summaries = []
        for i, item in enumerate(items[:20]):
            f = self._extract_content_fields(item)
            summaries.append(f"{i+1}. [{f['source']}] {f['title']}")

        items_text = "\n".join(summaries)

        prompt = f"""Sen X/Twitter viral içerik stratejistisin. 10M+ impression almış yüzlerce thread analiz etmişsin.

Aşağıdaki haber/içerik listesini oku ve HER BİRİNE 1-10 arası bir viral potansiyel skoru ver.

🎯 SKORLAMA KRİTERLERİ (ağırlık sırasıyla):

1. TARTIŞMA POTANSİYELİ (×3): İnsanlar buna "katılıyorum/katılmıyorum" diye yorum yapar mı? Kutuplaştırıcı mı?
2. MERAK BOŞLUĞU (×3): "Bunu bilmiyordum!" dedirtir mi? Şaşırtıcı bir açı var mı?
3. KİŞİSEL ETKİ (×2): Okuyanın hayatını, işini, parasını etkiler mi? "Bu beni ilgilendiriyor" dedirtir mi?
4. ZAMANLAMA (×2): Şu an herkesin konuştuğu bir konuyla bağlantılı mı?
5. PAYLAŞILABILIRLIK (×1): İnsanlar bunu paylaşarak "akıllı/bilgili" görünür mü?
6. EVRENSELLIK (×1): Sadece niş mi yoksa geniş kitle mi ilgilenir?

⚠️ DÜŞÜK SKOR VER (1-4):
- Sıradan ürün güncellemesi, versiyon notu
- "X şirketi Y yaptı" tarzı düz haber
- Niş akademik makale (geniş kitleyi ilgilendirmeyen)
- Zaten herkesin bildiği şeyler

✅ YÜKSEK SKOR VER (7-10):
- Endüstriyi sarsacak gelişmeler
- Parasal/kariyer etkisi olan haberler
- Büyük şirketlerin skandalları, sızıntıları
- "İmkansız" deneni başaran projeler
- Toplumu bölen tartışmalı konular
- Beklenmedik veri/istatistikler

İçerik listesi:
{items_text}

SADECE aşağıdaki formatta JSON döndür, başka hiçbir şey yazma:
[{{"index": 1, "score": 8}}, {{"index": 2, "score": 3}}, ...]
"""
        try:
            response = await self._generate_with_retry(prompt, max_retries=3, initial_delay=15.0)
            # JSON parse
            import json as _json
            # Temizle (bazen ```json ... ``` ile sarar)
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                clean = clean.strip()
            
            scores = _json.loads(clean)
            
            # Skoru atama
            scored_items = []
            score_map = {s["index"]: s["score"] for s in scores}
            for i, item in enumerate(items[:20]):
                score = score_map.get(i + 1, 5)
                scored_items.append({"item": item, "viral_score": score})
            
            # Skordan büyükten küçüğe sırala
            scored_items.sort(key=lambda x: x["viral_score"], reverse=True)
            logger.info(f"✅ Viral scoring complete. Top score: {scored_items[0]['viral_score'] if scored_items else 0}")
            return scored_items
            
        except Exception as e:
            logger.error(f"❌ Viral scoring failed: {e}")
            # Fallback: hepsine 5 ver
            return [{"item": item, "viral_score": 5} for item in items]

    async def generate_thread(self, content_item, language: str = "tr") -> list:
        """
        Tek bir içerik için X/Twitter thread'i üret (3-5 tweet).
        
        Args:
            content_item: ContentItem veya dict
            language: 'tr' veya 'en'
        
        Returns:
            List of tweet strings (thread sırasıyla)
        """
        f = self._extract_content_fields(content_item)
        
        if language == "tr":
            prompt = f"""Sen X/Twitter'da 10M+ impression alan thread'ler yazan bir viral içerik uzmanısın.

Aşağıdaki haber/içerik hakkında TÜRKÇE bir viral THREAD yaz (4-6 tweet):

Kaynak: {f['source']}
Başlık: {f['title']}
Detay: {f['summary'][:500]}
Link: {f['url']}

🔥 VİRAL THREAD STRATEJİSİ:

📌 TWEET 1 - HOOK (en kritik tweet, okumaya devam ettirmeli):
Aşağıdaki hook tekniklerinden BİRİNİ kullan:
- MERAK BOŞLUĞU: "X sessizce Y yaptı ve kimse fark etmedi..."
- ŞOK EDİCİ İSTATİSTİK: "Y'nin %87'si Z yapıyor. Ama asıl şok edici olan..."
- CESUR İDDİA: "X öldü. İşte neden herkes yanlış bakıyor..."
- KİŞİSEL HİKAYE: "3 yıl önce X yapıyordum. Bugün Y her şeyi değiştirdi."
- KARŞI SEZGISEL: "Herkes X sanıyor. Gerçek tam tersi."
🧵 ile başla, sonunda "👇" koy.

📌 TWEET 2-4 - GÖVDe (bilgiyi parçala, her tweet bir nugget):
- Her tweet tek bir güçlü fikir/veri içersin
- Kısa cümleler kullan (max 15 kelime per cümle)
- Somut sayılar, karşılaştırmalar, örnekler ver
- "Ama asıl mesele şu:" gibi geçiş cümleleri kullan
- Her tweet tek başına da değer versin (RT edilebilir olsun)

📌 SON TWEET - CTA (harekete geçir):
- Link ekle
- "Takip et + 🔔 aç" tarzı CTA
- Max 2 hashtag
- Tartışma sorusu sor: "Sen ne düşünüyorsun?"

⛔ YAPMA:
- "Merhaba arkadaşlar" gibi başlama
- Düz haber dili kullanma
- "Bu önemli bir gelişme" gibi sıkıcı cümleler
- Thread numarası (1/, 2/) kullanma
- 3'ten fazla emoji üst üste koyma

✅ YAP:
- Konuşma dili kullan ("Bak şimdi", "Düşünsene", "İşte olay burada")
- Kısa paragraflar (2-3 satır max)
- Güçlü fiiller kullan
- Her tweeti cliffhanger ile bitir
- Aranabilir anahtar kelimeleri (AI, GPT, Bitcoin, Startup vb.) metne DOĞAL yedir (hashtag olarak değil)
- İçerikte geçen şirket/kişi varsa @handle ile etiketle (örn: @OpenAI, @elonmusk)

SADECE tweet metinlerini döndür, her birini --- ile ayır. Başka açıklama yapma.
"""
        else:
            prompt = f"""You are a viral X/Twitter ghostwriter who has written threads with 10M+ impressions.

Write an ENGLISH viral THREAD (4-6 tweets) about this content:

Source: {f['source']}
Title: {f['title']}
Detail: {f['summary'][:500]}
Link: {f['url']}

🔥 VIRAL THREAD PLAYBOOK:

📌 TWEET 1 - THE HOOK (most critical tweet, must stop the scroll):
Use ONE of these proven hook formulas:
- CURIOSITY GAP: "X just quietly did Y and nobody noticed..."
- SHOCKING STAT: "87% of Z does W. But the real shock is..."
- BOLD CLAIM: "X is dead. Here's why everyone is looking at it wrong..."
- CONTRARIAN TAKE: "Everyone thinks X. The truth is the opposite."
- PREDICTION: "In 12 months, X will completely change Y. Here's why:"
Start with 🧵, end with 👇

📌 TWEETS 2-4 - THE BODY (each tweet = one powerful insight):
- One strong idea per tweet
- Short punchy sentences (max 15 words each)
- Use concrete numbers, comparisons, examples
- Transition phrases: "But here's the thing:", "It gets wilder:"
- Each tweet should be independently retweetable

📌 LAST TWEET - THE CTA (drive action):
- Include the link
- Ask a debate question: "What's your take?"
- Max 2 hashtags
- "Follow for more" type CTA

⛔ DON'T:
- Start with "Hey everyone" or "Today I want to talk about"
- Use flat news language
- Say "This is an important development"
- Use thread numbering (1/, 2/)
- Stack more than 3 emojis

✅ DO:
- Write like you're telling a friend something mind-blowing
- Use power verbs and short paragraphs
- End each tweet with a cliffhanger
- Be opinionated, not neutral
- Naturally weave in searchable keywords (AI, GPT, Bitcoin, Startup etc.) into the text — NOT as hashtags
- If a company/person is mentioned in the content, tag their @handle (e.g., @OpenAI, @elonmusk)

Return ONLY the tweet texts, separated by ---. No extra explanation.
"""
        
        try:
            raw = await self._generate_with_retry(prompt, max_retries=3, initial_delay=15.0)
            # --- ile ayır
            tweets = [t.strip() for t in raw.split("---") if t.strip()]
            
            # Boş veya çok kısa olanları filtrele
            tweets = [t for t in tweets if len(t) > 20]
            
            if not tweets:
                raise ValueError("Empty thread generated")
            
            logger.info(f"✅ Thread generated ({language}): {len(tweets)} tweets")
            return tweets
            
        except Exception as e:
            logger.error(f"❌ Thread generation failed ({language}): {e}")
            # Fallback: tek tweet
            if language == "tr":
                return [f"🧵 {f['title']}\n\nDetaylar 👇\n{f['url']} #Teknoloji"]
            else:
                return [f"🧵 {f['title']}\n\nDetails 👇\n{f['url']} #Tech"]

    async def generate_viral_threads(self, items: list, top_n: int = 5) -> list:
        """
        Tam pipeline: Viral skorla → En iyi N'ini seç → TR + EN thread üret.
        
        Returns:
            List of dicts: [{item, viral_score, tr_thread, en_thread}, ...]
        """
        logger.info(f"🚀 Starting viral thread pipeline for {len(items)} items (top {top_n})...")
        
        # 1. Viral skorlama
        scored = await self.score_viral_potential(items)
        
        # 2. En iyi N tanesini al (skor >= 6 olanları öncelikle)
        top_items = scored[:top_n]
        logger.info(f"🏆 Selected top {len(top_items)} items for thread generation")
        
        results = []
        for entry in top_items:
            item = entry["item"]
            viral_score = entry["viral_score"]
            
            # Skor çok düşükse (4 ve altı) atla
            if viral_score <= 4:
                logger.info(f"⏭️ Skipping low-score item (score={viral_score})")
                continue
            
            try:
                # TR thread üret, ardından EN (sıralı — rate limit koruması)
                tr_thread = await self.generate_thread(item, language="tr")
                await asyncio.sleep(4)  # Gemini rate limit arası bekleme
                en_thread = await self.generate_thread(item, language="en")
                
                results.append({
                    "item": item,
                    "viral_score": viral_score,
                    "tr_thread": tr_thread,
                    "en_thread": en_thread,
                })
                logger.info(f"\u2705 Threads ready (score={viral_score}): {self._extract_content_fields(item)['title'][:50]}...")
                
                # İtemler arası bekleme (Gemini free tier)
                await asyncio.sleep(6)
                
            except Exception as e:
                logger.error(f"❌ Thread generation failed for item: {e}")
                continue
        
        logger.info(f"🎉 Viral thread pipeline complete: {len(results)} threads ready")
        return results


# Singleton instance
_generator_instance: Optional[AIContentGenerator] = None


def get_ai_generator() -> AIContentGenerator:
    """
    Get singleton AI content generator instance.
    
    Returns:
        AIContentGenerator instance
        
    Raises:
        ValueError: If GEMINI_API_KEY is not configured
    """
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = AIContentGenerator()
    return _generator_instance
