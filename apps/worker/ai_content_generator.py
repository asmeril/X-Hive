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
from typing import Optional, List
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
                            max_output_tokens=500,
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
                    retry_delay = initial_delay * (2 ** attempt)  # Exponential backoff
                    
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
