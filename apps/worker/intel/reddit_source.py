"""
Reddit Content Source

Fetches top posts from 20+ tech-related subreddits
across all 8 content categories using web scraping.
"""

import aiohttp
from bs4 import BeautifulSoup
import logging
from typing import List, Optional
from datetime import datetime
import re

from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory,
    ContentSourceError
)

logger = logging.getLogger(__name__)


class RedditSource(BaseContentSource):
    """
    Reddit content aggregator using web scraping.
    
    Scrapes public subreddit data (no API required).
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
    
    def __init__(
        self,
        subreddits: Optional[dict] = None,
        time_filter: str = 'day',
        limit: int = 10
    ):
        """
        Initialize Reddit scraper.
        
        Args:
            subreddits: Custom subreddit mapping
            time_filter: Time filter (hour/day/week/month/year)
            limit: Posts per subreddit (max 25)
        """
        super().__init__()
        
        self.subreddits = subreddits or self.SUBREDDITS
        self.time_filter = time_filter
        self.limit = min(limit, 25)
        
        logger.info(f"✅ RedditSource initialized ({len(self.subreddits)} subreddits, scraping mode)")
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "Reddit"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch top posts from all configured subreddits using scraping"""
        
        items = []
        
        async with aiohttp.ClientSession() as session:
            for subreddit_name, category in self.subreddits.items():
                try:
                    posts = await self._scrape_subreddit(session, subreddit_name)
                    
                    for post in posts[:self.limit]:
                        item = ContentItem(
                            title=post['title'],
                            url=post['url'],
                            source_type='reddit',
                            source_name=f"Reddit - r/{subreddit_name}",
                            published_at=post.get('created_at', datetime.now()),
                            category=category,
                            description=post.get('selftext'),
                            author=post.get('author')
                        )
                        
                        item.relevance_score = self._calculate_relevance(post)
                        item.engagement_score = self._calculate_engagement(post)
                        
                        items.append(item)
                    
                    logger.debug(f"Scraped {len(posts[:self.limit])} posts from r/{subreddit_name}")
                
                except Exception as e:
                    logger.error(f"❌ Error scraping r/{subreddit_name}: {e}")
                    continue
        
        logger.info(f"✅ Reddit: Scraped {len(items)} posts from {len(self.subreddits)} subreddits")
        return items
    
    async def _scrape_subreddit(self, session: aiohttp.ClientSession, subreddit: str) -> List[dict]:
        url = f"{self.BASE_URL}/r/{subreddit}/top/?t={self.time_filter}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"HTTP {response.status} for r/{subreddit}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                posts = []
                post_divs = soup.find_all('div', class_='thing', limit=self.limit)
                
                for post_div in post_divs:
                    if 'stickied' in post_div.get('class', []):
                        continue
                    
                    try:
                        title_elem = post_div.find('a', class_='title')
                        title = title_elem.text.strip() if title_elem else ''
                        
                        data_url = post_div.get('data-url', '')
                        permalink = post_div.get('data-permalink', '')
                        url = data_url if data_url and not data_url.startswith('/r/') else f"{self.BASE_URL}{permalink}"
                        
                        score_elem = post_div.find('div', class_='score unvoted')
                        score_text = score_elem.get('title', '0') if score_elem else '0'
                        score = self._parse_number(score_text)
                        
                        comments_elem = post_div.find('a', class_='comments')
                        comments_text = comments_elem.text if comments_elem else '0 comments'
                        comments = self._parse_number(comments_text.split()[0])
                        
                        author_elem = post_div.find('a', class_='author')
                        author = author_elem.text if author_elem else None
                        
                        time_elem = post_div.find('time')
                        created_at = datetime.now()
                        if time_elem and time_elem.get('datetime'):
                            try:
                                from dateutil import parser
                                created_at = parser.parse(time_elem['datetime'])
                            except:
                                pass
                        
                        posts.append({
                            'title': title,
                            'url': url,
                            'score': score,
                            'comments': comments,
                            'author': author,
                            'created_at': created_at,
                            'permalink': f"{self.BASE_URL}{permalink}",
                        })
                    
                    except Exception as e:
                        logger.debug(f"Error parsing post: {e}")
                        continue
                
                return posts
        
        except Exception as e:
            logger.error(f"Error fetching r/{subreddit}: {e}")
            return []
    
    def _parse_number(self, text: str) -> int:
        """Parse number from text (e.g., '1.2k' -> 1200)"""
        try:
            text = text.strip().lower()
            
            if 'k' in text:
                return int(float(text.replace('k', '')) * 1000)
            if 'm' in text:
                return int(float(text.replace('m', '')) * 1000000)
            
            clean = re.sub(r'[^\d]', '', text)
            return int(clean) if clean else 0
        except Exception:
            return 0
    
    def _calculate_relevance(self, post: dict) -> float:
        """Calculate relevance score based on post quality indicators"""
        score = 0.5
        
        if post['score'] > 1000:
            score += 0.3
        elif post['score'] > 500:
            score += 0.2
        elif post['score'] > 100:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_engagement(self, post: dict) -> float:
        """Calculate engagement score based on interactions"""
        score = 0.0
        
        score += min(0.5, post['score'] / 1000)
        score += min(0.5, post['comments'] / 100)
        
        return min(score, 1.0)


reddit_source = RedditSource()
