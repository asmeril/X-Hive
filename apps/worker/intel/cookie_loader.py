"""
Cookie Loader - Load cookies from EditThisCookie JSON exports

EditThisCookie exports cookies as JSON array format:
[
    {
        "domain": ".reddit.com",
        "name": "reddit_session",
        "value": "...",
        ...
    },
    ...
]
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import aiohttp

logger = logging.getLogger(__name__)


class CookieLoader:
    """
    Load cookies from EditThisCookie JSON exports.
    
    Supports loading browser cookies exported as JSON arrays
    and injecting them into HTTP requests.
    """
    
    def __init__(self, cookies_dir: Optional[Path] = None):
        """
        Initialize cookie loader.
        
        Args:
            cookies_dir: Directory containing cookie JSON files
        """
        if cookies_dir is None:
            cookies_dir = Path(__file__).parent.parent / 'cookies'
        
        self.cookies_dir = Path(cookies_dir)
        self.cookies_cache: Dict[str, List[dict]] = {}
        
        # Create cookies directory if doesn't exist
        self.cookies_dir.mkdir(exist_ok=True)
        
        logger.info(f"✅ CookieLoader initialized: {self.cookies_dir}")
    
    def load_cookies(self, site: str) -> List[dict]:
        """
        Load cookies for a site from JSON file.
        
        Args:
            site: Site name (e.g., 'reddit', 'twitter', 'medium')
        
        Returns:
            List of cookie dicts in EditThisCookie format
        """
        
        # Check cache
        if site in self.cookies_cache:
            return self.cookies_cache[site]
        
        # Load from file
        cookie_file = self.cookies_dir / f'{site}.json'
        
        if not cookie_file.exists():
            logger.warning(f"⚠️  Cookie file not found: {cookie_file}")
            return []
        
        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            # Validate format
            if not isinstance(cookies, list):
                logger.error(f"❌ Invalid cookie format in {cookie_file} (expected list)")
                return []
            
            # Cache
            self.cookies_cache[site] = cookies
            
            logger.info(f"✅ Loaded {len(cookies)} cookies for {site}")
            return cookies
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in {cookie_file}: {e}")
            return []
        
        except Exception as e:
            logger.error(f"❌ Error loading cookies for {site}: {e}")
            return []
    
    def get_cookie_dict(self, site: str) -> Dict[str, str]:
        """
        Get cookies as simple name->value dict for requests library.
        
        Args:
            site: Site name
        
        Returns:
            Dict of cookie name -> value
        """
        cookies = self.load_cookies(site)
        
        cookie_dict = {}
        for cookie in cookies:
            if 'name' in cookie and 'value' in cookie:
                cookie_dict[cookie['name']] = cookie['value']
        
        return cookie_dict
    
    def get_cookie_header(self, site: str) -> str:
        """
        Get cookies as Cookie header string.
        
        Args:
            site: Site name
        
        Returns:
            Cookie header value (e.g., "name1=value1; name2=value2")
        """
        cookie_dict = self.get_cookie_dict(site)
        
        if not cookie_dict:
            return ""
        
        return '; '.join(f'{name}={value}' for name, value in cookie_dict.items())
    
    def get_aiohttp_cookies(self, site: str) -> aiohttp.CookieJar:
        """
        Get cookies as aiohttp CookieJar.
        
        Args:
            site: Site name
        
        Returns:
            aiohttp.CookieJar with cookies
        """
        cookies = self.load_cookies(site)
        
        jar = aiohttp.CookieJar()
        
        for cookie in cookies:
            # Convert EditThisCookie format to aiohttp format
            try:
                # aiohttp needs at minimum: name, value, domain
                if 'name' in cookie and 'value' in cookie and 'domain' in cookie:
                    jar.update_cookies({
                        cookie['name']: cookie['value']
                    })
            except Exception as e:
                logger.debug(f"Error adding cookie: {e}")
                continue
        
        return jar
    
    def create_session_with_cookies(self, site: str) -> aiohttp.ClientSession:
        """
        Create aiohttp session with cookies pre-loaded.
        
        Args:
            site: Site name
        
        Returns:
            aiohttp.ClientSession with cookies
        """
        jar = self.get_aiohttp_cookies(site)
        
        return aiohttp.ClientSession(cookie_jar=jar)
    
    def get_playwright_cookies(self, site: str) -> List[dict]:
        """
        Get cookies in Playwright format for browser automation.
        
        Args:
            site: Site name
        
        Returns:
            List of cookie dicts in Playwright format
        """
        cookies = self.load_cookies(site)
        
        playwright_cookies = []
        for cookie in cookies:
            try:
                pw_cookie = {
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    'domain': cookie.get('domain'),
                    'path': cookie.get('path', '/'),
                }
                
                # Optional fields
                if 'expires' in cookie or 'expirationDate' in cookie:
                    pw_cookie['expires'] = cookie.get('expires') or cookie.get('expirationDate')
                
                if 'httpOnly' in cookie:
                    pw_cookie['httpOnly'] = cookie.get('httpOnly')
                
                if 'secure' in cookie:
                    pw_cookie['secure'] = cookie.get('secure')
                
                if 'sameSite' in cookie:
                    sameSite = cookie.get('sameSite')
                    if sameSite in ['Strict', 'Lax', 'None']:
                        pw_cookie['sameSite'] = sameSite
                
                playwright_cookies.append(pw_cookie)
            
            except Exception as e:
                logger.debug(f"Error converting cookie to Playwright format: {e}")
                continue
        
        return playwright_cookies


# Global instance
_cookie_loader = None


def get_cookie_loader() -> CookieLoader:
    """Get global cookie loader instance"""
    global _cookie_loader
    
    if _cookie_loader is None:
        _cookie_loader = CookieLoader()
    
    return _cookie_loader
