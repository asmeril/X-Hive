"""
Twitter/X Content Source with Cookie-Based Scraping

Scrapes Twitter content using authenticated cookies to avoid API costs ($150/month savings).
Fetches viral tweets, influencer timelines, and trending topics.
Falls back to Nitter instances if cookie authentication fails.
"""

import aiohttp
from bs4 import BeautifulSoup
import logging
from typing import List, Optional, Dict
from datetime import datetime, timezone
import json
import re
from urllib.parse import quote_plus

from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory,
    ContentSourceError
)
from .cookie_manager import get_cookie_manager
from .cookie_loader import get_cookie_loader

logger = logging.getLogger(__name__)


class TwitterSource(BaseContentSource):
    """
    Twitter/X content aggregator using cookie-based scraping.
    
    Scrapes:
    - Viral tweets (high engagement)
    - Influencer timelines
    - Trending topics
    - Hashtag searches
    
    Uses authenticated cookies to bypass API costs ($150/month savings).
    Falls back to Nitter if cookies fail.
    """
    
    # Seed influencers (will be replaced by dynamic database in Phase 2)
    SEED_INFLUENCERS = {
        # AI/ML
        'sama': ContentCategory.AI_ML,           # Sam Altman
        'ylecun': ContentCategory.AI_ML,         # Yann LeCun
        'karpathy': ContentCategory.AI_ML,       # Andrej Karpathy
        'goodfellow_ian': ContentCategory.AI_ML, # Ian Goodfellow
        
        # Tech/Business
        'elonmusk': ContentCategory.TECH_PROGRAMMING,
        'satyanadella': ContentCategory.TECH_PROGRAMMING,
        'sundarpichai': ContentCategory.TECH_PROGRAMMING,
        
        # Crypto
        'VitalikButerin': ContentCategory.CRYPTO_WEB3,
        'naval': ContentCategory.CRYPTO_WEB3,
        
        # Startup
        'pmarca': ContentCategory.STARTUP_BUSINESS,  # Marc Andreessen
        'paulg': ContentCategory.STARTUP_BUSINESS,   # Paul Graham
    }
    
    TRENDING_KEYWORDS = [
        'AI', 'ChatGPT', 'LLM', 'Machine Learning',
        'Crypto', 'Bitcoin', 'Ethereum',
        'Startup', 'YC', 'Funding',
        'Tech', 'Programming', 'Python',
    ]
    
    BASE_URL = 'https://twitter.com'
    NITTER_INSTANCES = [
        'https://nitter.net',
        'https://nitter.poast.org',
        'https://nitter.privacydev.net',
    ]
    NITTER_TRENDING_PATHS = [
        '/trending',
        '/explore',
        '/',
    ]
    
    def __init__(
        self,
        influencers: Optional[Dict[str, ContentCategory]] = None,
        use_cookies: bool = True,
        fallback_to_nitter: bool = True,
        tweets_per_influencer: int = 5,
        min_likes: int = 100
    ):
        """
        Initialize Twitter source.
        
        Args:
            influencers: Username -> Category mapping
            use_cookies: Use cookie authentication (recommended)
            fallback_to_nitter: Fallback to Nitter if cookies fail
            tweets_per_influencer: Tweets to fetch per influencer
            min_likes: Minimum likes for viral tweets
        """
        super().__init__()
        
        # Get cookie manager and loader
        self.cookie_manager = get_cookie_manager()
        self.cookie_loader = get_cookie_loader()
        
        self.influencers = influencers or self.SEED_INFLUENCERS
        self.use_cookies = use_cookies
        self.fallback_to_nitter = fallback_to_nitter
        self.tweets_per_influencer = tweets_per_influencer
        self.min_likes = min_likes
        
        # Check cookie availability
        has_cookies = (
            self.cookie_manager.validate_cookie('twitter') and
            self.cookie_manager.validate_cookie('twitter_ct0')
        )
        
        if use_cookies and not has_cookies:
            logger.warning(
                "⚠️  Twitter cookies not found! Scraping will use Nitter fallback.\n"
                "   For better results, run: python tools/cookie_extractor.py\n"
                "   Savings: $150/month by avoiding Twitter API"
            )
            self.use_cookies = False
        
        logger.info(
            f"✅ TwitterSource initialized "
            f"({len(self.influencers)} influencers, "
            f"{'cookie auth' if self.use_cookies else 'Nitter fallback'})"
        )
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "Twitter/X"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """
        Fetch latest tweets from influencers and trending topics.
        
        Returns:
            List of ContentItem objects
        """
        
        items = []
        
        # Fetch from influencers
        for username, category in self.influencers.items():
            try:
                tweets = await self._fetch_user_tweets(username, category)
                items.extend(tweets)
                logger.debug(f"Fetched {len(tweets)} tweets from @{username}")
            
            except Exception as e:
                logger.error(f"❌ Error fetching tweets from @{username}: {e}")
                continue
        
        # Fetch viral tweets (trending) - with timeout protection
        try:
            # Skip for now - Nitter instances unstable
            logger.info("ℹ️  Skipping viral tweets (Nitter timeout issues)")
            # viral = await self._fetch_viral_tweets()
            # items.extend(viral)
        
        except Exception as e:
            logger.warning(f"⚠️  Skipping viral tweets due to timeout: {e}")
        
        logger.info(f"✅ Twitter: Fetched {len(items)} tweets from {len(self.influencers)} influencers")
        
        return items

    def _infer_category_from_text(self, text: str) -> ContentCategory:
        text_lower = text.lower()

        if any(keyword in text_lower for keyword in ['ai', 'ml', 'llm', 'chatgpt', 'model', 'deep learning']):
            return ContentCategory.AI_ML
        if any(keyword in text_lower for keyword in ['crypto', 'bitcoin', 'ethereum', 'web3']):
            return ContentCategory.CRYPTO_WEB3
        if any(keyword in text_lower for keyword in ['startup', 'founder', 'funding', 'vc', 'seed', 'series']):
            return ContentCategory.STARTUP_BUSINESS
        if any(keyword in text_lower for keyword in ['python', 'programming', 'developer', 'software', 'tech']):
            return ContentCategory.TECH_PROGRAMMING

        return ContentCategory.TECH_PROGRAMMING
    
    async def _fetch_user_tweets(
        self, 
        username: str,
        category: ContentCategory
    ) -> List[ContentItem]:
        """
        Fetch recent tweets from a user.
        
        Args:
            username: Twitter username (without @)
            category: Content category for this user
        
        Returns:
            List of ContentItem objects
        """
        
        # Try Playwright first (most reliable)
        try:
            items = await self._fetch_user_tweets_with_playwright(username, category)
            if items:
                logger.debug(f"✅ Playwright: fetched {len(items)} tweets from @{username}")
                return items
        except Exception as e:
            logger.debug(f"❌ Playwright failed for @{username}: {e}")
        
        # Try cookie-based scraping second
        if self.use_cookies:
            try:
                items = await self._fetch_user_tweets_with_cookies(username, category)
                if items:
                    logger.debug(f"✅ Cookie auth: fetched {len(items)} tweets from @{username}")
                    return items
                else:
                    logger.debug(f"⚠️  Cookie auth returned 0 items for @{username}, trying Nitter fallback")
            except Exception as e:
                logger.debug(f"❌ Cookie auth failed for @{username}: {e}, trying Nitter fallback")
        
        # Fallback to Nitter
        if self.fallback_to_nitter:
            return await self._fetch_user_tweets_nitter(username, category)
        
        return []
    
    async def _fetch_user_tweets_with_playwright(
        self,
        username: str,
        category: ContentCategory
    ) -> List[ContentItem]:
        """
        Fetch user tweets using Playwright (XiDeAI Pro method).
        
        Most reliable method - uses Playwright to scrape X.com with cookies.
        Parses <article> elements like XiDeAI Pro does.
        """
        
        items = []
        
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                # Load cookies
                playwright_cookies = self.cookie_loader.get_playwright_cookies('twitter')
                if playwright_cookies:
                    await context.add_cookies(playwright_cookies)
                
                page = await context.new_page()
                
                try:
                    # Navigate to user timeline
                    url = f"https://x.com/{username}"
                    await page.goto(url, wait_until='domcontentloaded', timeout=20000)
                    
                    # Wait for React to render
                    await page.wait_for_timeout(5000)
                    
                    # Try to wait for article elements
                    try:
                        await page.wait_for_selector('article', timeout=10000)
                    except:
                        logger.debug(f"No article elements found for @{username}")
                    
                    # Check if we're on login page
                    page_url = page.url
                    if 'login' in page_url or 'i/flow' in page_url:
                        logger.debug(f"Redirected to login page for @{username}")
                        return []
                    
                    # Extract tweets from <article> elements (XiDeAI Pro method)
                    tweets_data = await page.evaluate('''() => {
                        const articles = document.querySelectorAll('article');
                        const tweets = [];
                        
                        for (let article of articles) {
                            try {
                                // Author
                                const namesEl = article.querySelector('[data-testid="User-Names"]');
                                let author = '';
                                if (namesEl) {
                                    const text = namesEl.textContent;
                                    const match = text.match(/@(\\w+)/);
                                    author = match ? '@' + match[1] : '';
                                }
                                
                                // Text
                                const textEl = article.querySelector('[data-testid="tweetText"]');
                                const text = textEl ? textEl.textContent : '';
                                
                                // Skip too short
                                if (text.length < 10) continue;
                                
                                // URL
                                const linkEl = article.querySelector('a[href*="/status/"]');
                                const url = linkEl ? linkEl.href : '';
                                
                                // Time
                                const timeEl = article.querySelector('time');
                                const datetime = timeEl ? timeEl.getAttribute('datetime') : '';
                                
                                // Stats (likes, retweets)
                                let likes = 0;
                                let retweets = 0;
                                
                                const likeButton = article.querySelector('[data-testid="like"]');
                                if (likeButton) {
                                    const likeText = likeButton.getAttribute('aria-label') || '';
                                    const likeMatch = likeText.match(/(\\d+)/);
                                    if (likeMatch) likes = parseInt(likeMatch[1]);
                                }
                                
                                const retweetButton = article.querySelector('[data-testid="retweet"]');
                                if (retweetButton) {
                                    const rtText = retweetButton.getAttribute('aria-label') || '';
                                    const rtMatch = rtText.match(/(\\d+)/);
                                    if (rtMatch) retweets = parseInt(rtMatch[1]);
                                }
                                
                                if (url && text) {
                                    tweets.push({
                                        author: author,
                                        text: text,
                                        url: url,
                                        datetime: datetime,
                                        likes: likes,
                                        retweets: retweets
                                    });
                                }
                            } catch (e) {
                                console.error('Error parsing tweet:', e);
                            }
                        }
                        
                        return tweets;
                    }''')
                    
                    # Convert to ContentItems
                    for tweet_data in tweets_data[:self.tweets_per_influencer]:
                        try:
                            # Parse datetime
                            published_at = datetime.now(timezone.utc)
                            if tweet_data.get('datetime'):
                                try:
                                    published_at = datetime.fromisoformat(
                                        tweet_data['datetime'].replace('Z', '+00:00')
                                    )
                                except:
                                    pass
                            
                            text = tweet_data['text']
                            
                            item = ContentItem(
                                title=text[:100] + ('...' if len(text) > 100 else ''),
                                url=tweet_data['url'],
                                source_type='twitter',
                                source_name=f"Twitter - @{username}",
                                published_at=published_at,
                                category=category,
                                description=text,
                                author=tweet_data.get('author', f'@{username}')
                            )
                            
                            # Calculate scores based on engagement
                            likes = tweet_data.get('likes', 0)
                            retweets = tweet_data.get('retweets', 0)
                            
                            item.relevance_score = self._calculate_relevance(likes, retweets)
                            item.engagement_score = self._calculate_engagement(likes, retweets)
                            
                            items.append(item)
                        
                        except Exception as e:
                            logger.debug(f"Error creating ContentItem from tweet: {e}")
                            continue
                    
                    logger.debug(f"Playwright fetched {len(items)} tweets from @{username}")
                
                except Exception as e:
                    logger.debug(f"Playwright page error for @{username}: {e}")
                finally:
                    try:
                        await page.close()
                    except:
                        pass
                    
                    try:
                        await context.close()
                    except:
                        pass
                    
                    try:
                        await browser.close()
                    except:
                        pass
        
        except ImportError:
            logger.debug("Playwright not available")
        except Exception as e:
            logger.debug(f"Playwright fetch failed for @{username}: {e}")
        
        return items
    
    async def _fetch_user_tweets_with_cookies(
        self,
        username: str,
        category: ContentCategory
    ) -> List[ContentItem]:
        """
        Fetch user tweets using cookie authentication (Twitter.com).
        
        This method scrapes twitter.com using authenticated session.
        """
        
        items = []
        
        # Try to get cookies from JSON first
        try:
            cookie_header = self.cookie_loader.get_cookie_header('twitter')
            
            if not cookie_header:
                raise ContentSourceError("No Twitter cookies available")
            
            url = f"{self.BASE_URL}/{username}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': cookie_header,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://twitter.com/',
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    
                    if response.status == 403:
                        raise ContentSourceError("Twitter returned 403 - cookies may be invalid")
                    
                    if response.status != 200:
                        raise ContentSourceError(f"HTTP {response.status} from Twitter")
                    
                    html = await response.text()
                    
                    # Extract tweets from HTML
                    # Twitter uses complex React app, tweets are in script tags as JSON
                    
                    # Look for initial state data
                    tweet_data_match = re.search(
                        r'<script[^>]*>window\.__INITIAL_STATE__\s*=\s*({.*?})</script>',
                        html,
                        re.DOTALL
                    )
                    
                    if not tweet_data_match:
                        logger.debug(f"Could not find tweet data for @{username}")
                        return items
                    
                    try:
                        initial_state = json.loads(tweet_data_match.group(1))
                        
                        # Extract tweets from initial state
                        tweets_data = self._extract_tweets_from_initial_state(initial_state)
                        
                        for tweet_data in tweets_data[:self.tweets_per_influencer]:
                            item = self._create_content_item_from_tweet(tweet_data, category)
                            if item:
                                items.append(item)
                    
                    except json.JSONDecodeError as e:
                        logger.debug(f"Failed to parse Twitter initial state: {e}")
        
        except Exception as e:
            logger.debug(f"Cookie-based Twitter scraping failed: {e}")
        
        return items
    
    async def _fetch_user_tweets_nitter(
        self,
        username: str,
        category: ContentCategory
    ) -> List[ContentItem]:
        """
        Fetch user tweets using Nitter (Twitter scraper frontend).
        
        Nitter is more reliable but may be slower.
        """
        
        items = []
        
        # Try multiple Nitter instances (limit attempts)
        max_instances = 2  # Only try first 2 instances
        for nitter_url in self.NITTER_INSTANCES[:max_instances]:
            try:
                url = f"{nitter_url}/{username}"
                
                headers = {
                    'User-Agent': (
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36'
                    )
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url, 
                        headers=headers, 
                        timeout=aiohttp.ClientTimeout(total=5)  # Reduced to 5s
                    ) as response:
                        
                        if response.status != 200:
                            continue
                        
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find tweet containers
                        tweet_divs = soup.find_all('div', class_='timeline-item')
                        
                        for tweet_div in tweet_divs[:self.tweets_per_influencer]:
                            try:
                                # Extract tweet content
                                content_div = tweet_div.find('div', class_='tweet-content')
                                if not content_div:
                                    continue
                                
                                text = content_div.get_text(strip=True)
                                
                                # Extract link
                                link_elem = tweet_div.find('a', class_='tweet-link')
                                if not link_elem:
                                    continue
                                
                                tweet_url = nitter_url + link_elem['href']
                                
                                # Convert to twitter.com URL
                                tweet_url = tweet_url.replace(nitter_url, self.BASE_URL)
                                
                                # Extract stats
                                stats_div = tweet_div.find('div', class_='tweet-stats')
                                
                                likes = 0
                                retweets = 0
                                
                                if stats_div:
                                    # Parse stats
                                    stats_text = stats_div.get_text()
                                    
                                    # Extract numbers (simple regex)
                                    numbers = re.findall(r'(\d+(?:,\d+)*)', stats_text)
                                    if len(numbers) >= 2:
                                        likes = int(numbers[0].replace(',', ''))
                                        retweets = int(numbers[1].replace(',', ''))
                                
                                # Create ContentItem
                                item = ContentItem(
                                    title=text[:100] + ('...' if len(text) > 100 else ''),
                                    url=tweet_url,
                                    source_type='twitter',
                                    source_name=f"Twitter - @{username}",
                                    published_at=datetime.now(timezone.utc),  # Nitter doesn't always show exact time
                                    category=category,
                                    description=text,
                                    author=username
                                )
                                
                                # Calculate scores
                                item.relevance_score = self._calculate_relevance(likes, retweets)
                                item.engagement_score = self._calculate_engagement(likes, retweets)
                                
                                items.append(item)
                            
                            except Exception as e:
                                logger.debug(f"Error parsing tweet: {e}")
                                continue
                
                # If we got tweets, break (don't try other instances)
                if items:
                    logger.debug(f"Successfully fetched from Nitter instance: {nitter_url}")
                    break
            
            except Exception as e:
                logger.debug(f"Nitter instance {nitter_url} failed: {e}")
                continue
        
        return items
    
    async def _fetch_viral_tweets(self) -> List[ContentItem]:
        """
        Fetch viral tweets (high engagement).
        
        Uses trending searches and filters by engagement.
        """
        topics = await self._fetch_trending_topics()
        if not topics:
            topics = self.TRENDING_KEYWORDS

        items = []

        for topic in topics[:8]:
            try:
                search_items = await self._search_nitter_tweets(topic)
                for item in search_items:
                    if item.engagement_score >= 0.2:
                        items.append(item)
            except Exception as e:
                logger.debug(f"Error fetching viral tweets for topic '{topic}': {e}")
                continue

        return items

    async def _fetch_trending_topics(self) -> List[str]:
        topics = set()

        for nitter_url in self.NITTER_INSTANCES:
            for path in self.NITTER_TRENDING_PATHS:
                try:
                    url = f"{nitter_url}{path}"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            if response.status != 200:
                                continue

                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')

                            for link in soup.find_all('a', href=True):
                                href = link['href']
                                text = link.get_text(strip=True)

                                if href.startswith('/search?q='):
                                    match = re.search(r'q=([^&]+)', href)
                                    if match:
                                        text = match.group(1)

                                if href.startswith('/hashtag/'):
                                    text = href.replace('/hashtag/', '').replace('%23', '')

                                cleaned = text.replace('#', '').strip()
                                if len(cleaned) > 2:
                                    topics.add(cleaned)

                            if len(topics) >= 12:
                                return list(topics)

                except Exception:
                    continue

            if topics:
                break

        return list(topics)

    async def _search_nitter_tweets(self, query: str) -> List[ContentItem]:
        items = []
        encoded_query = quote_plus(query)

        for nitter_url in self.NITTER_INSTANCES:
            try:
                url = f"{nitter_url}/search?q={encoded_query}&f=tweets"

                headers = {
                    'User-Agent': (
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36'
                    )
                }

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status != 200:
                            continue

                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        tweet_divs = soup.find_all('div', class_='timeline-item')
                        for tweet_div in tweet_divs[:5]:
                            try:
                                content_div = tweet_div.find('div', class_='tweet-content')
                                if not content_div:
                                    continue

                                text = content_div.get_text(strip=True)
                                link_elem = tweet_div.find('a', class_='tweet-link')
                                if not link_elem:
                                    continue

                                tweet_url = nitter_url + link_elem['href']
                                tweet_url = tweet_url.replace(nitter_url, self.BASE_URL)

                                stats_div = tweet_div.find('div', class_='tweet-stats')
                                likes = 0
                                retweets = 0

                                if stats_div:
                                    stats_text = stats_div.get_text()
                                    numbers = re.findall(r'(\d+(?:,\d+)*)', stats_text)
                                    if len(numbers) >= 2:
                                        likes = int(numbers[0].replace(',', ''))
                                        retweets = int(numbers[1].replace(',', ''))

                                if likes < self.min_likes:
                                    continue

                                category = self._infer_category_from_text(text)

                                item = ContentItem(
                                    title=text[:100] + ('...' if len(text) > 100 else ''),
                                    url=tweet_url,
                                    source_type='twitter',
                                    source_name=f"Twitter - Trending: {query}",
                                    published_at=datetime.now(timezone.utc),
                                    category=category,
                                    description=text,
                                    author=""
                                )

                                item.relevance_score = self._calculate_relevance(likes, retweets)
                                item.engagement_score = self._calculate_engagement(likes, retweets)

                                items.append(item)

                            except Exception:
                                continue

                if items:
                    break

            except Exception:
                continue

        return items
    
    def _extract_tweets_from_initial_state(self, initial_state: dict) -> List[dict]:
        """
        Extract tweet data from Twitter's initial state object.
        
        Note: Twitter's data structure changes frequently.
        This is a simplified implementation.
        """
        
        tweets = []
        
        # Try to find tweets in various locations
        # (Twitter's structure is complex and unstable)
        
        try:
            # Look in entities.tweets
            if 'entities' in initial_state and 'tweets' in initial_state['entities']:
                tweets_dict = initial_state['entities']['tweets']
                for tweet_id, tweet_data in tweets_dict.items():
                    tweets.append(tweet_data)
        
        except Exception as e:
            logger.debug(f"Error extracting tweets from initial state: {e}")
        
        return tweets
    
    def _create_content_item_from_tweet(
        self,
        tweet_data: dict,
        category: ContentCategory
    ) -> Optional[ContentItem]:
        """
        Create ContentItem from tweet data dict.
        """
        
        try:
            text = tweet_data.get('text', tweet_data.get('full_text', ''))
            tweet_id = tweet_data.get('id_str', '')
            username = tweet_data.get('user', {}).get('screen_name', 'unknown')
            
            if not text or not tweet_id:
                return None
            
            # Create item
            item = ContentItem(
                title=text[:100] + ('...' if len(text) > 100 else ''),
                url=f"{self.BASE_URL}/{username}/status/{tweet_id}",
                source_type='twitter',
                source_name=f"Twitter - @{username}",
                published_at=datetime.now(timezone.utc),
                category=category,
                description=text,
                author=username
            )
            
            # Extract engagement
            likes = tweet_data.get('favorite_count', 0)
            retweets = tweet_data.get('retweet_count', 0)
            
            item.relevance_score = self._calculate_relevance(likes, retweets)
            item.engagement_score = self._calculate_engagement(likes, retweets)
            
            return item
        
        except Exception as e:
            logger.debug(f"Error creating ContentItem from tweet: {e}")
            return None
    
    def _calculate_relevance(self, likes: int, retweets: int) -> float:
        """Calculate relevance score based on engagement"""
        
        score = 0.5  # Base
        
        # High engagement = high relevance
        if likes > 10000:
            score += 0.3
        elif likes > 1000:
            score += 0.2
        elif likes > 100:
            score += 0.1
        
        # Retweets also matter
        if retweets > 1000:
            score += 0.2
        elif retweets > 100:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_engagement(self, likes: int, retweets: int) -> float:
        """Calculate engagement score"""
        
        score = 0.0
        
        # Likes (0-0.5)
        score += min(0.5, likes / 10000)
        
        # Retweets (0-0.5)
        score += min(0.5, retweets / 1000)
        
        return min(score, 1.0)


# Global instance
twitter_source = TwitterSource()
