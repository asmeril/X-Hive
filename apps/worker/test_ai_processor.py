#!/usr/bin/env python3
"""
Test AI Content Processor with Turkish Language Support
"""

import sys
import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env first, before any other imports
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.insert(0, '.')

from intel.ai_processor import ai_processor, ai_processor_en
from intel.base_source import ContentItem, ContentCategory, ContentQuality


async def test_turkish_processor():
    """Test Turkish AI processor"""
    
    print("\n" + "=" * 80)
    print("🇹🇷 TURKISH AI CONTENT PROCESSOR TEST")
    print("=" * 80)
    
    if not ai_processor or not ai_processor.model:
        print("❌ Turkish processor not available (missing GEMINI_API_KEY)")
        return False
    
    print(f"\n✅ Turkish Processor Initialized:")
    print(f"   Model: {ai_processor.model_name}")
    print(f"   Language: {ai_processor.language}")
    
    # Create test item
    test_item = ContentItem(
        title="Microsoft's BitNet - 1-bit LLM Framework",
        url="https://github.com/microsoft/BitNet",
        source_type="github",
        source_name="GitHub Trending",
        description="BitNet enables running large language models with 1-bit weights, dramatically reducing memory and compute requirements while maintaining performance.",
        category=ContentCategory.AI_ML,
        relevance_score=0.95,
        engagement_score=0.85
    )
    
    print(f"\n📝 Test Item:")
    print(f"   Title: {test_item.title}")
    print(f"   Category: {test_item.category.name}")
    print(f"   Relevance: {test_item.relevance_score:.2f}")
    print(f"   Engagement: {test_item.engagement_score:.2f}")
    
    print(f"\n🤖 Processing with Turkish Processor...")
    try:
        processed = await ai_processor.process_item(test_item)
        
        print(f"\n✅ Processing Complete:")
        print(f"   Processed: {processed.processed}")
        print(f"   Quality: {processed.quality.name if processed.quality else 'N/A'}")
        
        if processed.ai_summary:
            print(f"\n📊 Turkish Summary:")
            print(f"   {processed.ai_summary}")
        
        if processed.suggested_tweet:
            print(f"\n🐦 Turkish Tweet ({len(processed.suggested_tweet)} chars):")
            print(f"   {processed.suggested_tweet}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_english_processor():
    """Test English AI processor"""
    
    print("\n" + "=" * 80)
    print("🇺🇸 ENGLISH AI CONTENT PROCESSOR TEST")
    print("=" * 80)
    
    if not ai_processor_en or not ai_processor_en.model:
        print("❌ English processor not available (missing GEMINI_API_KEY)")
        return False
    
    print(f"\n✅ English Processor Initialized:")
    print(f"   Model: {ai_processor_en.model_name}")
    print(f"   Language: {ai_processor_en.language}")
    
    # Create test item
    test_item = ContentItem(
        title="OpenAI Announces GPT-5 Preview",
        url="https://openai.com/gpt5",
        source_type="news",
        source_name="OpenAI Blog",
        description="OpenAI unveils GPT-5, featuring improved reasoning, faster inference, and better multimodal capabilities.",
        category=ContentCategory.AI_ML,
        relevance_score=0.98,
        engagement_score=0.92
    )
    
    print(f"\n📝 Test Item:")
    print(f"   Title: {test_item.title}")
    print(f"   Category: {test_item.category.name}")
    print(f"   Relevance: {test_item.relevance_score:.2f}")
    print(f"   Engagement: {test_item.engagement_score:.2f}")
    
    print(f"\n🤖 Processing with English Processor...")
    try:
        processed = await ai_processor_en.process_item(test_item)
        
        print(f"\n✅ Processing Complete:")
        print(f"   Processed: {processed.processed}")
        print(f"   Quality: {processed.quality.name if processed.quality else 'N/A'}")
        
        if processed.ai_summary:
            print(f"\n📊 English Summary:")
            print(f"   {processed.ai_summary}")
        
        if processed.suggested_tweet:
            print(f"\n🐦 English Tweet ({len(processed.suggested_tweet)} chars):")
            print(f"   {processed.suggested_tweet}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    
    print("\n" + "=" * 80)
    print("🧪 AI CONTENT PROCESSOR LANGUAGE SUPPORT TEST")
    print("=" * 80)
    
    # Test Turkish
    tr_result = await test_turkish_processor()
    
    # Test English
    en_result = await test_english_processor()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Turkish Processor: {'✅ PASSED' if tr_result else '❌ FAILED'}")
    print(f"English Processor: {'✅ PASSED' if en_result else '❌ FAILED'}")
    print("=" * 80 + "\n")
    
    return tr_result and en_result


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
