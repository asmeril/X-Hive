#!/usr/bin/env python
"""
X-Hive Phase 1 - Comprehensive Test Suite
Tests all 9 content sources with JSON cookie support
"""

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import all available sources
from intel.hackernews_source import HackerNewsSource
from intel.reddit_source import RedditSource
from intel.twitter_source import TwitterSource
from intel.arxiv_source import ArxivSource
from intel.producthunt_source import ProductHuntSource
from intel.google_trends_source import GoogleTrendsSource
from intel.github_source import GitHubSource
from intel.substack_scraper import SubstackScraper
from intel.medium_scraper import MediumScraper
from intel.perplexity_scraper import PerplexityScraper
from intel.youtube_source import YouTubeSource
from intel.linkedin_source import LinkedInSource


async def test_all_sources():
    """Test all 11 content sources"""
    
    print("\n" + "=" * 80)
    print("[TEST] PHASE 1 COMPREHENSIVE TEST - ALL 11 SOURCES")
    print("=" * 80 + "\n")
    
    # Initialize all sources
    sources = [
        (HackerNewsSource(), "Hacker News"),
        (RedditSource(), "Reddit"),
        (TwitterSource(), "Twitter/X"),
        (ArxivSource(), "ArXiv"),
        (ProductHuntSource(), "Product Hunt"),
        (GoogleTrendsSource(), "Google Trends"),
        (SubstackScraper(), "Substack"),
        (MediumScraper(), "Medium"),
        (PerplexityScraper(), "Perplexity"),
        (YouTubeSource(), "YouTube"),
        (LinkedInSource(), "LinkedIn"),
        (GitHubSource(), "GitHub"),
    ]
    
    results = {}
    total_items = 0
    
    # Test each source
    for source, source_name in sources:
        print("=" * 80)
        print(f"[TEST] Testing: {source_name}")
        print("=" * 80 + "\n")
        
        try:
            items = await source.fetch_latest()
            results[source_name] = {
                'status': 'PASS',
                'items': len(items),
                'error': None
            }
            total_items += len(items)
            
            # Print sample
            if items:
                sample = items[0]
                print(f"[OK] {source_name}: Fetched {len(items)} items")
                print(f"   Sample: {sample.title[:50]}...")
                print(f"   Category: {sample.category}")
                print(f"   URL: {sample.url[:60]}...")
            else:
                print(f"[WARNING] {source_name}: Fetched 0 items")
            
        except Exception as e:
            results[source_name] = {
                'status': 'ERROR',
                'items': 0,
                'error': str(e)
            }
            print(f"[ERROR] {source_name}: {e}")
        
        print()
    
    # Print summary
    print("=" * 80)
    print("[SUMMARY] PHASE 1 COMPREHENSIVE TEST SUMMARY")
    print("=" * 80 + "\n")
    
    print(f"Sources Tested: {len(sources)}")
    passed = sum(1 for r in results.values() if r['status'] == 'PASS')
    print(f"Successful: {passed}/{len(sources)}")
    print(f"Total Items Fetched: {total_items}\n")
    
    print("Per-Source Results:")
    print("-" * 80)
    
    for source_name, result in results.items():
        status_icon = "[OK]" if result['status'] == 'PASS' else "[ERROR]"
        items = result['items']
        print(f"{source_name:25} {status_icon:8} {result['status']:8} {items:3} items")
    
    print("-" * 80)
    
    print("\n" + "=" * 80)
    if passed == len(sources):
        print("[OK] ALL PHASE 1 SOURCES WORKING!")
    else:
        print(f"[WARNING] {len(sources) - passed} sources failed")
    print("=" * 80 + "\n")
    
    return results


if __name__ == "__main__":
    # Run async test
    results = asyncio.run(test_all_sources())
    
    # Print final statistics
    print("\n" + "=" * 80)
    print("FINAL STATISTICS")
    print("=" * 80)
    
    passed = sum(1 for r in results.values() if r['status'] == 'PASS')
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"Sources Tested: {total}")
    print(f"Successful: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Total Items: {sum(r['items'] for r in results.values())}")
    print("=" * 80 + "\n")
