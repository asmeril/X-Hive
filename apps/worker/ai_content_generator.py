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
import re as _re
import time
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_SCOUT_MODEL = os.getenv("GEMINI_SCOUT_MODEL", "models/gemini-2.0-flash-lite")
GEMINI_WRITER_MODEL = os.getenv("GEMINI_WRITER_MODEL", "models/gemini-2.5-pro")
# Scout tier: hız + maliyet öncelikli (100+ item skorluyor)
# flash-lite (en ucuz/hızlı) → 2.5-flash-lite (lite ama yeni nesil) → 2.5-flash (güvenilir production)
GEMINI_SCOUT_FALLBACK_MODELS = [
    model.strip()
    for model in os.getenv("GEMINI_SCOUT_FALLBACK_MODELS", "models/gemini-2.5-flash-lite,models/gemini-2.5-flash").split(",")
    if model.strip()
]
# Writer tier: kalite öncelikli (döngü başına 2-6 çağrı)
# 2.5-flash (production ~1000 RPM) → 3-flash-preview (yeni nesil bonus) → 2.0-flash (kurtarma)
GEMINI_WRITER_FALLBACK_MODELS = [
    model.strip()
    for model in os.getenv("GEMINI_WRITER_FALLBACK_MODELS", "models/gemini-3-flash-preview,models/gemini-2.0-flash").split(",")
    if model.strip()
]

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class AIContentGenerator:
    """
    Generate AI-powered content for X/Twitter posts using Google Gemini.
    
    All operations are async and support Turkish prompts for better content quality.
    """
    # Class-level Gemini API throttle — shared across all coroutines/instances
    _api_lock: asyncio.Lock = None        # lazy-init (requires running event loop)
    _last_api_call: float = 0.0           # monotonic timestamp of last call start

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
        
        # Two-stage Gemini strategy:
        # - scout_model: cheaper/faster candidate scoring
        # - writer_model: stronger model for final viral thread writing
        self.scout_model = GEMINI_SCOUT_MODEL
        self.writer_model = GEMINI_WRITER_MODEL
        self.model = self.writer_model
        self.scout_models = self._unique_models(
            [self.scout_model, *GEMINI_SCOUT_FALLBACK_MODELS, self.writer_model]
        )
        self.writer_models = self._unique_models(
            [self.writer_model, *GEMINI_WRITER_FALLBACK_MODELS]
        )
        
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
        
        logger.info(
            f"[OK] AIContentGenerator initialized | scout={self.scout_model} | writer={self.writer_model}"
        )
        
        # Default topics for daily post generation
        self.default_topics = [
            "Yapay zeka ve otomasyon",
            "Verimlilik ipuçları",
            "Teknoloji inovasyonu"
        ]

    def _unique_models(self, models: List[str]) -> List[str]:
        unique_models = []
        for model in models:
            if model and model not in unique_models:
                unique_models.append(model)
        return unique_models

    def _truncate_prose(self, text: str, limit: int) -> str:
        """URL içermeyen düz metni anlam sınırından kırp."""
        if len(text) <= limit:
            return text
        window = text[:limit]
        for punct in ('. ', '! ', '? '):
            idx = window.rfind(punct)
            if idx > limit // 2:
                return text[:idx + 1].rstrip()
        for punct in (', ', '; ', ': '):
            idx = window.rfind(punct)
            if idx > limit // 2:
                return text[:idx] + '…'
        idx = window.rfind(' ')
        if idx > limit // 2:
            return text[:idx] + '…'
        return window[:limit - 1] + '…'

    def _smart_truncate_tweet(self, text: str, limit: int = 270) -> str:
        """Anlam butunlugunu ve URL'yi koruyarak tweet kirp.
        URL iceren tweet: URL korunur, onceki metin prose sinirinda kirpilir.
        URL olmayan tweet: cumle -> virgul -> kelime sinirinda kirp.
        """
        if len(text) <= limit:
            return text
        url_match = _re.search(r'https?://\S+', text)
        if url_match:
            url = url_match.group()
            pre_url = text[:url_match.start()].strip()
            post_url = text[url_match.end():].strip()
            url_part = '\n' + url
            prose_budget = limit - len(url_part)
            if prose_budget < 20:
                return url[:limit]
            truncated_pre = self._truncate_prose(pre_url, prose_budget)
            result = truncated_pre + url_part
            if post_url and len(result) + 1 + len(post_url) <= limit:
                result += ' ' + post_url
            return result
        return self._truncate_prose(text, limit)

    async def _generate_with_model_fallback(
        self,
        prompt: str,
        preferred_models: List[str],
        **kwargs,
    ) -> str:
        last_error = None

        for model_name in self._unique_models(preferred_models):
            try:
                if model_name != preferred_models[0]:
                    logger.warning(f"⚠️ Switching Gemini model fallback -> {model_name}")
                return await self._generate_with_retry(
                    prompt,
                    model=model_name,
                    **kwargs,
                )
            except Exception as exc:
                last_error = exc
                logger.warning(f"⚠️ Model {model_name} failed: {exc}")

        raise Exception(f"All Gemini models failed: {last_error}")
    
    async def _generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        model: Optional[str] = None,
        min_gap_seconds: Optional[float] = None,
        max_output_tokens: int = 2000,
        max_backoff_seconds: float = 900.0,
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
        active_model = model or self.writer_model

        # Lazy-init class-level lock (asyncio.Lock requires a running event loop)
        if AIContentGenerator._api_lock is None:
            AIContentGenerator._api_lock = asyncio.Lock()

        for attempt in range(max_retries):
            try:
                logger.debug(f"[RETRY] Attempt {attempt + 1}/{max_retries}")

                # Global rate-limiter: one Gemini call at a time.
                async with AIContentGenerator._api_lock:
                    enforced_gap = min_gap_seconds if min_gap_seconds is not None else 15.0
                    gap = enforced_gap - (
                        time.monotonic() - AIContentGenerator._last_api_call
                    )
                    if gap > 0:
                        logger.info(f"⏳ Gemini throttle: {gap:.1f}s bekleniyor | model={active_model}")
                        await asyncio.sleep(gap)
                    AIContentGenerator._last_api_call = time.monotonic()

                    # Call Gemini API (serialized inside lock — one request at a time)
                    response = await asyncio.to_thread(
                        lambda: self.client.models.generate_content(
                            model=active_model,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=0.9,
                                max_output_tokens=max_output_tokens,
                                top_p=0.95,
                                top_k=40,
                                safety_settings=self.safety_settings
                            )
                        )
                    )
                    AIContentGenerator._last_api_call = time.monotonic()

                # Extract text from response
                text = response.text.strip()
                logger.info(f"✅ Generated content on attempt {attempt + 1}")
                return text

            except Exception as e:
                error_msg = str(e)

                # RPM / quota rate limit (429 / RESOURCE_EXHAUSTED)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    extra = min(max_backoff_seconds, max(5.0, initial_delay * (2 ** attempt)))
                    logger.warning(
                        f"⏳ Rate limit on {active_model} (attempt {attempt + 1}/{max_retries}), {extra:.0f}s bekleniyor..."
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(extra)
                    else:
                        raise Exception(f"Gemini rate limit on {active_model} after {max_retries} attempts")

                # Safety filter rejection
                elif "finish_reason" in error_msg or "Invalid operation" in error_msg:
                    logger.warning(f"⚠️ Content filtered (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(initial_delay * (attempt + 1))

                else:
                    logger.error(f"❌ Generation error (attempt {attempt + 1}/{max_retries}): {error_msg}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(initial_delay * (2 ** attempt))

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
            post_text = await self._generate_with_retry(
                prompt,
                max_retries=4,
                initial_delay=5.0,
                model=self.scout_model,
                min_gap_seconds=8.0,
                max_output_tokens=500,
                max_backoff_seconds=120.0,
            )
            
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
            reply_text = await self._generate_with_retry(
                prompt,
                max_retries=4,
                initial_delay=5.0,
                model=self.scout_model,
                min_gap_seconds=8.0,
                max_output_tokens=400,
                max_backoff_seconds=120.0,
            )
            
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
        if isinstance(content_item, dict):
            return {
                "title": content_item.get("title", ""),
                "url": content_item.get("url", ""),
                "source": content_item.get("source_name", content_item.get("source", "Kaynak")),
                "summary": content_item.get("ai_summary", content_item.get("summary", content_item.get("description", ""))),
                "category": content_item.get("category", ""),
            }
        
        # Assume ContentItem dataclass or similar object
        return {
            "title": getattr(content_item, 'title', "") or "",
            "url": getattr(content_item, 'url', "") or "",
            "source": getattr(content_item, 'source_name', "Kaynak") or "Kaynak",
            "summary": (getattr(content_item, 'ai_summary', "") or 
                       getattr(content_item, 'description', "") or ""),
            "category": getattr(content_item, 'category', "") or "",
        }

    def _validate_thread_quality(self, tweets: List[str], language: str) -> None:
        """Strict quality gate for thread output. Raises ValueError if invalid."""
        if not tweets:
            raise ValueError("Empty thread")
        if len(tweets) < 4 or len(tweets) > 6:
            raise ValueError(f"Invalid thread length: {len(tweets)} (expected 4-6)")

        first = tweets[0].strip()
        if "🧵" not in first:
            raise ValueError("Hook tweet must include 🧵")
        if "Detaylar 👇" in first or "Details 👇" in first:
            raise ValueError("Detected fallback-like hook format")

        for i, tw in enumerate(tweets, start=1):
            if len(tw.strip()) < 40:
                raise ValueError(f"Tweet {i} too short")
            # Anlam bütünlüğünü koruyan akıllı kırpma (270 char hedef — URL sayımı için buffer)
            if len(tweets[i - 1]) > 270:
                original_len = len(tweets[i - 1])
                tweets[i - 1] = self._smart_truncate_tweet(tweets[i - 1], limit=270)
                logger.warning(f"⚠️ Tweet {i} akıllı kırpıldı: {original_len} → {len(tweets[i-1])} karakter")

        # Source link should appear somewhere in the thread (not necessarily the last tweet)
        has_link = any(("http://" in t or "https://" in t) for t in tweets)
        if not has_link:
            raise ValueError("Thread missing source link")

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
            raise

    # ─── VIRAL SCORING & THREAD GENERATION ────────────────────

    def _estimate_virality_prior(self, item) -> float:
        """Cheap heuristic prior before spending LLM tokens."""
        f = self._extract_content_fields(item)
        title = (f.get("title") or "").lower()
        source = (f.get("source") or "").lower()
        relevance = float(getattr(item, "relevance_score", 0.5) or 0.5)
        engagement = float(getattr(item, "engagement_score", 0.5) or 0.5)

        score = relevance * 4.0 + engagement * 3.0

        hot_terms = [
            "openai", "anthropic", "google", "meta", "microsoft", "nvidia", "xai",
            "gpt", "claude", "grok", "gemini", "bitcoin", "crypto", "lawsuit",
            "leak", "ban", "launch", "funding", "acquisition", "%", "$", "million", "billion"
        ]
        if any(term in title for term in hot_terms):
            score += 1.5
        if any(ch.isdigit() for ch in title):
            score += 0.7
        if "hacker news" in source or "reddit" in source:
            score += 0.6
        if "github" in source or "product hunt" in source:
            score += 0.4

        return score

    def _select_candidates_for_scoring(self, items: list, limit: int = 12) -> list:
        ranked = sorted(items, key=self._estimate_virality_prior, reverse=True)
        return ranked[:limit]

    async def score_viral_potential(self, items: list) -> list:
        """
        AI ile içerik listesini viral potansiyeline göre skorla.
        Her item'a 1-10 arası viral_score atar.
        En yüksek skorlular döndürülür.
        """
        if not items:
            return []

        candidates = self._select_candidates_for_scoring(items, limit=12)

        # Başlıkları topla (önce heuristik ile daraltıldı)
        summaries = []
        for i, item in enumerate(candidates):
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

⚠️ DÜŞÜK SKOR VER (1-5):
- Sıradan ürün güncellemesi, versiyon notu
- "X şirketi Y yaptı" tarzı düz haber
- Niş akademik makale (geniş kitleyi ilgilendirmeyen)
- Zaten herkesin bildiği şeyler

✅ YÜKSEK SKOR VER (8-10):
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
            response = await self._generate_with_model_fallback(
                prompt,
                preferred_models=self.scout_models,
                max_retries=3,
                initial_delay=10.0,
                min_gap_seconds=8.0,
                max_output_tokens=1200,
                max_backoff_seconds=120.0,
            )
            # JSON parse
            import json as _json
            import re as _re

            # Temizle (bazen ```json ... ``` ile sarar)
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                clean = clean.strip()

            start = clean.find("[")
            end = clean.rfind("]")
            if start != -1 and end != -1 and end > start:
                clean = clean[start:end + 1]

            try:
                scores = _json.loads(clean)
            except Exception:
                matches = _re.findall(
                    r'"index"\s*:\s*(\d+)\D+"score"\s*:\s*(\d+)',
                    clean,
                    flags=_re.S,
                )
                if not matches:
                    raise
                scores = [
                    {"index": int(index), "score": max(1, min(10, int(score)))}
                    for index, score in matches
                ]
                logger.warning("⚠️ Viral scoring response repaired with regex fallback")

            # Skoru atama
            scored_items = []
            score_map = {int(s["index"]): int(s["score"]) for s in scores}
            for i, item in enumerate(candidates):
                score = score_map.get(i + 1, 5)
                scored_items.append({"item": item, "viral_score": score})
            
            # Skordan büyükten küçüğe sırala
            scored_items.sort(key=lambda x: x["viral_score"], reverse=True)
            logger.info(f"✅ Viral scoring complete. Top score: {scored_items[0]['viral_score'] if scored_items else 0}")
            return scored_items
            
        except Exception as e:
            logger.error(f"❌ Viral scoring failed: {e}")
            # No-fallback policy: scoring yoksa thread üretimine geçme
            return []

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

📌 TWEET 2-4 - GÖVDE (bilgiyi parçala, her tweet bir nugget):
- Her tweet tek bir güçlü fikir/veri içersin
- Kısa cümleler kullan (max 15 kelime per cümle)
- Somut sayılar, karşılaştırmalar, örnekler ver
- "Ama asıl mesele şu:" gibi geçiş cümleleri kullan
- Her tweet tek başına da değer versin (RT edilebilir olsun)
- En az 1 somut veri, sayı veya karşılaştırma ver

📌 SON TWEET - CTA (harekete geçir):
- Link ekle
- "Takip et + 🔔 aç" tarzı CTA
- Max 2 hashtag
- Tartışma sorusu sor: "Sen ne düşünüyorsun?"
- Son tweette KAYNAK LINK zorunlu

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

SADECE tweet metinlerini döndür, her birini --- ile ayır. Tam olarak 5 tweet üret.
Başka açıklama yapma.
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
- Include at least one concrete number/data point across the body tweets

📌 LAST TWEET - THE CTA (drive action):
- Include the link
- Ask a debate question: "What's your take?"
- Max 2 hashtags
- "Follow for more" type CTA
- Include the source LINK in the final tweet

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

Return ONLY the tweet texts, separated by ---. Produce exactly 5 tweets. No extra explanation.
"""
        
        try:
            raw = await self._generate_with_model_fallback(
                prompt,
                preferred_models=self.writer_models,
                max_retries=2,
                initial_delay=20.0,
                min_gap_seconds=20.0,
                max_output_tokens=2500,
                max_backoff_seconds=120.0,
            )
            # --- ile ayır
            tweets = [t.strip() for t in raw.split("---") if t.strip()]
            
            # Boş veya çok kısa olanları filtrele
            tweets = [t for t in tweets if len(t) > 20]
            
            self._validate_thread_quality(tweets, language)
            
            logger.info(f"✅ Thread generated ({language}): {len(tweets)} tweets")
            return tweets
            
        except Exception as e:
            logger.error(f"❌ Thread generation failed ({language}): {e}")
            raise

    async def generate_viral_threads(self, items: list, top_n: int = 3) -> list:
        """
        Tam pipeline: Viral skorla → En iyi N'ini seç → TR + EN thread üret.
        
        Returns:
            List of dicts: [{item, viral_score, tr_thread, en_thread}, ...]
        """
        logger.info(f"🚀 Starting viral thread pipeline for {len(items)} items (top {top_n})...")
        
        # 1. Viral skorlama
        scored = await self.score_viral_potential(items)
        if not scored:
            logger.warning("⚠️ No scored candidates; skipping thread generation")
            return []
        
        # 2. En iyi N tanesini al (yalnızca yüksek skorlu içerikler)
        top_items = scored[:top_n]
        logger.info(f"🏆 Selected top {len(top_items)} items for thread generation")
        
        results = []
        for entry in top_items:
            item = entry["item"]
            viral_score = entry["viral_score"]
            
            # Yüksek kalite eşiği: 7 ve altını atla
            if viral_score <= 7:
                logger.info(f"⏭️ Skipping low-score item (score={viral_score})")
                continue
            
            try:
                # TR thread üret, ardından EN (sıralı).
                # Model çağrıları kendi throttle/backoff mekanizmasıyla yönetilir.
                tr_thread = await self.generate_thread(item, language="tr")
                en_thread = await self.generate_thread(item, language="en")
                
                results.append({
                    "item": item,
                    "viral_score": viral_score,
                    "tr_thread": tr_thread,
                    "en_thread": en_thread,
                })
                logger.info(f"\u2705 Threads ready (score={viral_score}): {self._extract_content_fields(item)['title'][:50]}...")
                
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
