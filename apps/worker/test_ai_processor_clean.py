#!/usr/bin/env python3
"""
Test AI Content Processor with Turkish Language Support
No emoji - simple ASCII output
"""

import sys
import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env first
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, '.')

from intel.ai_processor import ai_processor, ai_processor_en
from intel.base_source import ContentItem, ContentCategory, ContentQuality


async def test_turkish_processor():
    """Test Turkish AI processor"""
    
    print("\n" + "=" * 80)
    print("[TR] TURKISH AI CONTENT PROCESSOR TEST")
    print("=" * 80)
    
    if not ai_processor or not ai_processor.client:
        print("[ERROR] Turkish processor not available (missing GEMINI_API_KEY or client)")
        return False
    
    print("[OK] Turkish Processor Initialized:")
    print("  Model: " + str(ai_processor.model_name))
    print("  Language: " + str(ai_processor.language))
    
    test_item = ContentItem(
        title="Microsoft's BitNet - 1-bit LLM Framework",
        url="https://github.com/microsoft/BitNet",
        source_type="github",
        source_name="GitHub Trending",
        description="BitNet enables running large language models with 1-bit weights, dramatically reducing memory and compute requirements.",
        category=ContentCategory.AI_ML,
        relevance_score=0.95,
        engagement_score=0.85
    )
    
    print("\n[ITEM] Test Item:")
    print("  Title: " + test_item.title)
    print("  Category: " + test_item.category.name)
    
    print("\n[AI] Processing with Turkish Processor...")
    try:
        processed = await ai_processor.process_item(test_item)
        
        print("[OK] Processing Complete:")
        print("  Processed: " + str(processed.processed))
        print("  Quality: " + (processed.quality.name if processed.quality else 'N/A'))
        
        if processed.ai_summary:
            print("\n[SUMMARY] Turkish Summary:")
            print("  " + processed.ai_summary)
        
        if processed.suggested_tweet:
            tweet_len = len(processed.suggested_tweet)
            print("\n[TWEET] Turkish Tweet ({} chars):".format(tweet_len))
            print("  " + processed.suggested_tweet)
        
        return True
    
    except Exception as e:
        print("[ERROR] " + str(e))
        import traceback
        traceback.print_exc()
        return False


async def test_english_processor():
    """Test English AI processor"""
    
    print("\n" + "=" * 80)
    print("[EN] ENGLISH AI CONTENT PROCESSOR TEST")
    print("=" * 80)
    
    if not ai_processor_en or not ai_processor_en.client:
        print("[ERROR] English processor not available (missing GEMINI_API_KEY or client)")
        return False
    
    print("[OK] English Processor Initialized:")
    print("  Model: " + str(ai_processor_en.model_name))
    print("  Language: " + str(ai_processor_en.language))
    
    test_item = ContentItem(
        title="OpenAI Announces GPT-5 Preview",
        url="https://openai.com/gpt5",
        source_type="news",
        source_name="OpenAI Blog",
        description="OpenAI unveils GPT-5 with improved reasoning, faster inference, and better multimodal capabilities.",
        category=ContentCategory.AI_ML,
        relevance_score=0.98,
        engagement_score=0.92
    )
    
    print("\n[ITEM] Test Item:")
    print("  Title: " + test_item.title)
    print("  Category: " + test_item.category.name)
    
    print("\n[AI] Processing with English Processor...")
    try:
        processed = await ai_processor_en.process_item(test_item)
        
        print("[OK] Processing Complete:")
        print("  Processed: " + str(processed.processed))
        print("  Quality: " + (processed.quality.name if processed.quality else 'N/A'))
        
        if processed.ai_summary:
            print("\n[SUMMARY] English Summary:")
            print("  " + processed.ai_summary)
        
        if processed.suggested_tweet:
            tweet_len = len(processed.suggested_tweet)
            print("\n[TWEET] English Tweet ({} chars):".format(tweet_len))
            print("  " + processed.suggested_tweet)
        
        return True
    
    except Exception as e:
        print("[ERROR] " + str(e))
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    
    print("=" * 80)
    print("[TEST] AI CONTENT PROCESSOR LANGUAGE SUPPORT")
    print("=" * 80)
    
    tr_result = await test_turkish_processor()
    en_result = await test_english_processor()
    
    print("\n" + "=" * 80)
    print("[SUMMARY] TEST RESULTS")
    print("=" * 80)
    print("Turkish Processor: " + ('PASSED' if tr_result else 'FAILED'))
    print("English Processor: " + ('PASSED' if en_result else 'FAILED'))
    print("=" * 80 + "\n")
    
    return tr_result and en_result


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n[WARN] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print("[ERROR] Test failed: " + str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
