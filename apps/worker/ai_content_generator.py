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
from typing import Optional, List
import google.generativeai as genai

from config import GEMINI_API_KEY

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
            raise ValueError("❌ GEMINI_API_KEY not configured in .env")
        
        # Configure Gemini API
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Initialize model with optimized settings
        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            generation_config={
                'temperature': 0.9,
                'max_output_tokens': 300,
                'top_p': 0.95,
                'top_k': 40,
            }
        )
        
        logger.info("🤖 AIContentGenerator initialized (Gemini 1.5 Flash)")
        
        # Default topics for daily post generation
        self.default_topics = [
            "Yapay zeka ve otomasyon",
            "Verimlilik ipuçları",
            "Teknoloji inovasyonu"
        ]
    
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
        Generate a single X/Twitter post.
        
        Args:
            topic: Post topic (if None, uses generic tech topic)
            style: Writing style (professional, casual, humorous, inspirational)
            max_length: Maximum post length in characters
        
        Returns:
            Generated post text
            
        Raises:
            Exception: If API call fails
        """
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
        
        try:
            logger.debug(f"🔄 Generating post for topic: {topic} (style: {style})")
            
            # Call Gemini API asynchronously
            response = await asyncio.to_thread(
                lambda: self.model.generate_content(prompt)
            )
            
            post_text = response.text.strip()
            
            # Truncate if exceeds max_length
            if len(post_text) > max_length:
                logger.warning(f"📝 Post exceeds {max_length} chars, truncating...")
                post_text = post_text[:max_length - 3] + "..."
            
            logger.info(f"✅ Generated post ({len(post_text)} chars)")
            return post_text
            
        except Exception as e:
            logger.error(f"❌ Post generation failed: {e}")
            
            # Fallback post
            fallback = f"🚀 {topic}\n\n#XHive #AI"
            logger.warning(f"⚠️ Using fallback post")
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
        
        logger.info(f"📊 Generating {count} daily posts...")
        
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
            
            logger.info(f"✅ Generated {len(valid_posts)}/{count} posts")
            return valid_posts
            
        except Exception as e:
            logger.error(f"❌ Batch generation failed: {e}")
            return []
    
    async def generate_reply(
        self,
        original_tweet: str,
        tone: str = "friendly"
    ) -> str:
        """
        Generate a contextual reply to a tweet.
        
        Args:
            original_tweet: The original tweet text to reply to
            tone: Reply tone (friendly, informative, witty, supportive)
        
        Returns:
            Generated reply text
            
        Raises:
            Exception: If API call fails
        """
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
        
        try:
            logger.debug(f"🔄 Generating {tone} reply...")
            
            # Call Gemini API asynchronously
            response = await asyncio.to_thread(
                lambda: self.model.generate_content(prompt)
            )
            
            reply_text = response.text.strip()
            
            # Truncate if exceeds 280
            if len(reply_text) > 280:
                reply_text = reply_text[:277] + "..."
            
            logger.info(f"✅ Generated reply ({len(reply_text)} chars)")
            return reply_text
            
        except Exception as e:
            logger.error(f"❌ Reply generation failed: {e}")
            
            # Fallback reply
            fallback = f"👍 Harika paylaşım! #{tone}"
            logger.warning(f"⚠️ Using fallback reply")
            return fallback
    
    
    def _get_style_description(self, style: str) -> str:
        """
        Convert style code to Turkish description.
        
        Args:
            style: Style code (professional/casual/humorous/inspirational)
        
        Returns:
            Turkish style description
        """
        style_map = {
            "professional": "profesyonel ve bilgilendirici",
            "casual": "samimi ve rahat",
            "humorous": "eğlenceli ve mizahi",
            "inspirational": "ilham verici ve motive edici"
        }
        
        return style_map.get(style, "profesyonel")


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