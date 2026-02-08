"""
X-Hive Auto Cookie Extractor

Interactive tool to extract authentication cookies from multiple platforms.

Opens browser for each platform, waits for manual login,
then automatically extracts cookies and saves to .env file.

Usage:
    python tools/cookie_extractor.py
    
    Or from apps/worker directory:
    python -m tools.cookie_extractor
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import os
from typing import Dict, Optional, List
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CookieExtractor:
    """
    Interactive cookie extraction tool.
    
    Opens browser for each platform, waits for user to login,
    then extracts and saves cookies automatically.
    """
    
    PLATFORMS = {
        'reddit': {
            'name': 'Reddit',
            'url': 'https://old.reddit.com',
            'cookie_names': ['reddit_session'],
            'login_url': 'https://old.reddit.com/login',
            'success_indicator': 'preferences',
            'instructions': (
                "1. Click 'Log in' button (top right)\n"
                "2. Enter username and password\n"
                "3. Click 'Log in'\n"
                "4. Wait for homepage to load\n"
                "5. Browser will auto-close when cookie is captured"
            )
        },
        'twitter': {
            'name': 'Twitter/X',
            'url': 'https://twitter.com',
            'cookie_names': ['auth_token', 'ct0'],
            'login_url': 'https://twitter.com/i/flow/login',
            'success_indicator': 'home',
            'instructions': (
                "1. Enter phone/email/username\n"
                "2. Click 'Next'\n"
                "3. Enter password\n"
                "4. Click 'Log in'\n"
                "5. Complete any verification if prompted\n"
                "6. Wait for home feed to load\n"
                "7. Browser will auto-close when cookies are captured"
            )
        },
        'medium': {
            'name': 'Medium',
            'url': 'https://medium.com',
            'cookie_names': ['sid'],
            'login_url': 'https://medium.com/m/signin',
            'success_indicator': 'medium.com',
            'instructions': (
                "1. Click 'Sign in' or 'Get started'\n"
                "2. Sign in with Google or Email\n"
                "3. Complete authentication\n"
                "4. Wait for homepage to load\n"
                "5. Browser will auto-close when cookie is captured"
            )
        },
        'substack': {
            'name': 'Substack',
            'url': 'https://substack.com',
            'cookie_names': ['substack.sid'],
            'login_url': 'https://substack.com/sign-in',
            'success_indicator': 'substack.com',
            'instructions': (
                "1. Click 'Sign in'\n"
                "2. Enter your email\n"
                "3. Click 'Continue'\n"
                "4. Check your email for magic link\n"
                "5. Click the link in email\n"
                "6. Wait for homepage to load\n"
                "7. Browser will auto-close when cookie is captured"
            )
        },
    }
    
    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize cookie extractor.
        
        Args:
            env_path: Path to .env file (default: apps/worker/.env)
        """
        if env_path is None:
            env_path = Path(__file__).parent.parent / '.env'
        
        self.env_path = env_path
        self.extracted_cookies: Dict[str, Dict[str, str]] = {}
        
        # Create .env if doesn't exist
        if not self.env_path.exists():
            self.env_path.parent.mkdir(parents=True, exist_ok=True)
            self.env_path.touch()
    
    async def extract_all(self, platforms: Optional[List[str]] = None):
        """
        Extract cookies from selected platforms interactively.
        
        Args:
            platforms: List of platform keys to extract (default: all)
        """
        
        if platforms is None:
            platforms = list(self.PLATFORMS.keys())
        
        print("\n" + "="*80)
        print("🍪 X-HIVE AUTO COOKIE EXTRACTOR")
        print("="*80)
        print("\nThis tool will extract authentication cookies from:")
        for platform in platforms:
            print(f"  • {self.PLATFORMS[platform]['name']}")
        print("\n" + "="*80)
        print("\n⚠️  IMPORTANT:")
        print("  - Use throwaway/secondary accounts (not your main accounts)")
        print("  - Cookies will be saved to .env file")
        print("  - Keep .env file private (never commit to git)")
        print("\n" + "="*80 + "\n")
        
        input("Press ENTER to start...")
        
        async with async_playwright() as p:
            for platform_key in platforms:
                await self._extract_platform(p, platform_key)
        
        # Save to .env
        self._save_to_env()
        
        # Summary
        self._print_summary()
    
    async def _extract_platform(self, playwright, platform_key: str):
        """
        Extract cookies from a single platform.
        
        Args:
            playwright: Playwright instance
            platform_key: Platform key (e.g., 'reddit', 'twitter')
        """
        
        platform = self.PLATFORMS[platform_key]
        
        print("\n" + "="*80)
        print(f"🌐 PLATFORM: {platform['name']}")
        print("="*80 + "\n")
        
        print("📋 Instructions:")
        print(platform['instructions'])
        print("\n" + "-"*80 + "\n")
        
        input(f"Press ENTER to open {platform['name']} browser...")
        
        # Launch browser (visible so user can login)
        logger.info(f"Launching browser for {platform['name']}...")
        browser = await playwright.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        # Navigate to login page
        logger.info(f"Opening {platform['login_url']}...")
        await page.goto(platform['login_url'], wait_until='networkidle')
        
        print(f"\n✋ Browser opened! Please login to {platform['name']}...")
        print("⏳ Waiting for you to complete login (up to 5 minutes)...\n")
        
        # Wait for user to login
        # We'll check for cookies periodically
        success = False
        
        for attempt in range(60):  # Check every 5 seconds for 5 minutes
            await asyncio.sleep(5)
            
            # Get current cookies
            cookies = await context.cookies()
            
            # Check if we have the required cookies
            found_cookies = {}
            for cookie in cookies:
                if cookie['name'] in platform['cookie_names']:
                    found_cookies[cookie['name']] = cookie['value']
            
            if len(found_cookies) >= len(platform['cookie_names']):
                success = True
                self.extracted_cookies[platform_key] = found_cookies
                logger.info(f"✅ Cookies detected for {platform['name']}!")
                break
        
        if success:
            print(f"\n✅ Successfully extracted {len(found_cookies)} cookie(s) from {platform['name']}:")
            for cookie_name in found_cookies.keys():
                print(f"   • {cookie_name}")
        else:
            print(f"\n⚠️  Could not detect cookies for {platform['name']}")
            print(f"   Expected cookies: {', '.join(platform['cookie_names'])}")
            print(f"   Make sure you're fully logged in!")
        
        # Close browser
        await browser.close()
        
        print(f"\n✅ {platform['name']} complete!\n")
    
    def _save_to_env(self):
        """Save extracted cookies to .env file"""
        
        print("\n" + "="*80)
        print("💾 SAVING COOKIES TO .env")
        print("="*80 + "\n")
        
        # Read existing .env
        env_lines = []
        if self.env_path.exists():
            with open(self.env_path, 'r', encoding='utf-8') as f:
                env_lines = f.readlines()
        
        # Remove existing cookie lines
        cookie_keys = [
            'REDDIT_COOKIE', 'TWITTER_COOKIE', 'TWITTER_CT0',
            'MEDIUM_COOKIE', 'SUBSTACK_COOKIE'
        ]
        
        env_lines = [
            line for line in env_lines
            if not any(line.startswith(key + '=') for key in cookie_keys)
        ]
        
        # Add/find cookie section
        cookie_section_exists = any('# === COOKIES ===' in line for line in env_lines)
        
        if not cookie_section_exists:
            env_lines.insert(0, '\n# === COOKIES ===\n\n')
        
        # Find insertion point (after COOKIES header)
        insert_idx = 0
        for i, line in enumerate(env_lines):
            if '# === COOKIES ===' in line:
                insert_idx = i + 1
                break
        
        # Build new cookie lines
        new_lines = []
        
        # Reddit
        if 'reddit' in self.extracted_cookies:
            reddit = self.extracted_cookies['reddit']
            if 'reddit_session' in reddit:
                new_lines.append(f"REDDIT_COOKIE={reddit['reddit_session']}\n")
        
        # Twitter
        if 'twitter' in self.extracted_cookies:
            twitter = self.extracted_cookies['twitter']
            if 'auth_token' in twitter:
                new_lines.append(f"TWITTER_COOKIE={twitter['auth_token']}\n")
            if 'ct0' in twitter:
                new_lines.append(f"TWITTER_CT0={twitter['ct0']}\n")
        
        # Medium
        if 'medium' in self.extracted_cookies:
            medium = self.extracted_cookies['medium']
            if 'sid' in medium:
                new_lines.append(f"MEDIUM_COOKIE={medium['sid']}\n")
        
        # Substack
        if 'substack' in self.extracted_cookies:
            substack = self.extracted_cookies['substack']
            if 'substack.sid' in substack:
                new_lines.append(f"SUBSTACK_COOKIE={substack['substack.sid']}\n")
        
        # Insert new lines
        env_lines[insert_idx:insert_idx] = new_lines
        
        # Write back
        with open(self.env_path, 'w', encoding='utf-8') as f:
            f.writelines(env_lines)
        
        print(f"✅ Saved {len(new_lines)} cookie(s) to: {self.env_path}")
        print()
    
    def _print_summary(self):
        """Print extraction summary"""
        
        print("\n" + "="*80)
        print("📊 EXTRACTION SUMMARY")
        print("="*80 + "\n")
        
        if not self.extracted_cookies:
            print("⚠️  No cookies were extracted!")
            print("\nPossible reasons:")
            print("  - Login was not completed")
            print("  - Wrong credentials")
            print("  - Browser closed too early")
            print("\nTry running the tool again.")
        else:
            for platform_key, cookies in self.extracted_cookies.items():
                platform_name = self.PLATFORMS[platform_key]['name']
                print(f"✅ {platform_name:20s}: {len(cookies)} cookie(s)")
                for cookie_name in cookies.keys():
                    print(f"   • {cookie_name}")
            
            print("\n" + "="*80)
            print("✅ COOKIE EXTRACTION COMPLETE!")
            print("="*80 + "\n")
            
            print("🔄 Next steps:")
            print("  1. Verify cookies in .env file")
            print("  2. Run: python -c \"from intel.cookie_manager import get_cookie_manager; get_cookie_manager()\"")
            print("  3. Run: python test_batch1_sources.py")
            print()


async def main():
    """Main entry point"""
    
    print("\n🍪 X-Hive Cookie Extractor\n")
    print("Select platforms to extract cookies from:")
    print("  1. Essential (Reddit + Twitter) - Recommended for Phase 1")
    print("  2. All available platforms")
    print("  3. Custom selection")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    
    extractor = CookieExtractor()
    
    if choice == '1':
        # Essential: Reddit + Twitter
        print("\n✅ Extracting essential cookies (Reddit + Twitter)")
        await extractor.extract_all(platforms=['reddit', 'twitter'])
    
    elif choice == '2':
        # All platforms
        print("\n✅ Extracting all available platform cookies")
        await extractor.extract_all()
    
    elif choice == '3':
        # Custom selection
        print("\nAvailable platforms:")
        platform_list = list(CookieExtractor.PLATFORMS.items())
        for i, (key, platform) in enumerate(platform_list, 1):
            print(f"  {i}. {platform['name']}")
        
        print("\nEnter platform numbers separated by commas (e.g., 1,2,4):")
        selection = input("> ").strip()
        
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            platforms = [platform_list[i][0] for i in indices]
            
            print(f"\n✅ Extracting cookies for: {', '.join(platforms)}")
            await extractor.extract_all(platforms=platforms)
        
        except (ValueError, IndexError):
            print("\n❌ Invalid selection!")
            return
    
    else:
        print("\n❌ Invalid choice!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Extraction cancelled by user")
