"""
Google Trends - Çalışan Scraping Yöntemi
"""
import aiohttp
import asyncio
import json
import re
from typing import List
from dataclasses import dataclass

@dataclass
class TrendItem:
    title: str
    geo: str
    rank: int
    traffic: str = ""

class GoogleTrendsScraper:
    """
    Google Trends Trending Searches sayfasını scrape eder.
    RSS yerine HTML/JSON endpoint kullanır.
    """
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    
    async def fetch_trends(self, geo: str = "US") -> List[TrendItem]:
        """Trending searches sayfasından veri çek"""
        
        # Yöntem 1: Daily trends JSON endpoint
        items = await self._fetch_daily_trends_json(geo)
        if items:
            return items
        
        # Yöntem 2: Realtime trends
        items = await self._fetch_realtime_trends(geo)
        if items:
            return items
        
        return []
    
    async def _fetch_daily_trends_json(self, geo: str) -> List[TrendItem]:
        """Daily trends JSON endpoint"""
        
        url = f"https://trends.google.com/trends/api/dailytrends?hl=en-US&tz=-180&geo={geo.upper()}&ns=15"
        
        try:
            async with aiohttp.ClientSession(headers=self.HEADERS) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status != 200:
                        print(f"Daily trends returned {resp.status}")
                        return []
                    
                    text = await resp.text()
                    
                    # Google bazen )]}' prefix ekler
                    if text.startswith(")]}'"):
                        text = text[4:]
                    
                    data = json.loads(text)
                    items = []
                    
                    # Parse the response
                    days = data.get("default", {}).get("trendingSearchesDays", [])
                    
                    rank = 1
                    for day in days:
                        for search in day.get("trendingSearches", []):
                            title_data = search.get("title", {})
                            title = title_data.get("query", "")
                            traffic = search.get("formattedTraffic", "")
                            
                            if title:
                                items.append(TrendItem(
                                    title=title,
                                    geo=geo,
                                    rank=rank,
                                    traffic=traffic
                                ))
                                rank += 1
                    
                    return items
                    
        except Exception as e:
            print(f"Daily trends error: {e}")
            return []
    
    async def _fetch_realtime_trends(self, geo: str) -> List[TrendItem]:
        """Realtime trends endpoint"""
        
        url = f"https://trends.google.com/trends/api/realtimetrends?hl=en-US&tz=-180&cat=all&fi=0&fs=0&geo={geo.upper()}&ri=300&rs=20&sort=0"
        
        try:
            async with aiohttp.ClientSession(headers=self.HEADERS) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status != 200:
                        print(f"Realtime trends returned {resp.status}")
                        return []
                    
                    text = await resp.text()
                    
                    if text.startswith(")]}'"):
                        text = text[4:]
                    
                    data = json.loads(text)
                    items = []
                    
                    stories = data.get("storySummaries", {}).get("trendingStories", [])
                    
                    for idx, story in enumerate(stories):
                        title = story.get("title", "")
                        if title:
                            items.append(TrendItem(
                                title=title,
                                geo=geo,
                                rank=idx + 1,
                                traffic=""
                            ))
                    
                    return items
                    
        except Exception as e:
            print(f"Realtime trends error: {e}")
            return []


# Test fonksiyonu
async def test_scraper():
    scraper = GoogleTrendsScraper()
    
    for geo in ["US", "TR", "GB"]:
        print(f"\n{'='*50}")
        print(f"📍 {geo} Trends:")
        print(f"{'='*50}")
        
        trends = await scraper.fetch_trends(geo)
        
        if not trends:
            print("❌ No trends found")
            continue
        
        for trend in trends[:10]:
            traffic = f" ({trend.traffic})" if trend.traffic else ""
            print(f"  {trend.rank}. {trend.title}{traffic}")
        
        print(f"\n✅ Total: {len(trends)} trends")


if __name__ == "__main__":
    asyncio.run(test_scraper())
