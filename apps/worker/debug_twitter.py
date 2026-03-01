"""Debug Twitter Playwright"""
import asyncio
import logging
from intel.twitter_source import TwitterSource
from intel.base_source import ContentCategory

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

async def main():
    twitter = TwitterSource(
        influencers={'karpathy': ContentCategory.AI_ML},
        tweets_per_influencer=3
    )
    
    print("Testing @karpathy with Playwright...")
    items = await twitter.fetch_latest()
    
    print(f"\nResult: {len(items)} tweets")
    
    if items:
        for item in items[:2]:
            print(f"\n{item.title}")
            print(f"URL: {item.url}")

if __name__ == "__main__":
    asyncio.run(main())
