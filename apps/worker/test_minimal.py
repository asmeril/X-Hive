"""
Minimal test - just show the tweets
"""
import asyncio
import sys
import logging
from pathlib import Path

# Disable all logging
logging.basicConfig(level=logging.CRITICAL)
for logger_name in logging.root.manager.loggerDict:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

sys.path.insert(0, str(Path(__file__).parent))

from intel.aggregator import aggregator
from intel.ai_processor import ai_processor

async def main():
    # Fetch
    items = await aggregator.fetch_all()
    top_items = aggregator.get_top_items(items, n=2)
    
    # Process
    processed = await ai_processor.process_batch(top_items, max_items=2)
    
    # Results
    print("="*80)
    for i, item in enumerate(processed, 1):
        if item.processed:
            print(f"\n[{i}] TITLE: {item.title[:70]}")
            print(f"URL: {item.url}")
            print(f"QUALITY: {item.quality}")
            # Use only ASCII
            summary = repr(item.ai_summary)[1:-1]
            tweet = repr(item.suggested_tweet)[1:-1]
            print(f"SUMMARY: {summary}")
            print(f"TWEET: {tweet}")
    print("\n" + "="*80)
    print(f"SUCCESS: {sum(1 for x in processed if x.processed)}/{len(processed)}")

if __name__ == "__main__":
    asyncio.run(main())
