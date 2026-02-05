"""
Show AI-generated tweets in JSON format
"""
import asyncio
import sys
import json
import logging
from pathlib import Path

# Disable logging
logging.basicConfig(level=logging.CRITICAL)
for logger_name in logging.root.manager.loggerDict:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

sys.path.insert(0, str(Path(__file__).parent))

from intel.aggregator import aggregator
from intel.ai_processor import ai_processor

async def main():
    # Fetch
    items = await aggregator.fetch_all()
    top_items = aggregator.get_top_items(items, n=3)
    
    # Process
    processed = await ai_processor.process_batch(top_items, max_items=3)
    
    # Convert to JSON
    results = []
    for item in processed:
        if item.processed:
            results.append({
                'title': item.title,
                'url': item.url,
                'quality': str(item.quality),
                'summary': item.ai_summary,
                'tweet': item.suggested_tweet,
                'relevance': item.relevance_score,
                'engagement': item.engagement_score
            })
    
    # Save to JSON file
    output_file = Path(__file__).parent / 'tweets_output.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Results saved to: {output_file}")
    print(f"Total tweets generated: {len(results)}")

if __name__ == "__main__":
    asyncio.run(main())
