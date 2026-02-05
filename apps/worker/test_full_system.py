#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
X-Hive Full System Integration Test

End-to-end test: Intel gathering → AI processing → Ready to post

Demonstrates complete workflow:
1. Fetch content from multiple sources (RSS, GitHub, Telegram)
2. Aggregate and filter by relevance/recency
3. Process with AI to generate Turkish tweets
4. Quality assessment and filtering
5. Select best tweets for posting
"""

import asyncio
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, '.')

from intel.aggregator import aggregator
from intel.ai_processor import ai_processor
from intel.base_source import ContentQuality


async def test_full_system():
    """
    Full X-Hive system test: Intel gathering -> AI processing -> Tweet ready
    
    Flow:
    1. Fetch content from all sources (RSS + GitHub + Telegram)
    2. Aggregate and filter
    3. Process with AI (Turkish tweets)
    4. Select best tweets for posting
    5. Show ready-to-post content
    """
    
    print("\n" + "="*80)
    print("X-HIVE FULL SYSTEM TEST")
    print("Intelligence Gathering -> AI Processing -> Ready to Post")
    print("="*80 + "\n")
    
    # ========================================
    # PHASE 1: INTEL GATHERING
    # ========================================
    
    print("[1] INTEL GATHERING")
    print("-" * 80)
    
    logger.info("Fetching content from all sources...")
    
    try:
        items = await aggregator.fetch_all()
    except Exception as e:
        logger.error(f"Failed to fetch content: {e}")
        print(f"\n[ERROR] Content fetching failed: {e}")
        return False
    
    if not items:
        print("\n[ERROR] No items fetched from sources")
        return False
    
    print(f"\n[OK] Collected {len(items)} items from all sources\n")
    
    # Show stats
    try:
        stats = aggregator.get_stats(items)
        
        print("[STATS] Content Statistics:")
        print(f"        Total items: {stats['total_items']}")
        print(f"        Avg relevance: {stats['avg_relevance']:.2f}")
        print(f"        Avg engagement: {stats['avg_engagement']:.2f}")
        
        print(f"\n[SOURCES]")
        for source, count in stats['sources'].items():
            print(f"        {source}: {count} items")
        
        print(f"\n[CATEGORIES]")
        for category, count in stats['categories'].items():
            print(f"        {category}: {count} items")
    except Exception as e:
        logger.warning(f"Failed to get stats: {e}")
    
    print()
    
    # ========================================
    # PHASE 2: CONTENT SELECTION
    # ========================================
    
    print("[2] CONTENT SELECTION")
    print("-" * 80)
    
    # Get top 5 items
    top_items = aggregator.get_top_items(items, n=5)
    
    print(f"\n[OK] Top {len(top_items)} items selected for AI processing:\n")
    
    for i, item in enumerate(top_items, 1):
        title = item.title[:70] if len(item.title) > 70 else item.title
        print(f"{i}. {title}")
        print(f"   Source: {item.source_name} | Category: {item.category.name}")
        print(f"   Scores: Relevance={item.relevance_score:.2f}, Engagement={item.engagement_score:.2f}")
        print()
    
    # ========================================
    # PHASE 3: AI PROCESSING
    # ========================================
    
    print("[3] AI PROCESSING")
    print("-" * 80)
    
    if not ai_processor or not ai_processor.client:
        print("\n[WARN] AI processor not available (missing GEMINI_API_KEY)")
        print("       Skipping AI processing phase")
        print("       (Set GEMINI_API_KEY in .env to enable)\n")
        return True
    
    print("[AI] Generating Turkish tweets with Gemini...\n")
    
    try:
        processed = await ai_processor.process_batch(top_items, max_items=5)
    except Exception as e:
        logger.error(f"Failed to process items: {e}")
        print(f"\n[ERROR] AI processing failed: {e}")
        return False
    
    successful = [p for p in processed if p.processed]
    failed = [p for p in processed if not p.processed]
    
    print(f"[OK] Successfully processed: {len(successful)}/{len(processed)}")
    
    if failed:
        print(f"[WARN] Failed: {len(failed)}")
    
    print()
    
    # ========================================
    # PHASE 4: QUALITY FILTERING
    # ========================================
    
    print("[4] QUALITY FILTERING")
    print("-" * 80)
    
    high_quality = ai_processor.filter_by_quality(successful, ContentQuality.HIGH)
    medium_quality = ai_processor.filter_by_quality(successful, ContentQuality.MEDIUM)
    
    print(f"\n[STATS] HIGH quality: {len(high_quality)} tweets")
    print(f"        MEDIUM quality: {len(medium_quality)} tweets")
    print(f"        Total postable: {len(high_quality) + len(medium_quality)} tweets\n")
    
    # ========================================
    # PHASE 5: READY TO POST
    # ========================================
    
    print("[5] READY TO POST")
    print("=" * 80)
    
    postable = high_quality + medium_quality
    
    if not postable:
        print("\n[WARN] No high-quality tweets generated")
        print("       Try with valid GEMINI_API_KEY\n")
        return True
    
    for i, item in enumerate(postable, 1):
        print(f"\n{'='*80}")
        print(f"TWEET #{i} - Quality: {item.quality.name if item.quality else 'N/A'}")
        print(f"{'='*80}")
        
        print(f"\n[SOURCE]")
        title = item.title[:80] if len(item.title) > 80 else item.title
        print(f"   {title}")
        print(f"   {item.source_name} ({item.source_type})")
        
        print(f"\n[READY TO POST]")
        print(f"\n{'-'*80}")
        if item.suggested_tweet:
            print(item.suggested_tweet)
        print(item.url)
        print(f"{'-'*80}")
        
        if item.suggested_tweet:
            tweet_length = len(item.suggested_tweet) + len(item.url) + 1
            print(f"\n[LENGTH] {tweet_length}/280 chars")
        
        print(f"[QUALITY] {item.quality.name if item.quality else 'N/A'}")
        print(f"[SCORES] Relevance: {item.relevance_score:.2f} | Engagement: {item.engagement_score:.2f}")
    
    # ========================================
    # PHASE 6: BEST TWEET RECOMMENDATION
    # ========================================
    
    print(f"\n{'='*80}")
    print("BEST TWEET TO POST NOW")
    print(f"{'='*80}\n")
    
    best = postable[0]
    
    if best.suggested_tweet:
        print(best.suggested_tweet)
    print(best.url)
    
    print(f"\n[QUALITY] {best.quality.name if best.quality else 'N/A'}")
    combined_score = best.relevance_score * 0.6 + best.engagement_score * 0.4
    print(f"[SCORE] Combined: {combined_score:.2f}")
    print(f"[CATEGORY] {best.category.name}")
    print(f"[SOURCE] {best.source_name}")
    
    # ========================================
    # SUMMARY
    # ========================================
    
    print(f"\n{'='*80}")
    print("FULL SYSTEM TEST COMPLETE")
    print(f"{'='*80}\n")
    
    print("[SUMMARY]")
    print(f"   Content fetched: {len(items)} items")
    print(f"   AI processed: {len(successful)} items")
    print(f"   Ready to post: {len(postable)} tweets")
    print(f"   Recommended: 1 best tweet")
    
    print("\n[INFO] X-Hive is ready for production!")
    print("       Next: Integrate with PostScheduler and Twitter API\n")
    
    return True


async def main():
    """Run full system test"""
    try:
        result = await test_full_system()
        return 0 if result else 1
    except KeyboardInterrupt:
        print("\n\n[WARN] Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
