"""
Batch 1 Sources - Quick Test Runner

Simple script to quickly validate all sources are working.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def quick_test():
    """Quick validation of all sources"""
    
    print("\n🚀 Quick Batch 1 Sources Test\n")
    
    sources = [
        ('intel.reddit_source', 'reddit_source', 'Reddit'),
        ('intel.hackernews_source', 'hackernews_source', 'Hacker News'),
        ('intel.arxiv_source', 'arxiv_source', 'ArXiv'),
        ('intel.producthunt_source', 'producthunt_source', 'Product Hunt'),
        ('intel.google_trends_source', 'google_trends_source', 'Google Trends'),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, var_name, display_name in sources:
        try:
            module = __import__(module_name, fromlist=[var_name])
            source = getattr(module, var_name)
            
            print(f"Testing {display_name}...", end=' ')
            items = await source.fetch_latest()
            
            if items:
                print(f"✅ {len(items)} items")
                passed += 1
            else:
                print("⚠️  No items")
                failed += 1
                
        except Exception as e:
            print(f"❌ {str(e)[:50]}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All sources working!")
        return 0
    elif passed >= 3:
        print("⚠️  Most sources working")
        return 1
    else:
        print("❌ Multiple sources failed")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(quick_test())
    sys.exit(exit_code)
