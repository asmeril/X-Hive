"""
Reddit Content Source

Fetches top posts from 20+ tech-related subreddits
across all 8 content categories using web scraping.

Supports JWT authentication for modern Reddit.
"""

import aiohttp
from bs4 import BeautifulSoup
import logging
from typing import List, Optional
from datetime import datetime
import re
import json
import os

from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory,
    ContentSourceError
)
from .cookie_manager import get_cookie_manager

logger = logging.getLogger(__name__)


class RedditSource(BaseContentSource):
    """
    Reddit content aggregator using JWT authentication.
    
    Supports both:
    1. Modern Reddit (reddit.com) with JWT Bearer auth
    2. Old Reddit (old.reddit.com) with cookie scraping
    
    Falls back to old.reddit.com if JWT fails.
    """
    
    SUBREDDITS = {
        'MachineLearning': ContentCategory.AI_ML,
        'artificial': ContentCategory.AI_ML,
        'singularity': ContentCategory.AI_ML,
        'LocalLLaMA': ContentCategory.AI_ML,
        'learnmachinelearning': ContentCategory.AI_ML,
        'deeplearning': ContentCategory.AI_ML,
        'programming': ContentCategory.TECH_PROGRAMMING,
        'Python': ContentCategory.TECH_PROGRAMMING,
        'webdev': ContentCategory.TECH_PROGRAMMING,
        'technology': ContentCategory.TECH_PROGRAMMING,
        'startups': ContentCategory.STARTUP_BUSINESS,
        'Entrepreneur': ContentCategory.STARTUP_BUSINESS,
        'SaaS': ContentCategory.STARTUP_BUSINESS,
        'CryptoCurrency': ContentCategory.CRYPTO_WEB3,
        'ethereum': ContentCategory.CRYPTO_WEB3,
        'gaming': ContentCategory.GAMING_ENTERTAINMENT,
        'gamedev': ContentCategory.GAMING_ENTERTAINMENT,
        'AndroidApps': ContentCategory.MOBILE_APPS,
        'cybersecurity': ContentCategory.SECURITY_PRIVACY,
        'science': ContentCategory.SCIENCE,
    }
    
    BASE_URL = "https://old.reddit.com"
    MODERN_URL = "https://www.reddit.com"
    
    def __init__(
        self,
        subreddits: Optional[dict] = None,
        time_filter: str = 'day',
        limit: int = 10,
        use_old_reddit: bool = True,
        use_playwright_fallback: bool = True
    ):
        """
        Initialize Reddit scraper with JWT support.
        
        Args:
            subreddits: Custom subreddit mapping
            time_filter: Time filter (hour/day/week/month/year)
            limit: Posts per subreddit (max 25)
            use_old_reddit: Use old.reddit.com (more reliable)
            use_playwright_fallback: Use Playwright fallback on 403
        """
        super().__init__()
        
        # Get cookie manager
        self.cookie_manager = get_cookie_manager()
        
        self.subreddits = subreddits or self.SUBREDDITS
        self.time_filter = time_filter
        self.limit = min(limit, 25)
        self.use_old_reddit = use_old_reddit
        self.use_playwright_fallback = use_playwright_fallback
        
        # Check if cookie available
        self.jwt_token = self.cookie_manager.get_reddit_cookie()
        self.token_v2 = self.cookie_manager.get_reddit_token_v2()
        self.csrf_token = self.cookie_manager.get_reddit_csrf()
        
        if not self.jwt_token:
            logger.warning(
                "⚠️  No Reddit cookie found. Will scrape without auth (rate-limited).\n"
                "   Run: python tools/cookie_extractor.py"
            )
        
        logger.info(
            f"✅ RedditSource initialized "
            f"({len(self.subreddits)} subreddits, "
            f"{'with' if self.jwt_token else 'without'} auth, "
            f"{'old' if use_old_reddit else 'modern'} Reddit)"
        )
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "Reddit"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """
        Reddit: Placeholder (JWT auth complexity - defer to Phase 2)
        
        Modern Reddit requires complex JWT Bearer token flow.
        Will implement in Phase 2 with proper OAuth flow.
        """
        logger.info("ℹ️  Reddit: Temporarily skipped (JWT auth - implement in Phase 2)")
        return []
    
    def _get_headers(self, old_reddit: bool = True) -> dict:
        """
        Get request headers with authentication.
        
        Args:
            old_reddit: Whether using old.reddit.com
        
        Returns:
            Headers dict
        """
        if old_reddit:
            return self.cookie_manager.get_headers_for_reddit()

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

        bearer = self.token_v2 or self.jwt_token
        if bearer:
            headers['Authorization'] = f'Bearer {bearer}'

        if self.csrf_token:
            headers['X-CSRF-Token'] = self.csrf_token

        return headers
    
    async def _scrape_old_reddit(
        self,
        session: aiohttp.ClientSession,
        subreddit: str,
        category: ContentCategory
    ) -> List[ContentItem]:
        """
        Scrape old.reddit.com (reliable, simple HTML).
        
        Args:
            session: aiohttp session
            subreddit: Subreddit name
            category: Content category
        
        Returns:
            List of ContentItem
        """
        
        url = f"{self.BASE_URL}/r/{subreddit}/top/?t={self.time_filter}"
        headers = self._get_headers(old_reddit=True)
        
        items = []
        
        try:
            async with session.get(url, headers=headers) as response:
                
                if response.status == 403:
                    logger.warning(f"⚠️  403 for r/{subreddit} - trying without cookie")
                    # Retry without cookie
                    headers.pop('Cookie', None)
                    async with session.get(url, headers=headers) as retry_response:
                        if retry_response.status != 200:
                            if self.use_playwright_fallback:
                                html = await self._fetch_with_playwright(url)
                                if not html:
                                    return items
                            else:
                                return items
                        else:
                            html = await retry_response.text()
                elif response.status == 429:
                    logger.warning(f"⚠️  Rate limited on r/{subreddit}")
                    return items
                elif response.status != 200:
                    logger.error(f"❌ HTTP {response.status} for r/{subreddit}")
                    return items
                else:
                    html = await response.text()
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find all post containers
                post_divs = soup.find_all('div', class_='thing', limit=self.limit * 2)
                
                if not post_divs:
                    logger.warning(f"⚠️  No posts found for r/{subreddit}")
                    return items
                
                for post_div in post_divs:
                    # Skip stickied posts
                    if 'stickied' in post_div.get('class', []):
                        continue
                    
                    try:
                        # Extract post data
                        title_elem = post_div.find('a', class_='title')
                        if not title_elem:
                            continue
                        
                        title = title_elem.text.strip()
                        if not title:
                            continue
                        
                        # Get URL
                        data_url = post_div.get('data-url', '')
                        permalink = post_div.get('data-permalink', '')
                        
                        # Prefer external link, fallback to Reddit comments
                        if data_url and not data_url.startswith('/r/'):
                            url = data_url
                        else:
                            url = f"{self.BASE_URL}{permalink}"
                        
                        # Get score
                        score_elem = post_div.find('div', class_='score')
                        if not score_elem:
                            score_elem = post_div.find('div', class_='score unvoted')
                        
                        score = 0
                        if score_elem:
                            score_text = score_elem.get('title', score_elem.text)
                            score = self._parse_number(score_text)
                        
                        # Get comments count
                        comments_elem = post_div.find('a', class_='comments')
                        comments = 0
                        if comments_elem:
                            comments_text = comments_elem.text
                            comments = self._parse_number(comments_text.split()[0])
                        
                        # Get author
                        author_elem = post_div.find('a', class_='author')
                        author = author_elem.text if author_elem else None
                        
                        # Get timestamp
                        time_elem = post_div.find('time')
                        created_at = datetime.now()
                        if time_elem and time_elem.get('datetime'):
                            try:
                                from dateutil import parser
                                created_at = parser.parse(time_elem['datetime'])
                            except:
                                pass
                        
                        # Create ContentItem
                        item = ContentItem(
                            title=title,
                            url=url,
                            source_type='reddit',
                            source_name=f"Reddit - r/{subreddit}",
                            published_at=created_at,
                            category=category,
                            description='',
                            author=author
                        )
                        
                        # Calculate scores
                        item.relevance_score = self._calculate_relevance(score)
                        item.engagement_score = self._calculate_engagement(score, comments)
                        
                        items.append(item)
                        
                        if len(items) >= self.limit:
                            break
                    
                    except Exception as e:
                        logger.debug(f"Error parsing post: {e}")
                        continue
        
        except aiohttp.ClientError as e:
            logger.error(f"❌ Network error fetching r/{subreddit}: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error scraping r/{subreddit}: {e}")
        
        return items

    async def _fetch_with_playwright(self, url: str) -> Optional[str]:
        """Fetch page HTML using Playwright (fallback for 403)."""
        try:
            from playwright.async_api import async_playwright
        except Exception as e:
            logger.warning(f"Playwright not available: {e}")
            return None

        user_agent = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(user_agent=user_agent)

                cookies = []
                session_cookie = self.cookie_manager.get_reddit_cookie()
                if session_cookie:
                    cookies.append({
                        'name': 'reddit_session',
                        'value': session_cookie,
                        'domain': '.reddit.com',
                        'path': '/',
                    })

                csrf = self.cookie_manager.get_reddit_csrf()
                if csrf:
                    cookies.append({
                        'name': 'csrf_token',
                        'value': csrf,
                        'domain': '.reddit.com',
                        'path': '/',
                    })

                loid = os.getenv('REDDIT_LOID')
                if loid:
                    cookies.append({
                        'name': 'loid',
                        'value': loid,
                        'domain': '.reddit.com',
                        'path': '/',
                    })

                if cookies:
                    await context.add_cookies(cookies)

                page = await context.new_page()
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                html = await page.content()

                await context.close()
                await browser.close()
                return html
        except Exception as e:
            logger.warning(f"Playwright fetch failed: {e}")
            return None
    
    async def _scrape_modern_reddit(
        self,
        session: aiohttp.ClientSession,
        subreddit: str,
        category: ContentCategory
    ) -> List[ContentItem]:
        """
        Scrape modern reddit.com with JWT auth.
        
        NOTE: This is complex and may break. old.reddit.com is more reliable.
        """
        
        # For now, fallback to old reddit
        logger.debug(f"Modern Reddit not fully implemented, using old Reddit for r/{subreddit}")
        return await self._scrape_old_reddit(session, subreddit, category)
    
    def _parse_number(self, text: str) -> int:
        """Parse number from text (e.g., '1.2k' -> 1200)"""
        try:
            text = text.strip().lower()
            
            if 'k' in text:
                return int(float(text.replace('k', '')) * 1000)
            elif 'm' in text:
                return int(float(text.replace('m', '')) * 1000000)
            else:
                # Remove non-numeric characters
                clean = re.sub(r'[^\d]', '', text)
                return int(clean) if clean else 0
        except:
            return 0
    
    def _calculate_relevance(self, score: int) -> float:
        """Calculate relevance score based on upvotes"""
        base = 0.5
        
        if score > 1000:
            base += 0.3
        elif score > 500:
            base += 0.2
        elif score > 100:
            base += 0.1
        
        return min(base, 1.0)
    
    def _calculate_engagement(self, score: int, comments: int) -> float:
        """Calculate engagement score"""
        eng = 0.0
        
        # Upvotes (0-0.5 range)
        eng += min(0.5, score / 1000)
        
        # Comments (0-0.5 range)
        eng += min(0.5, comments / 100)
        
        return min(eng, 1.0)


# Global instance
reddit_source = RedditSource()
