"""
X-Hive Cookie Manager

Centralized cookie management for all content sources.

Manages authentication cookies for:
- Reddit (reddit_session)
- Twitter/X (auth_token, ct0)
- Medium (sid)
- LinkedIn (li_at)
- YouTube (SAPISID)
- GitHub (user_session)
- Product Hunt (_producthunt_session)
- Substack (substack.sid)
- Arxiv (optional auth)

Usage:
    from intel.cookie_manager import get_cookie_manager
    
    cm = get_cookie_manager()
    headers = cm.get_headers_for_reddit()
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv
import logging
from .cookie_loader import get_cookie_loader

logger = logging.getLogger(__name__)

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class CookieManager:
    """
    Centralized cookie management for all content sources.
    
    Manages authentication cookies for:
    - Reddit (reddit_session)
    - Twitter/X (auth_token, ct0)
    - Medium (sid)
    - LinkedIn (li_at)
    - YouTube (SAPISID)
    - GitHub (user_session)
    - Product Hunt (_producthunt_session)
    - Substack (substack.sid)
    - Arxiv (optional auth)
    """
    
    def __init__(self):
        """Initialize cookie manager and load cookies from environment"""
        
        # Initialize cookie loader for JSON cookies
        self.cookie_loader = get_cookie_loader()
        
        # Load all cookies from environment
        self.cookies = {
            'reddit': os.getenv('REDDIT_COOKIE'),
            'twitter': os.getenv('TWITTER_COOKIE'),
            'twitter_ct0': os.getenv('TWITTER_CT0'),
            'medium': os.getenv('MEDIUM_COOKIE'),
            'linkedin': os.getenv('LINKEDIN_COOKIE'),
            'youtube': os.getenv('YOUTUBE_SAPISID'),
            'github': os.getenv('GITHUB_USER_SESSION'),
            'producthunt': os.getenv('PRODUCTHUNT_COOKIE'),
            'substack': os.getenv('SUBSTACK_COOKIE'),
            'arxiv': os.getenv('ARXIV_COOKIE'),
        }
        
        # Log which cookies are available
        available = [k for k, v in self.cookies.items() if v]
        missing = [k for k, v in self.cookies.items() if not v]
        
        if available:
            logger.info(f"✅ Cookies loaded from .env: {', '.join(available)}")
        
        if missing:
            logger.debug(f"⚠️  Missing .env cookies: {', '.join(missing)}")
    
    def get_reddit_cookie(self) -> Optional[str]:
        """Get Reddit session cookie (primary auth)"""
        return self.cookies.get('reddit')

    def get_reddit_token_v2(self) -> Optional[str]:
        """Get Reddit token_v2 (access token)"""
        return os.getenv('REDDIT_TOKEN_V2')

    def get_reddit_csrf(self) -> Optional[str]:
        """Get Reddit CSRF token"""
        return os.getenv('REDDIT_CSRF')
    
    def get_twitter_cookie(self) -> Optional[str]:
        """Get Twitter auth token"""
        return self.cookies.get('twitter')
    
    def get_twitter_ct0(self) -> Optional[str]:
        """Get Twitter CSRF token"""
        return self.cookies.get('twitter_ct0')
    
    def get_medium_cookie(self) -> Optional[str]:
        """Get Medium session cookie"""
        return self.cookies.get('medium')
    
    def get_linkedin_cookie(self) -> Optional[str]:
        """Get LinkedIn auth cookie"""
        return self.cookies.get('linkedin')
    
    def get_youtube_cookie(self) -> Optional[str]:
        """Get YouTube SAPISID cookie"""
        return self.cookies.get('youtube')
    
    def get_github_cookie(self) -> Optional[str]:
        """Get GitHub user session cookie"""
        return self.cookies.get('github')
    
    def get_producthunt_cookie(self) -> Optional[str]:
        """Get Product Hunt session cookie"""
        return self.cookies.get('producthunt')
    
    def get_substack_cookie(self) -> Optional[str]:
        """Get Substack session cookie"""
        return self.cookies.get('substack')
    
    def get_cookies_for_site_json(self, site: str) -> Optional[Dict[str, str]]:
        """
        Get cookies from JSON file (EditThisCookie export).
        
        Falls back to .env cookies if JSON not found.
        
        Args:
            site: Site name (reddit, twitter, medium, etc)
        
        Returns:
            Dict of cookie name -> value, or None if no cookies
        """
        json_cookies = self.cookie_loader.get_cookie_dict(site)
        
        if json_cookies:
            logger.info(f"✅ Using JSON cookies for {site} ({len(json_cookies)} cookies)")
            return json_cookies
        
        # Fallback to env-based single cookie
        env_cookie = self.cookies.get(site)
        if env_cookie:
            logger.debug(f"⚠️  Falling back to .env cookie for {site}")
            return {site: env_cookie}
        
        return None
    
    def get_headers_for_site(self, site: str) -> Dict[str, str]:
        """
        Get HTTP headers for any site with JSON cookie support.
        
        Attempts to use JSON cookies first, falls back to .env.
        
        Args:
            site: Site name (reddit, twitter, medium, etc)
        
        Returns:
            Headers dict with User-Agent and Cookie header
        """
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'DNT': '1',
        }
        
        cookies_dict = self.get_cookies_for_site_json(site)
        
        if cookies_dict:
            cookie_header = '; '.join(f'{k}={v}' for k, v in cookies_dict.items())
            headers['Cookie'] = cookie_header
        
        return headers
    
    def get_headers_for_reddit(self) -> Dict[str, str]:
        """
        Get HTTP headers with Reddit cookies.
        
        Returns:
            Headers dict with multiple Reddit cookies
        """
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
        
        cookie_parts = []
        
        session = self.get_reddit_cookie()
        if session:
            cookie_parts.append(f'reddit_session={session}')
        
        csrf = self.get_reddit_csrf()
        if csrf:
            cookie_parts.append(f'csrf_token={csrf}')
        
        loid = os.getenv('REDDIT_LOID')
        if loid:
            cookie_parts.append(f'loid={loid}')
        
        if cookie_parts:
            headers['Cookie'] = '; '.join(cookie_parts)
        
        if csrf:
            headers['X-CSRF-Token'] = csrf
        
        return headers
    
    def get_headers_for_twitter(self) -> Dict[str, str]:
        """
        Get HTTP headers with Twitter cookies.
        
        Returns:
            Headers dict with auth_token and ct0
        """
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'x-twitter-active-user': 'yes',
            'x-twitter-client-language': 'en',
        }
        
        cookie_parts = []
        
        auth_token = self.get_twitter_cookie()
        if auth_token:
            cookie_parts.append(f'auth_token={auth_token}')
        
        ct0 = self.get_twitter_ct0()
        if ct0:
            cookie_parts.append(f'ct0={ct0}')
            headers['x-csrf-token'] = ct0
        
        if cookie_parts:
            headers['Cookie'] = '; '.join(cookie_parts)
        
        return headers
    
    def get_headers_for_medium(self) -> Dict[str, str]:
        """
        Get HTTP headers with Medium cookie.
        
        Returns:
            Headers dict
        """
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml',
        }
        
        cookie = self.get_medium_cookie()
        if cookie:
            headers['Cookie'] = f'sid={cookie}'
        
        return headers
    
    def get_headers_for_linkedin(self) -> Dict[str, str]:
        """
        Get HTTP headers with LinkedIn cookie.
        
        Returns:
            Headers dict
        """
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36'
            ),
            'Accept': 'text/html',
        }
        
        cookie = self.get_linkedin_cookie()
        if cookie:
            headers['Cookie'] = f'li_at={cookie}'
        
        return headers
    
    def validate_cookie(self, platform: str) -> bool:
        """
        Check if cookie for platform exists and is not empty.
        
        Args:
            platform: Platform name (reddit, twitter, medium, etc)
        
        Returns:
            True if cookie exists and looks valid
        """
        cookie = self.cookies.get(platform)
        return bool(cookie and len(cookie) > 10)


# Global singleton
_cookie_manager = None


def get_cookie_manager() -> CookieManager:
    """Get global cookie manager instance"""
    global _cookie_manager
    
    if _cookie_manager is None:
        _cookie_manager = CookieManager()
    
    return _cookie_manager
