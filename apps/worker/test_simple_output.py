"""
Simple test to see AI-generated tweets - Plain text output only
"""
import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from intel.aggregator import aggregator
from intel.ai_processor import ai_processor

async def main():
    print("Fetching content...")
    items = await aggregator.fetch_all()
    
    print(f"Got {len(items)} items")
    
    # Get top 3 items
    top_items = aggregator.get_top_items(items, n=3)
    
    print("\nProcessing with AI...")
    processed = await ai_processor.process_batch(top_items, max_items=3)
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    for i, item in enumerate(processed, 1):
        print(f"\n[{i}] {item.title[:60]}...")
        print(f"    URL: {item.url}")
        print(f"    Processed: {item.processed}")
        if item.processed:
            print(f"    Quality: {item.quality}")
            # Print tweet in ASCII-safe way
            tweet = item.suggested_tweet.encode('ascii', 'replace').decode('ascii')
            summary = item.ai_summary.encode('ascii', 'replace').decode('ascii')
            print(f"    Summary: {summary}")
            print(f"    Tweet: {tweet}")
    
    print("\n" + "="*80)
    print(f"Successfully processed: {sum(1 for item in processed if item.processed)}/{len(processed)}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
