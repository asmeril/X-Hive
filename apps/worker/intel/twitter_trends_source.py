"""
Twitter/X Trends Content Source

Fetches trending topics from Twitter/X.
"""

import aiohttp
import asyncio
import logging
from typing import List
from datetime import datetime, timezone
from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory,
)
from .cookie_manager import get_cookie_manager

logger = logging.getLogger(__name__)


class TwitterTrendsSource(BaseContentSource):
    """
    Twitter/X Trends aggregator.
    
    Fetches trending topics from Twitter.
    """
    
    def __init__(
        self,
        limit: int = 20
    ):
        super().__init__()
        self.cookie_manager = get_cookie_manager()
        self.limit = limit
        logger.info(f"✅ TwitterTrendsSource initialized (limit={limit})")
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "Twitter Trends"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch trending topics from Twitter/X"""
        
        items = []
        
        try:
            # Try API first
            items = await self._fetch_via_api()
            
            if not items:
                # Fallback to Playwright scraping
                logger.info("📡 API failed, trying Playwright scraping...")
                items = await self._fetch_via_playwright()
        
        except Exception as e:
            logger.error(f"❌ Error fetching Twitter Trends: {e}")
        
        return items
    
    async def _fetch_via_api(self) -> List[ContentItem]:
        """Fetch trends via Twitter API"""
        
        items = []
        
        try:
            # Get cookies
            cookies = self.cookie_manager.get_cookies_for_site_json('twitter')
            ct0_cookie = self.cookie_manager.get_twitter_ct0()
            
            if not cookies:
                logger.warning("⚠️  Twitter cookies not found, skipping")
                return []
            
            if not ct0_cookie:
                # Try to extract ct0 from JSON cookies
                ct0_cookie = cookies.get('ct0')
                if not ct0_cookie:
                    logger.warning("⚠️  Twitter ct0 token not found, skipping")
                    return []
            
            headers = {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                ),
                'Authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
                'x-csrf-token': ct0_cookie,
                'x-twitter-active-user': 'yes',
                'x-twitter-auth-type': 'OAuth2Session',
                'x-twitter-client-language': 'en',
            }
            
            # Twitter Trends API endpoint
            url = "https://api.twitter.com/2/guide.json?include_profile_interstitial_type=1&include_blocking=1&include_blocked_by=1&include_followed_by=1&include_want_retweets=1&include_mute_edge=1&include_can_dm=1&include_can_media_tag=1&include_ext_has_nft_avatar=1&skip_status=1&cards_platform=Web-12&include_cards=1&include_ext_alt_text=true&include_quote_count=true&include_reply_count=1&tweet_mode=extended&include_entities=true&include_user_entities=true&include_ext_media_color=true&include_ext_media_availability=true&send_error_codes=true&simple_quoted_tweet=true&count=20&candidate_source=trends&include_page_configuration=false&entity_tokens=false"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    cookies=cookies,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"⚠️  Twitter API returned {response.status}")
                        return []
                    
                    data = await response.json()
                    
                    # Parse trends from response
                    if 'timeline' in data and 'instructions' in data['timeline']:
                        for instruction in data['timeline']['instructions']:
                            if 'addEntries' in instruction:
                                for entry in instruction['addEntries'].get('entries', []):
                                    if 'content' in entry and 'item' in entry['content']:
                                        item_content = entry['content']['item']
                                        if 'clientEventInfo' in item_content:
                                            details = item_content['clientEventInfo'].get('details', {})
                                            trend_name = details.get('guideDetails', {}).get('transparentGuideDetails', {}).get('trendMetadata', {}).get('trendName')
                                            
                                            if trend_name:
                                                trend_url = f"https://twitter.com/search?q={trend_name.replace(' ', '+').replace('#', '%23')}"
                                                
                                                category = self._categorize_trend(trend_name)
                                                
                                                item = ContentItem(
                                                    title=trend_name,
                                                    url=trend_url,
                                                    source_type='twitter_trends',
                                                    source_name="Twitter Trends",
                                                    published_at=datetime.now(timezone.utc),
                                                    category=category,
                                                    description=f"Trending on Twitter: {trend_name}"
                                                )
                                                
                                                item.relevance_score = 0.85
                                                item.engagement_score = 0.8
                                                
                                                items.append(item)
                                                
                                                if len(items) >= self.limit:
                                                    break
            
            logger.info(f"✅ Twitter Trends API: Fetched {len(items)} trends")
        
        except Exception as e:
            logger.debug(f"⚠️  Twitter API failed: {e}")
        
        return items
    
    async def _fetch_via_playwright(self) -> List[ContentItem]:
        """Fetch trends via Playwright browser automation (fallback)"""
        
        items = []
        
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                # Load cookies
                playwright_cookies = self.cookie_manager.cookie_loader.get_playwright_cookies('twitter')
                if playwright_cookies:
                    await context.add_cookies(playwright_cookies)
                
                page = await context.new_page()
                
                try:
                    await page.goto('https://x.com/explore/tabs/trending', wait_until='networkidle', timeout=30000)
                    await page.wait_for_timeout(3000)
                    
                    # Extract trends from page
                    trends = await page.evaluate('''() => {
                        const trends = [];
                        const trendElements = document.querySelectorAll('[data-testid="trend"]');
                        
                        for (const el of trendElements) {
                            const textContent = el.innerText;
                            const lines = textContent.split('\\n');
                            
                            // Find the trend name (usually first non-numeric line)
                            for (const line of lines) {
                                if (line.trim() && 
                                    !line.match(/^[0-9,KM]+$/) && 
                                    !line.includes('Trending') && 
                                    !line.includes('posts')) {
                                    trends.push(line.trim());
                                    break;
                                }
                            }
                        }
                        
                        return [...new Set(trends)];
                    }''')
                    
                    if trends:
                        for idx, trend_name in enumerate(trends[:self.limit]):
                            trend_url = f"https://x.com/search?q={trend_name.replace(' ', '+').replace('#', '%23')}"
                            category = self._categorize_trend(trend_name)
                            
                            item = ContentItem(
                                title=trend_name,
                                url=trend_url,
                                source_type='twitter_trends',
                                source_name="Twitter Trends",
                                published_at=datetime.now(timezone.utc),
                                category=category,
                                description=f"Trending on Twitter: {trend_name}"
                            )
                            
                            item.relevance_score = 0.85 - (idx * 0.02)
                            item.engagement_score = 0.8
                            
                            items.append(item)
                        
                        logger.info(f"✅ Twitter Trends (Playwright): Fetched {len(items)} trends")
                    else:
                        logger.warning("⚠️  No trends found with Playwright")
                
                except Exception as e:
                    logger.warning(f"⚠️  Playwright page error: {e}")
                finally:
                    await context.close()
                    await browser.close()
        
        except ImportError:
            logger.warning("⚠️  Playwright not available")
        except Exception as e:
            logger.warning(f"⚠️  Playwright failed: {e}")
        
        return items
    
    def _categorize_trend(self, trend: str) -> ContentCategory:
        """Auto-categorize trend"""
        
        trend_lower = trend.lower()
        
        if any(kw in trend_lower for kw in ['ai', 'chatgpt', 'openai', 'ml', 'robot', 'gemini', 'llm']):
            return ContentCategory.AI_ML
        elif any(kw in trend_lower for kw in ['crypto', 'bitcoin', 'ethereum', 'nft']):
            return ContentCategory.CRYPTO_WEB3
        elif any(kw in trend_lower for kw in ['game', 'gaming', 'esports', 'twitch', 'ps5', 'xbox']):
            return ContentCategory.GAMING_ENTERTAINMENT
        elif any(kw in trend_lower for kw in ['iphone', 'android', 'app', 'mobile']):
            return ContentCategory.MOBILE_APPS
        elif any(kw in trend_lower for kw in ['hack', 'breach', 'security', 'privacy']):
            return ContentCategory.SECURITY_PRIVACY
        elif any(kw in trend_lower for kw in ['startup', 'ipo', 'funding', 'vc']):
            return ContentCategory.STARTUP_BUSINESS
        elif any(kw in trend_lower for kw in ['python', 'javascript', 'code', 'developer']):
            return ContentCategory.TECH_PROGRAMMING
        else:
            return ContentCategory.GENERAL_NEWS


# Export
twitter_trends_source = TwitterTrendsSource()
