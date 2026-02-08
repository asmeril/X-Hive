"""
Test Cookie Manager

Validates that cookie manager correctly:
1. Loads from .env
2. Provides headers for platforms
3. Validates cookie existence
"""

import logging
from intel.cookie_manager import get_cookie_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_cookie_manager():
    """Test cookie manager functionality"""
    
    print("\n" + "="*70)
    print("🍪 TESTING COOKIE MANAGER")
    print("="*70 + "\n")
    
    # Get cookie manager
    cm = get_cookie_manager()
    
    # Test platform validation
    platforms = ['reddit', 'twitter', 'medium', 'substack']
    
    print("📋 Cookie Status:\n")
    
    available = []
    missing = []
    
    for platform in platforms:
        is_valid = cm.validate_cookie(platform)
        status = "✅" if is_valid else "❌"
        print(f"  {status} {platform:15s}: {'Available' if is_valid else 'Missing'}")
        
        if is_valid:
            available.append(platform)
        else:
            missing.append(platform)
    
    print("\n" + "-"*70 + "\n")
    
    # Test header generation
    print("🔧 Testing Header Generation:\n")
    
    if cm.validate_cookie('reddit'):
        headers = cm.get_headers_for_reddit()
        print(f"  ✅ Reddit headers: {len(headers)} keys")
        print(f"     - User-Agent: {headers.get('User-Agent', 'N/A')[:50]}...")
        if 'Cookie' in headers:
            print(f"     - Cookie: reddit_session=***{headers['Cookie'][-20:]}")
    else:
        print("  ⚠️  Reddit: No cookie - using unauthenticated headers")
        headers = cm.get_headers_for_reddit()
        print(f"     - User-Agent: {headers.get('User-Agent', 'N/A')[:50]}...")
    
    print()
    
    if cm.validate_cookie('twitter'):
        headers = cm.get_headers_for_twitter()
        print(f"  ✅ Twitter headers: {len(headers)} keys")
        print(f"     - User-Agent: {headers.get('User-Agent', 'N/A')[:50]}...")
        if 'Cookie' in headers:
            print(f"     - Cookie: auth_token=***...")
        if 'x-csrf-token' in headers:
            print(f"     - CSRF Token: Present")
    else:
        print("  ⚠️  Twitter: No cookie - using unauthenticated headers")
    
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70 + "\n")
    
    print(f"Available cookies: {len(available)}")
    for p in available:
        print(f"  ✅ {p}")
    
    print(f"\nMissing cookies: {len(missing)}")
    for p in missing:
        print(f"  ❌ {p}")
    
    if missing:
        print("\n⚠️  To extract missing cookies, run:")
        print("   python tools/cookie_extractor.py")
    else:
        print("\n✅ All cookies available!")
    
    print()


if __name__ == "__main__":
    test_cookie_manager()
