"""
Google Trends Content Source

Fetches trending searches from Google Trends.
"""

import aiohttp
import feedparser
from pytrends.request import TrendReq
import asyncio
import logging
from typing import List, Optional
from datetime import datetime, timezone
from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory,
    ContentSourceError,
    CATEGORY_TARGETS
)
from .cookie_manager import get_cookie_manager

logger = logging.getLogger(__name__)


class GoogleTrendsSource(BaseContentSource):
    """
    Google Trends aggregator.
    
    Fetches trending searches.
    """
    
    def __init__(
        self,
        geo: Optional[str] = None,
        geos: Optional[List[str]] = None,
        limit: int = 20
    ):
        super().__init__()
        self.cookie_manager = get_cookie_manager()
        if geos:
            self.geos = geos
        elif geo:
            self.geos = [geo]
        else:
            self.geos = ['TR', 'US', 'JP', 'CN', 'GB', 'DE']
        self.limit = limit
        
        # Initialize pytrends with proper configuration
        try:
            self.pytrends = TrendReq(
                hl='en-US',
                tz=360,
                timeout=(10, 25)
            )
            logger.info(f"✅ GoogleTrendsSource initialized (geos={self.geos}, limit={limit})")
        except Exception as e:
            logger.error(f"❌ Error initializing pytrends: {e}")
            self.pytrends = None
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "Google Trends"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch trending searches from Google Trends"""
        
        if not self.pytrends:
            logger.error("❌ Google Trends: pytrends not initialized")
            return []
        
        items = []
        
        try:
            # Fetch trending searches (synchronous call, run in executor)
            loop = asyncio.get_event_loop()
            
            pn_map = {
                'US': 'united_states',
                'TR': 'turkey',
                'JP': 'japan',
                'CN': 'china',
                'GB': 'united_kingdom',
                'DE': 'germany'
            }

            seen = set()

            for geo in self.geos:
                pn = pn_map.get(geo.upper(), 'united_states')
                trends_list = []

                try:
                    if hasattr(self.pytrends, 'daily_trends'):
                        trends_data = await loop.run_in_executor(
                            None,
                            lambda: self.pytrends.daily_trends(geo=geo.upper())
                        )
                    elif hasattr(self.pytrends, 'today_searches'):
                        trends_data = await loop.run_in_executor(
                            None,
                            lambda: self.pytrends.today_searches(pn=pn)
                        )
                    else:
                        trends_data = await loop.run_in_executor(
                            None,
                            lambda: self.pytrends.trending_searches(pn=pn)
                        )

                    if trends_data is None:
                        logger.warning(f"⚠️  No trends data for {geo}")
                    elif hasattr(trends_data, 'empty') and trends_data.empty:
                        logger.warning(f"⚠️  No trends found for {geo}")
                    elif hasattr(trends_data, 'columns'):
                        if 'trend' in trends_data.columns:
                            trends_list = list(trends_data['trend'])
                        elif len(trends_data.columns) > 0:
                            trends_list = list(trends_data[trends_data.columns[0]])
                    elif isinstance(trends_data, list):
                        trends_list = trends_data
                    elif hasattr(trends_data, 'tolist'):
                        trends_list = trends_data.tolist()
                except Exception as e:
                    logger.warning(f"⚠️  Pytrends failed for {geo}, trying RSS: {e}")

                if not trends_list:
                    trends_list = await self._fetch_rss_trends(geo)

                if not trends_list:
                    logger.warning(f"⚠️  No trend entries for {geo}")
                    continue

                # Process trends
                for idx, trend in enumerate(trends_list[:self.limit]):
                    if not trend or len(str(trend)) < 2:
                        continue

                    trend_text = str(trend)
                    if trend_text.lower() in seen:
                        continue
                    seen.add(trend_text.lower())

                    # Create search URL
                    search_url = f"https://www.google.com/search?q={trend_text.replace(' ', '+')}"

                    # Auto-categorize
                    category = self._categorize_trend(trend_text)

                    item = ContentItem(
                        title=trend_text,
                        url=search_url,
                        source_type='google_trends',
                        source_name=f"Google Trends - {geo.upper()}",
                        published_at=datetime.now(timezone.utc),
                        category=category,
                        description=f"Trending search ({geo.upper()}): {trend_text}"
                    )

                    item.relevance_score = 0.8 - (idx * 0.02)  # Decay by rank
                    item.engagement_score = 0.75

                    items.append(item)
            
            logger.info(f"✅ Google Trends: Fetched {len(items)} trends")
        
        except Exception as e:
            logger.error(f"❌ Error fetching Google Trends: {e}")
        
        return items

    async def _fetch_rss_trends(self, geo: str) -> List[str]:
        """
        Fetch trending searches via multiple methods:
        1. Daily trends JSON API
        2. Realtime trends JSON API  
        3. Playwright browser automation (fallback)
        """
        
        # Method 1: Daily trends JSON endpoint
        trends = await self._fetch_json_endpoint(
            f"https://trends.google.com/trends/api/dailytrends?hl=en-US&tz=-180&geo={geo.upper()}&ns=15",
            geo,
            "daily"
        )
        if trends:
            return trends
        
        # Method 2: Realtime trends JSON endpoint
        trends = await self._fetch_json_endpoint(
            f"https://trends.google.com/trends/api/realtimetrends?hl=en-US&tz=-180&cat=all&fi=0&fs=0&geo={geo.upper()}&ri=300&rs=20&sort=0",
            geo,
            "realtime"
        )
        if trends:
            return trends
        
        # Method 3: Playwright fallback
        return await self._fetch_with_playwright(geo)
    
    async def _fetch_json_endpoint(self, url: str, geo: str, endpoint_type: str) -> List[str]:
        """Fetch from Google Trends JSON API"""
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status != 200:
                        logger.debug(f"JSON {endpoint_type} returned {resp.status} for {geo}")
                        return []
                    
                    text = await resp.text()
                    
                    # Remove Google's XSSI protection prefix
                    if text.startswith(")]}'"):
                        text = text[4:]
                    
                    import json
                    data = json.loads(text)
                    trends = []
                    
                    if endpoint_type == "daily":
                        days = data.get("default", {}).get("trendingSearchesDays", [])
                        for day in days:
                            for search in day.get("trendingSearches", []):
                                title_data = search.get("title", {})
                                title = title_data.get("query", "")
                                if title:
                                    trends.append(title)
                    
                    elif endpoint_type == "realtime":
                        stories = data.get("storySummaries", {}).get("trendingStories", [])
                        for story in stories:
                            title = story.get("title", "")
                            if title:
                                trends.append(title)
                    
                    if trends:
                        logger.info(f"✅ JSON {endpoint_type} extracted {len(trends)} trends for {geo}")
                        return trends[:self.limit]
                    
                    return []
                    
        except Exception as e:
            logger.debug(f"JSON {endpoint_type} error for {geo}: {e}")
            return []
    
    async def _fetch_with_playwright(self, geo: str) -> List[str]:
        """Fetch trending searches via Playwright browser automation (fallback)"""
        
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                url = f"https://trends.google.com/trending?geo={geo.upper()}"
                
                try:
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    await page.wait_for_timeout(4000)
                    
                    # Extract trends from page text
                    trends = await page.evaluate('''() => {
                        const trends = [];
                        const text = document.body.innerText;
                        const lines = text.split('\\n');
                        
                        const skipPatterns = [
                            'Trends', 'Home', 'Explore', 'Trending now', 'Sign in',
                            'United States', 'Turkey', 'Japan', 'China', 'United Kingdom', 'Germany',
                            'Past 24 hours', 'All categories', 'All trends', 'By relevance',
                            'Export', 'Search trends', 'Sort by title', 'Search volume',
                            'Started', 'Trend breakdown', 'Trend status', 'Sort by recency',
                            'location_on', 'calendar_month', 'category', 'grid_3x3',
                            'sort', 'ios_share', 'search', 'info', 'trending_up', 'arrow_upward'
                        ];
                        
                        for (let i = 0; i < lines.length; i++) {
                            const line = lines[i].trim();
                            
                            if (line.length < 3 || line.length > 80) continue;
                            if (skipPatterns.some(p => line === p || line.startsWith(p))) continue;
                            if (/^\\d+[KM]?\\+?$/.test(line)) continue;
                            if (/^\\d+%$/.test(line)) continue;
                            if (/^\\d+ hours? ago$/.test(line)) continue;
                            if (/^Active$/.test(line)) continue;
                            if (/^\\+ \\d+ more$/.test(line)) continue;
                            if (/^\\(Updated .+\\)$/.test(line)) continue;
                            if (/^Sort by /.test(line)) continue;
                            if (!/[a-zA-Z0-9]/.test(line)) continue;
                            
                            trends.push(line);
                        }
                        
                        return [...new Set(trends)];
                    }''')
                    
                    if trends and len(trends) > 0:
                        logger.info(f"✅ Playwright extracted {len(trends)} trends for {geo}")
                        return trends[:self.limit]
                    else:
                        logger.warning(f"⚠️  No trends found with Playwright for {geo}")
                        return []
                        
                except Exception as e:
                    logger.warning(f"⚠️  Playwright page error for {geo}: {e}")
                    return []
                finally:
                    await context.close()
                    await browser.close()
                    
        except ImportError:
            logger.warning(f"⚠️  Playwright not available")
            return []
        except Exception as e:
            logger.warning(f"⚠️  Playwright failed for {geo}: {e}")
            return []
    
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
            return ContentCategory.NEWS


# Export
google_trends_source = GoogleTrendsSource()
