"""
Generate multiple tweets and show all results
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import logging
logging.basicConfig(level=logging.CRITICAL)

import asyncio
from intel.aggregator import aggregator
from intel.ai_processor import ai_processor

async def main():
    print("Fetching trending content...")
    items = await aggregator.fetch_all()
    
    print(f"Found {len(items)} items")
    print("Selecting top 5 items...")
    
    top_items = aggregator.get_top_items(items, n=5)
    
    print("Generating Turkish tweets with Gemini AI...\n")
    processed = await ai_processor.process_batch(top_items, max_items=5)
    
    # Prepare results
    results = []
    for i, item in enumerate(processed, 1):
        if item.processed:
            results.append({
                'id': i,
                'title': item.title,
                'url': item.url,
                'quality': str(item.quality),
                'relevance': item.relevance_score,
                'engagement': item.engagement_score,
                'summary': item.ai_summary,
                'tweet': item.suggested_tweet
            })
    
    # Save to JSON
    with open('all_tweets.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Display results
    print("\n" + "="*80)
    print(f"GENERATED {len(results)} TURKISH TWEETS")
    print("="*80 + "\n")
    
    for r in results:
        print(f"[{r['id']}] {r['title'][:70]}...")
        print(f"    Quality: {r['quality']} | Relevance: {r['relevance']:.2f} | Engagement: {r['engagement']:.2f}")
        print(f"    Summary: {r['summary']}")
        print(f"    Tweet: {r['tweet']}")
        print(f"    URL: {r['url']}")
        print()
    
    print("="*80)
    print(f"All {len(results)} tweets saved to: all_tweets.json")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
