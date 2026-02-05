"""
Ultra simple sync test - just 1 tweet
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Suppress all logging
import logging
logging.basicConfig(level=logging.CRITICAL)

import asyncio
from intel.github_source import GitHubTrendingSource
from intel.ai_processor import ai_processor
from intel.base_source import ContentItem, ContentCategory

async def main():
    print("Creating test item...")
    
    # Create a simple test item
    item = ContentItem(
        title="SGLang is a high-performance serving framework for LLMs",
        description="A structured generation language designed for large language models (LLMs). Co-developed with SGLang team and LMSYS.",
        url="https://github.com/sgl-project/sglang",
        source_type="github",
        source_name="GitHub Trending",
        category=ContentCategory.AI_ML,
        relevance_score=1.0,
        engagement_score=1.0
    )
    
    print("Processing with Gemini AI...")
    processed = await ai_processor.process_item(item)
    
    if processed.processed:
        # Save to file
        result = {
            'title': processed.title,
            'url': processed.url,
            'quality': str(processed.quality),
            'summary': processed.ai_summary,
            'tweet': processed.suggested_tweet
        }
        
        with open('single_tweet.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print("\n" + "="*80)
        print("SUCCESS! Tweet generated:")
        print("="*80)
        print(f"Summary: {processed.ai_summary}")
        print(f"Tweet: {processed.suggested_tweet}")
        print(f"Quality: {processed.quality}")
        print("="*80)
        print("\nSaved to: single_tweet.json")
    else:
        print("FAILED to generate tweet")

if __name__ == "__main__":
    asyncio.run(main())
