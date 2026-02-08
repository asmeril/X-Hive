"""
Comprehensive Test Script for Batch 1 Content Sources

Tests all 5 API-based content sources:
1. Reddit (PRAW API)
2. Hacker News (Official API)
3. ArXiv (Research Papers API)
4. Product Hunt (GraphQL API)
5. Google Trends (pytrends)
"""

import asyncio
import logging
import sys
from datetime import datetime
from collections import Counter
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import all Batch 1 sources
try:
    from intel.reddit_source import reddit_source
    from intel.hackernews_source import hackernews_source
    from intel.arxiv_source import arxiv_source
    from intel.producthunt_source import producthunt_source
    from intel.google_trends_source import google_trends_source
        from intel.twitter_source import twitter_source
    from intel.base_source import ContentCategory, CATEGORY_TARGETS
except ImportError as e:
    print(f"❌ Failed to import sources: {e}")
    sys.exit(1)


async def test_source(source, source_name: str):
    """
    Test a single content source.
    
    Args:
        source: Content source instance
        source_name: Human-readable source name
        
    Returns:
        dict with test results
    """
    
    print(f"\n{'='*80}")
    print(f"🧪 TESTING: {source_name}")
    print('='*80 + "\n")
    
    results = {
        'source': source_name,
        'success': False,
        'items_count': 0,
        'categories': {},
        'avg_relevance': 0.0,
        'avg_engagement': 0.0,
        'max_relevance': 0.0,
        'min_relevance': 1.0,
        'max_engagement': 0.0,
        'min_engagement': 1.0,
        'errors': [],
        'elapsed_time': 0.0
    }
    
    try:
        # Fetch content
        print(f"📡 Fetching content from {source_name}...")
        start_time = datetime.now()
        
        items = await source.fetch_latest()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        results['elapsed_time'] = elapsed
        
        if not items:
            print(f"⚠️  No items fetched from {source_name}")
            results['errors'].append("No items returned")
            return results
        
        # Count items
        results['items_count'] = len(items)
        print(f"✅ Fetched {len(items)} items in {elapsed:.2f}s\n")
        
        # Analyze categories
        categories = Counter(item.category for item in items)
        results['categories'] = {cat.value: count for cat, count in categories.items()}
        
        print("📊 Category Distribution:")
        for category, count in categories.most_common():
            percentage = (count / len(items)) * 100
            bar = '█' * int(percentage / 5)
            print(f"   {category.value:25s}: {count:3d} ({percentage:5.1f}%) {bar}")
        
        # Calculate average scores
        relevance_scores = [item.relevance_score for item in items if item.relevance_score is not None]
        engagement_scores = [item.engagement_score for item in items if item.engagement_score is not None]
        
        if relevance_scores:
            results['avg_relevance'] = sum(relevance_scores) / len(relevance_scores)
            results['max_relevance'] = max(relevance_scores)
            results['min_relevance'] = min(relevance_scores)
            print(f"\n⭐ Relevance Scores:")
            print(f"   Average: {results['avg_relevance']:.2f}")
            print(f"   Range:   {results['min_relevance']:.2f} - {results['max_relevance']:.2f}")
        
        if engagement_scores:
            results['avg_engagement'] = sum(engagement_scores) / len(engagement_scores)
            results['max_engagement'] = max(engagement_scores)
            results['min_engagement'] = min(engagement_scores)
            print(f"\n💬 Engagement Scores:")
            print(f"   Average: {results['avg_engagement']:.2f}")
            print(f"   Range:   {results['min_engagement']:.2f} - {results['max_engagement']:.2f}")
        
        # Validate data quality
        print(f"\n✔️  Data Quality Checks:")
        
        # Check all items have required fields
        required_fields = ['title', 'url', 'source_type', 'source_name', 'category']
        missing_count = 0
        
        for item in items:
            for field in required_fields:
                if not getattr(item, field, None):
                    missing_count += 1
        
        if missing_count == 0:
            print(f"   All items have required fields ✅")
        else:
            print(f"   ⚠️  {missing_count} missing field(s) across items")
            results['errors'].append(f"{missing_count} items missing required fields")
        
        # Check URL validity
        invalid_urls = sum(1 for item in items if not item.url or not item.url.startswith(('http://', 'https://')))
        if invalid_urls == 0:
            print(f"   All URLs are valid ✅")
        else:
            print(f"   ⚠️  {invalid_urls} invalid URL(s)")
            results['errors'].append(f"{invalid_urls} invalid URLs")
        
        # Check category validity
        valid_categories = set(cat.value for cat in ContentCategory)
        invalid_categories = sum(1 for item in items if item.category.value not in valid_categories)
        if invalid_categories == 0:
            print(f"   All categories are valid ✅")
        else:
            print(f"   ⚠️  {invalid_categories} invalid category(ies)")
            results['errors'].append(f"{invalid_categories} invalid categories")
        
        # Show sample items
        print(f"\n📋 Sample Items (first 3):\n")
        for i, item in enumerate(items[:3], 1):
            print(f"{i}. {item.title[:65]}...")
            print(f"   Category: {item.category.value:20s} | Source: {item.source_name}")
            print(f"   Scores: Relevance={item.relevance_score:.2f}, Engagement={item.engagement_score:.2f}")
            print(f"   URL: {item.url[:70]}{'...' if len(item.url) > 70 else ''}")
            if item.author:
                print(f"   Author: {item.author}")
            if item.published_at:
                print(f"   Published: {item.published_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
        
        results['success'] = True
        print(f"✅ {source_name} test PASSED!\n")
    
    except Exception as e:
        logger.error(f"❌ {source_name} test FAILED: {e}", exc_info=True)
        results['errors'].append(str(e))
        print(f"❌ {source_name} test FAILED: {e}\n")
    
    return results


async def test_all_sources():
    """
    Test all Batch 1 sources.
    """
    
    print("\n" + "="*80)
    print("X-HIVE PHASE 1 - BATCH 1: API-BASED SOURCES TEST")
    print("="*80)
    print("\nTesting 5 content sources:\n")
    print("  1️⃣  Reddit          (PRAW API) - 20 subreddits")
    print("  2️⃣  Hacker News     (Official API) - top/new/best stories")
    print("  3️⃣  ArXiv           (Research API) - AI/ML/Science papers")
    print("  4️⃣  Product Hunt    (GraphQL API) - daily products")
    print("  5️⃣  Google Trends   (pytrends) - trending searches")
    print("\nTarget Distribution:")
    print("  🤖 AI/ML (30%)  💻 Tech (20%)  🚀 Startup (15%)  🎮 Gaming (10%)")
    print("  💰 Crypto (10%)  📱 Mobile (5%)  🔒 Security (5%)  🌍 Science (5%)")
    print("\n" + "="*80 + "\n")
    
    # Test each source
    sources = [
        (reddit_source, "Reddit"),
        (hackernews_source, "Hacker News"),
        (arxiv_source, "ArXiv"),
        (producthunt_source, "Product Hunt"),
        (google_trends_source, "Google Trends"),
        (twitter_source, "Twitter/X"),
    ]
    
    all_results = []
    
    for source, name in sources:
        result = await test_source(source, name)
        all_results.append(result)
    
    # Summary Report
    print("\n" + "="*80)
    print("📊 BATCH 1 TEST SUMMARY")
    print("="*80 + "\n")
    
    total_items = sum(r['items_count'] for r in all_results)
    successful = sum(1 for r in all_results if r['success'])
    total_time = sum(r['elapsed_time'] for r in all_results)
    
    print(f"Test Execution:")
    print(f"  Sources Tested:     {len(sources)}")
    print(f"  Successful:         {successful}/{len(sources)}")
    print(f"  Total Time:         {total_time:.2f}s")
    print(f"  Total Items:        {total_items}")
    print(f"  Average per source: {total_items/len(sources) if sources else 0:.1f}")
    print()
    
    # Per-source summary
    print("Per-Source Results:")
    print("-" * 80)
    print(f"{'Source':<20} {'Status':<12} {'Items':<8} {'Relevance':<12} {'Engagement':<12} {'Time':<8}")
    print("-" * 80)
    
    for result in all_results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        rel_str = f"{result['avg_relevance']:.2f}" if result['avg_relevance'] > 0 else "N/A"
        eng_str = f"{result['avg_engagement']:.2f}" if result['avg_engagement'] > 0 else "N/A"
        time_str = f"{result['elapsed_time']:.1f}s"
        
        print(f"{result['source']:<20} {status:<12} {result['items_count']:<8} {rel_str:<12} {eng_str:<12} {time_str:<8}")
        
        if result['errors']:
            for error in result['errors']:
                print(f"  ⚠️  {error}")
    
    # Overall category distribution
    print(f"\n📊 Overall Category Distribution:")
    print("-" * 80)
    
    all_categories = Counter()
    for result in all_results:
        for cat, count in result['categories'].items():
            all_categories[cat] += count
    
    if all_categories:
        for category, count in all_categories.most_common():
            percentage = (count / total_items) * 100 if total_items > 0 else 0
            bar = '█' * int(percentage / 5)
            print(f"{category:25s}: {count:4d} ({percentage:5.1f}%) {bar}")
    
    # Quality metrics
    print(f"\n⭐ Quality Metrics:")
    print("-" * 80)
    
    valid_results = [r for r in all_results if r['success']]
    
    if valid_results:
        avg_relevance = sum(r['avg_relevance'] for r in valid_results if r['avg_relevance']) / len(valid_results)
        avg_engagement = sum(r['avg_engagement'] for r in valid_results if r['avg_engagement']) / len(valid_results)
        
        print(f"Average Relevance Score:    {avg_relevance:.3f} (0.0-1.0)")
        print(f"Average Engagement Score:   {avg_engagement:.3f} (0.0-1.0)")
        
        if avg_relevance >= 0.7:
            print(f"  ✅ Relevance score is good (>= 0.7)")
        elif avg_relevance >= 0.5:
            print(f"  ⚠️  Relevance score is acceptable (>= 0.5)")
        else:
            print(f"  ❌ Relevance score is low (< 0.5)")
        
        if avg_engagement >= 0.6:
            print(f"  ✅ Engagement score is good (>= 0.6)")
        elif avg_engagement >= 0.4:
            print(f"  ⚠️  Engagement score is acceptable (>= 0.4)")
        else:
            print(f"  ❌ Engagement score is low (< 0.4)")
    
    # Category target comparison
    print(f"\n🎯 Category Target vs Actual:")
    print("-" * 80)
    print(f"{'Category':<25} {'Target':<12} {'Actual':<12} {'Difference':<12} {'Status':<8}")
    print("-" * 80)
    
    category_diffs = []
    
    for category_enum in ContentCategory:
        category_name = category_enum.value
        target_pct = CATEGORY_TARGETS.get(category_enum, 0) * 100
        actual_count = all_categories.get(category_name, 0)
        actual_pct = (actual_count / total_items) * 100 if total_items > 0 else 0
        diff = actual_pct - target_pct
        
        status = "✅" if abs(diff) < 10 else "⚠️" if abs(diff) < 15 else "❌"
        
        category_diffs.append((category_name, target_pct, actual_pct, diff, status))
        
        print(f"{category_name:<25} {target_pct:>5.1f}%      {actual_pct:>5.1f}%      {diff:>+5.1f}%       {status}")
    
    # Balance assessment
    print(f"\n📈 Distribution Balance:")
    
    acceptable_diffs = sum(1 for _, _, _, diff, status in category_diffs if status != "❌")
    
    if acceptable_diffs == len(ContentCategory):
        print(f"  ✅ Excellent! All categories within acceptable range")
    elif acceptable_diffs >= len(ContentCategory) - 2:
        print(f"  ✅ Good! Most categories within acceptable range")
    else:
        print(f"  ⚠️  {len(ContentCategory) - acceptable_diffs} category(ies) need adjustment")
    
    # Data completeness
    print(f"\n📋 Data Completeness:")
    print("-" * 80)
    
    total_errors = sum(len(r['errors']) for r in all_results)
    
    if total_errors == 0:
        print(f"  ✅ All data quality checks passed!")
    else:
        print(f"  ⚠️  {total_errors} data quality issue(s) found")
        for result in all_results:
            if result['errors']:
                print(f"     {result['source']}: {', '.join(result['errors'])}")
    
    # Final result
    print("\n" + "="*80)
    
    if successful == len(sources) and total_errors == 0:
        print("✅ BATCH 1: ALL TESTS PASSED!")
        print("="*80)
        print("\n🚀 Ready for production! Next: Batch 2 (Twitter/X Sources)")
        status_code = 0
    elif successful >= 3:
        print(f"⚠️  BATCH 1: {successful}/{len(sources)} sources working")
        print("="*80)
        print(f"\n📋 Action Required: Configure remaining {len(sources)-successful} source(s)")
        print("   Check .env file for missing credentials:")
        for result in all_results:
            if not result['success']:
                print(f"   - {result['source']}")
        status_code = 1
    else:
        print("❌ BATCH 1: CRITICAL FAILURE - Most sources not working")
        print("="*80)
        print("\n🔧 Action Required: Review error messages above")
        status_code = 2
    
    print("\n📝 Next Steps:")
    print("  1. Review test results above")
    print("  2. Fix any failed sources")
    print("  3. Adjust category distribution if needed")
    print("  4. Proceed to Batch 2: Twitter/X Hybrid Sources")
    print()
    
    return status_code


async def main():
    """Main entry point"""
    try:
        status_code = await test_all_sources()
        return status_code
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
