"""Quick Twitter test - single influencer"""
import asyncio
from intel.twitter_source import TwitterSource
from intel.base_source import ContentCategory

async def main():
    # Test with just one influencer
    twitter = TwitterSource(
        influencers={'karpathy': ContentCategory.AI_ML},
        tweets_per_influencer=3
    )
    
    print(f"Testing Twitter with @karpathy...")
    items = await twitter.fetch_latest()
    
    print(f"\n✅ Result: {len(items)} tweets\n")
    
    for i, item in enumerate(items, 1):
        print(f"{i}. {item.title}")
        print(f"   URL: {item.url}")
        print(f"   Author: {item.author}")
        print(f"   Engagement: {item.engagement_score:.2f}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
