"""
AI Content Processor for X-Hive

Processes ContentItem objects into ready-to-post tweets using Gemini AI.
Generates summaries, tweets, hashtags, and quality assessments.
"""

import logging
from typing import List, Optional, Dict
import asyncio
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

# Google Generative AI SDK (new SDK)
import google.genai as genai
from google.genai.types import GenerateContentResponse

from .base_source import ContentItem, ContentCategory, ContentQuality

# Load environment variables from worker directory
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Fallback to current directory
    load_dotenv()

logger = logging.getLogger(__name__)


class AIContentProcessor:
    """
    AI-powered content processor using Gemini.
    
    Processes ContentItem objects into ready-to-post tweets:
    - Summarizes content
    - Generates engaging tweets
    - Adds relevant hashtags
    - Filters low-quality content
    
    Features:
    - Async batch processing
    - Quality assessment
    - Category-aware prompts
    - Token optimization
    - Error handling with fallbacks
    """
    
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        language: str = "tr"  # 'tr' or 'en'
    ):
        """
        Initialize AI content processor.
        
        Args:
            model_name: Gemini model name
            language: Output language ('tr' for Turkish, 'en' for English)
        """
        
        # Always set language first
        self.language = language
        self.model_name = model_name
        self.model = None
        self.client = None
        
        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            logger.warning("GEMINI_API_KEY not found - AI processing disabled")
            return
        
        try:
            # Initialize client with API key
            self.client = genai.Client(api_key=api_key)
            logger.info(f"AIContentProcessor initialized ({model_name}, lang={language})")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
    
    async def process_item(self, item: ContentItem) -> ContentItem:
        """
        Process a single content item with AI.
        
        Adds:
        - ai_summary: Concise summary
        - suggested_tweet: Ready-to-post tweet
        - quality: Quality assessment
        
        Args:
            item: Content item to process
        
        Returns:
            Processed item with AI fields filled
        """
        
        if not self.client:
            logger.warning("AI processor not initialized - skipping")
            return item
        
        try:
            # Generate summary and tweet
            result = await self._generate_content(item)
            
            if result:
                item.ai_summary = result.get('summary', '')
                item.suggested_tweet = result.get('tweet', '')
                item.quality = self._assess_quality(item, result)
                item.processed = True
                
                logger.debug(f"✅ Processed: {item.title[:50]}...")
            else:
                logger.warning(f"⚠️ No AI result for: {item.title[:50]}...")
                item.processed = False
            
            return item
        
        except Exception as e:
            logger.error(f"❌ Failed to process item: {e}")
            item.processed = False
            return item
    
    async def process_batch(self, items: List[ContentItem], max_items: int = 10) -> List[ContentItem]:
        """
        Process multiple items (limited for API quota).
        
        Args:
            items: List of content items
            max_items: Max items to process (API limit)
        
        Returns:
            List of processed items
        """
        
        if not self.client:
            logger.warning("AI processor not initialized - returning items unprocessed")
            return items
        
        logger.info(f"🤖 Processing {min(len(items), max_items)} items with AI...")
        
        processed = []
        
        for i, item in enumerate(items[:max_items]):
            try:
                processed_item = await self.process_item(item)
                processed.append(processed_item)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
            
            except Exception as e:
                logger.error(f"❌ Failed to process item {i+1}: {e}")
                processed.append(item)  # Add unprocessed item
                continue
        
        successful = sum(1 for item in processed if item.processed)
        logger.info(f"✅ Processed {successful}/{len(processed)} items successfully")
        
        return processed
    
    async def _generate_content(self, item: ContentItem) -> Optional[Dict[str, str]]:
        """
        Generate summary and tweet using Gemini.
        
        Args:
            item: Content item
        
        Returns:
            Dictionary with 'summary' and 'tweet' keys
        """
        
        prompt = self._build_prompt(item)
        
        try:
            # Generate content asynchronously using new SDK
            model_name = f"models/{self.model_name}" if not self.model_name.startswith("models/") else self.model_name
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model_name,
                contents=prompt
            )
            
            if not response or not response.text:
                logger.warning("Empty response from Gemini")
                return None
            
            # Parse response
            result = self._parse_response(response.text)
            
            return result
        
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None
    
    def _build_prompt(self, item: ContentItem) -> str:
        """
        Build prompt for Gemini with language support.
        
        Args:
            item: Content item
        
        Returns:
            Formatted prompt
        """
        
        if self.language == 'tr':
            return self._build_turkish_prompt(item)
        else:
            return self._build_english_prompt(item)
    
    def _build_turkish_prompt(self, item: ContentItem) -> str:
        """
        Build Turkish prompt for Gemini.
        
        Args:
            item: Content item
        
        Returns:
            Formatted Turkish prompt
        """
        
        category_context = {
            ContentCategory.AI_ML: "Yapay Zeka/Makine Öğrenmesi",
            ContentCategory.TECH_NEWS: "Teknoloji",
            ContentCategory.STARTUP: "Startup/İş Dünyası",
            ContentCategory.PROGRAMMING: "Yazılım Geliştirme",
            ContentCategory.PRODUCTIVITY: "Verimlilik",
            ContentCategory.BLOCKCHAIN: "Blockchain/Web3",
            ContentCategory.CYBERSECURITY: "Siber Güvenlik",
            ContentCategory.DESIGN: "Tasarım/UX"
        }
        
        context = category_context.get(item.category, "Teknoloji")
        
        # Truncate description to save tokens
        description = item.description[:500] if item.description else ""
        
        prompt = f"""Sen bir teknoloji Twitter içerik uzmanısın. Bu {context} haberi için ilgi çekici Türkçe içerik oluştur.

İÇERİK:
Başlık: {item.title}
Açıklama: {description}
Kaynak: {item.source_name}
URL: {item.url}

GÖREV:
1. 1 cümlelik özet yaz (max 100 karakter)
2. İlgi çekici bir tweet oluştur (max 260 karakter, URL için yer bırak)

TWEET GEREKSİNİMLERİ:
- İlgi çekici ve bilgilendirici
- Ana değeri/yeniliği vurgula
- Profesyonel ama samimi üslup
- 2-3 İngilizce hashtag ekle (#AI, #MachineLearning gibi)
- Emoji KULLANMA (ayrıca ekleyeceğiz)
- Uygun olduğunda soru veya hook ile bitir
- Türkçe karakter kullan (ı, ş, ğ, ü, ö, ç, İ)

YANIT FORMATI (tam olarak):
ÖZET: [özetiniz burada]
TWEET: [tweet'iniz burada]

Örnek:
ÖZET: Microsoft 1-bit LLM framework'ü ile yapay zeka maliyetlerini düşürüyor
TWEET: Microsoft'un BitNet teknolojisi, LLM'leri 1-bit ağırlıklarla çalıştırarak bellek ve işlem maliyetlerini dramatik şekilde azaltıyor. Performans kaybı olmadan! Yapay zeka demokratikleşiyor mu? #MachineLearning #AI #OpenSource
"""
        
        return prompt
    
    def _build_english_prompt(self, item: ContentItem) -> str:
        """
        Build English prompt for Gemini.
        
        Args:
            item: Content item
        
        Returns:
            Formatted English prompt
        """
        
        category_context = {
            ContentCategory.AI_ML: "AI/Machine Learning",
            ContentCategory.TECH_NEWS: "Technology",
            ContentCategory.STARTUP: "Startup/Business",
            ContentCategory.PROGRAMMING: "Programming/Development",
            ContentCategory.PRODUCTIVITY: "Productivity",
            ContentCategory.BLOCKCHAIN: "Blockchain/Web3",
            ContentCategory.CYBERSECURITY: "Cybersecurity",
            ContentCategory.DESIGN: "Design/UX"
        }
        
        context = category_context.get(item.category, "Technology")
        
        # Truncate description to save tokens
        description = item.description[:500] if item.description else ""
        
        prompt = f"""You are a tech Twitter content expert. Create engaging content for this {context} story.

CONTENT:
Title: {item.title}
Description: {description}
Source: {item.source_name}
URL: {item.url}

TASK:
1. Write a 1-sentence summary (max 100 chars)
2. Create an engaging tweet (max 260 chars, leaving room for URL)

TWEET REQUIREMENTS:
- Engaging and informative
- Highlight key value/innovation
- Professional but conversational tone
- Include 2-3 relevant hashtags
- NO emoji (we'll add them separately)
- End with a hook or question when appropriate

RESPONSE FORMAT (exactly):
SUMMARY: [your summary here]
TWEET: [your tweet here]

Example:
SUMMARY: Microsoft releases 1-bit LLM framework for efficient inference
TWEET: Microsoft's BitNet enables running LLMs with 1-bit weights - dramatically reducing memory and compute costs while maintaining performance. Could this democratize AI deployment? #MachineLearning #AI #OpenSource
"""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict[str, str]:
        """
        Parse Gemini response into structured data.
        
        Args:
            response_text: Raw response from Gemini
        
        Returns:
            Dictionary with 'summary' and 'tweet'
        """
        
        lines = response_text.strip().split('\n')
        
        summary = ""
        tweet = ""
        
        for line in lines:
            line = line.strip()
            
            # Support both English and Turkish formats
            if line.startswith("SUMMARY:") or line.startswith("ÖZET:"):
                summary = line.replace("SUMMARY:", "").replace("ÖZET:", "").strip()
            elif line.startswith("TWEET:"):
                tweet = line.replace("TWEET:", "").strip()
        
        # Fallback: use first two non-empty lines
        if not summary or not tweet:
            non_empty = [l.strip() for l in lines if l.strip()]
            
            if not summary and len(non_empty) > 0:
                summary = non_empty[0]
            
            if not tweet and len(non_empty) > 1:
                tweet = non_empty[1]
        
        return {
            'summary': summary[:200],  # Truncate
            'tweet': tweet[:280]  # Twitter limit
        }
    
    def _assess_quality(self, item: ContentItem, ai_result: Dict[str, str]) -> ContentQuality:
        """
        Assess content quality based on multiple factors.
        
        Args:
            item: Content item
            ai_result: AI processing result
        
        Returns:
            ContentQuality enum
        """
        
        score = 0
        
        # Factor 1: Relevance score (max 3 points)
        if item.relevance_score >= 0.8:
            score += 3
        elif item.relevance_score >= 0.6:
            score += 2
        else:
            score += 1
        
        # Factor 2: Engagement score (max 2 points)
        if item.engagement_score >= 0.7:
            score += 2
        elif item.engagement_score >= 0.4:
            score += 1
        
        # Factor 3: AI-generated content quality (max 2 points)
        tweet = ai_result.get('tweet', '')
        
        if len(tweet) >= 100 and len(tweet) <= 280:
            score += 2
        elif len(tweet) > 0:
            score += 1
        
        # Factor 4: Category priority (max 1 point)
        if item.category == ContentCategory.AI_ML:
            score += 1
        
        # Determine quality (max 8 points)
        if score >= 7:
            return ContentQuality.HIGH
        elif score >= 4:
            return ContentQuality.MEDIUM
        else:
            return ContentQuality.LOW
    
    def filter_by_quality(
        self,
        items: List[ContentItem],
        min_quality: ContentQuality = ContentQuality.MEDIUM
    ) -> List[ContentItem]:
        """
        Filter items by quality level.
        
        Args:
            items: Content items
            min_quality: Minimum quality level
        
        Returns:
            Filtered items
        """
        
        quality_order = {
            ContentQuality.LOW: 0,
            ContentQuality.MEDIUM: 1,
            ContentQuality.HIGH: 2
        }
        
        min_level = quality_order[min_quality]
        
        filtered = [
            item for item in items
            if item.quality and quality_order.get(item.quality, 0) >= min_level
        ]
        
        logger.info(f"Filtered {len(filtered)}/{len(items)} items (min quality: {min_quality.name})")
        
        return filtered
    
    def get_best_items(
        self,
        items: List[ContentItem],
        n: int = 5
    ) -> List[ContentItem]:
        """
        Get top N items by quality and scores.
        
        Args:
            items: Content items
            n: Number of items to return
        
        Returns:
            Top N items
        """
        
        quality_order = {
            ContentQuality.LOW: 0,
            ContentQuality.MEDIUM: 1,
            ContentQuality.HIGH: 2
        }
        
        # Sort by quality, then relevance, then engagement
        sorted_items = sorted(
            items,
            key=lambda x: (
                quality_order.get(x.quality, 0),
                x.relevance_score,
                x.engagement_score
            ),
            reverse=True
        )
        
        return sorted_items[:n]


# Global instances (gracefully handle missing API key)
try:
    # Turkish version (default) - using latest stable gemini-2.5-flash model
    ai_processor = AIContentProcessor(
        model_name="gemini-2.5-flash",
        language='tr'
    )
    
    # English version (optional) - same model
    ai_processor_en = AIContentProcessor(
        model_name="gemini-2.5-flash",
        language='en'
    )
except Exception as e:
    logger.error(f"Failed to initialize AI processor: {e}")
    ai_processor = None
    ai_processor_en = None


# Test example
async def test_ai_processor():
    """Test AI content processor"""
    
    if not ai_processor or not ai_processor.client:
        print("AI processor not available (missing GEMINI_API_KEY)")
        return
    
    print("=" * 80)
    print("AI CONTENT PROCESSOR TEST")
    print("=" * 80)
    
    # Create test item
    test_item = ContentItem(
        title="Microsoft's BitNet - Official inference framework for 1-bit LLMs",
        url="https://github.com/microsoft/BitNet",
        source_type="github",
        source_name="GitHub Trending",
        description="BitNet enables running large language models with 1-bit weights, dramatically reducing memory and compute requirements while maintaining performance.",
        category=ContentCategory.AI_ML,
        relevance_score=0.95,
        engagement_score=0.85
    )
    
    print("\n[1] Processing test item...")
    print(f"Title: {test_item.title}")
    print(f"Category: {test_item.category.name}")
    
    processed = await ai_processor.process_item(test_item)
    
    print("\n[2] AI Processing Results:")
    print("=" * 80)
    print(f"\nSummary: {processed.ai_summary}")
    print(f"\nTweet: {processed.suggested_tweet}")
    print(f"\nQuality: {processed.quality.name if processed.quality else 'N/A'}")
    print(f"Processed: {processed.processed}")
    
    print("\n" + "=" * 80)
    print("✅ AI PROCESSOR TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_ai_processor())
