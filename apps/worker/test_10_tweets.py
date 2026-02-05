"""
Generate 10 tweets to show system capabilities
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
    print("📡 Fetching trending AI/Tech content...")
    items = await aggregator.fetch_all()
    
    print(f"✅ Found {len(items)} items")
    print("🎯 Selecting top 10 items for tweet generation...")
    
    top_items = aggregator.get_top_items(items, n=10)
    
    print("🤖 Generating Turkish tweets with Gemini AI (this may take ~30 seconds)...\n")
    processed = await ai_processor.process_batch(top_items, max_items=10)
    
    # Collect results
    results = []
    high_quality = []
    medium_quality = []
    
    for i, item in enumerate(processed, 1):
        if item.processed:
            tweet_data = {
                'id': i,
                'title': item.title,
                'url': item.url,
                'quality': str(item.quality),
                'relevance': item.relevance_score,
                'engagement': item.engagement_score,
                'summary': item.ai_summary,
                'tweet': item.suggested_tweet,
                'category': str(item.category)
            }
            results.append(tweet_data)
            
            if 'HIGH' in str(item.quality):
                high_quality.append(tweet_data)
            elif 'MEDIUM' in str(item.quality):
                medium_quality.append(tweet_data)
    
    # Save all tweets
    with open('full_tweets.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Display summary
    print("\n" + "="*80)
    print(f"✅ SUCCESSFULLY GENERATED {len(results)} TURKISH TWEETS")
    print("="*80)
    print(f"\n📊 Quality Distribution:")
    print(f"   🌟 HIGH Quality: {len(high_quality)} tweets")
    print(f"   ⭐ MEDIUM Quality: {len(medium_quality)} tweets")
    print(f"   💾 Saved to: full_tweets.json")
    print("\n" + "="*80)
    
    # Show first 3 as preview
    print("\n🎬 PREVIEW - First 3 Tweets:")
    print("="*80 + "\n")
    
    for tweet in results[:3]:
        print(f"[{tweet['id']}] {tweet['title'][:65]}...")
        print(f"    Quality: {tweet['quality']}")
        print(f"    Tweet: {tweet['tweet']}")
        print(f"    URL: {tweet['url']}\n")
    
    if len(results) > 3:
        print(f"... and {len(results) - 3} more tweets in full_tweets.json")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(main())
