"""
Product Hunt Content Source

Fetches daily top products from Product Hunt.
"""

import aiohttp
from bs4 import BeautifulSoup
import logging
from typing import List, Optional
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
import os

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory,
    ContentSourceError,
    CATEGORY_TARGETS
)
from .cookie_loader import get_cookie_loader

logger = logging.getLogger(__name__)


class ProductHuntSource(BaseContentSource):
    """
    Product Hunt aggregator.
    
    Fetches daily top products.
    """
    
    API_BASE = "https://api.producthunt.com/v2/api/graphql"
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        days_back: int = 3,
        limit: int = 20
    ):
        super().__init__()
        
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_token = api_token or os.getenv('PRODUCTHUNT_API_TOKEN')
        self.days_back = days_back
        self.limit = limit
        
        # Note: API token is optional - will fall back to web scraping
        if not self.api_token:
            logger.info("ℹ️  Product Hunt API token not found - using web scraping")
        
        logger.info(f"✅ ProductHuntSource initialized (limit={limit})")
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "Product Hunt"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch latest Product Hunt products"""
        
        # Try API first if token available
        if self.api_token:
            try:
                items = await self._fetch_via_api()
                if items:
                    return items
            except Exception as e:
                logger.debug(f"API fetch failed, falling back to scraping: {e}")
        
        # Fallback to web scraping
        return await self._fetch_via_scraping()
    
    async def _fetch_via_api(self) -> List[ContentItem]:
        """Fetch via Product Hunt API (requires token)"""
        
        items = []
        
        # GraphQL query
        query = """
        query {
          posts(order: VOTES, first: %d) {
            edges {
              node {
                id
                name
                tagline
                description
                url
                votesCount
                commentsCount
                createdAt
                topics {
                  edges {
                    node {
                      name
                    }
                  }
                }
              }
            }
          }
        }
        """ % self.limit
        
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.API_BASE,
                json={'query': query},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    raise ContentSourceError(f"API returned {resp.status}")
                
                data = await resp.json()
        
        posts = data.get('data', {}).get('posts', {}).get('edges', [])
        
        for edge in posts:
            post = edge['node']
            
            # Create ContentItem
            item = ContentItem(
                title=post['name'],
                url=post['url'],
                source_type='producthunt',
                source_name='Product Hunt',
                published_at=datetime.fromisoformat(post['createdAt'].replace('Z', '+00:00')),
                description=post.get('tagline') or post.get('description', '')[:500]
            )
            
            # Categorize based on topics
            topics = [t['node']['name'].lower() for t in post.get('topics', {}).get('edges', [])]
            item.category = self._categorize_by_topics(topics, post['name'])
            
            # Scores
            item.relevance_score = min(post['votesCount'] / 500, 1.0)
            item.engagement_score = min(post['commentsCount'] / 50, 1.0)
            
            items.append(item)
        
        logger.info(f"✅ Product Hunt API: Fetched {len(items)} products")
        
        return items
    
    async def _fetch_via_scraping(self) -> List[ContentItem]:
        """Fetch via web scraping (no API token needed)"""
        
        items = []
        
        url = "https://www.producthunt.com"
        
        # Get cookies if available
        cookie_loader = get_cookie_loader()
        cookie_header = cookie_loader.get_cookie_header('producthunt')
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        if cookie_header:
            headers['Cookie'] = cookie_header
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    
                    if response.status != 200:
                        logger.error(f"HTTP {response.status} from Product Hunt")
                        return items
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find product cards (Product Hunt structure)
                    # They use various selectors, try multiple approaches
                    
                    # Try method 1: data attributes
                    products = soup.find_all('div', attrs={'data-test': 'post-item'})
                    
                    if not products:
                        # Try method 2: class names
                        products = soup.find_all('div', class_=lambda x: x and 'post' in str(x).lower())
                    
                    if not products:
                        # Try method 3: article tags
                        products = soup.find_all('article')
                    
                    if not products:
                        logger.warning("⚠️  No products found in HTML structure")
                        return items
                    
                    for product in products[:self.limit]:
                        try:
                            # Extract product name
                            name_elem = product.find(['h2', 'h3', 'a'], class_=lambda x: x and ('title' in str(x).lower() or 'name' in str(x).lower()))
                            
                            if not name_elem:
                                # Try data-test attribute
                                name_elem = product.find(attrs={'data-test': 'post-name'})
                            
                            if not name_elem:
                                continue
                            
                            name = name_elem.get_text(strip=True)
                            
                            if not name or len(name) < 3:
                                continue
                            
                            # Get URL
                            link = product.find('a', href=True)
                            if link:
                                product_url = link['href']
                                if not product_url.startswith('http'):
                                    product_url = 'https://www.producthunt.com' + product_url
                            else:
                                continue
                            
                            # Get description
                            desc_elem = product.find(['p', 'div'], class_=lambda x: x and 'tagline' in str(x).lower())
                            description = desc_elem.get_text(strip=True) if desc_elem else None
                            
                            # Create item
                            item = ContentItem(
                                title=name,
                                url=product_url,
                                source_type='producthunt',
                                source_name='Product Hunt',
                                published_at=datetime.now(timezone.utc),
                                category=self._categorize_product(name, description),
                                description=description
                            )
                            
                            item.relevance_score = 0.75
                            item.engagement_score = 0.7
                            
                            items.append(item)
                        
                        except Exception as e:
                            logger.debug(f"Error parsing product: {e}")
                            continue
                    
                    logger.info(f"✅ Product Hunt scraping: Fetched {len(items)} products")
        
        except Exception as e:
            logger.error(f"❌ Error fetching Product Hunt: {e}")
        
        return items
    
    def _categorize_by_topics(self, topics: List[str], name: str) -> ContentCategory:
        """Categorize product based on topics (API response)"""
        
        # Check topics
        if any(t in topics for t in ['ai', 'machine learning', 'artificial intelligence']):
            return ContentCategory.AI_ML
        
        if any(t in topics for t in ['crypto', 'blockchain', 'web3']):
            return ContentCategory.CRYPTO_WEB3
        
        if any(t in topics for t in ['gaming', 'games']):
            return ContentCategory.GAMING_ENTERTAINMENT
        
        if any(t in topics for t in ['mobile', 'ios', 'android']):
            return ContentCategory.MOBILE_APPS
        
        if any(t in topics for t in ['security', 'privacy']):
            return ContentCategory.SECURITY_PRIVACY
        
        # Default: startup/business
        return ContentCategory.STARTUP_BUSINESS
    
    def _categorize_product(self, name: str, description: Optional[str]) -> ContentCategory:
        """Auto-categorize product based on name/description (scraping)"""
        
        text = (name + ' ' + (description or '')).lower()
        
        if any(kw in text for kw in ['ai', 'ml', 'machine learning', 'neural', 'gpt', 'llm']):
            return ContentCategory.AI_ML
        elif any(kw in text for kw in ['crypto', 'blockchain', 'web3', 'nft', 'defi']):
            return ContentCategory.CRYPTO_WEB3
        elif any(kw in text for kw in ['game', 'gaming', 'vr', 'ar']):
            return ContentCategory.GAMING_ENTERTAINMENT
        elif any(kw in text for kw in ['mobile', 'ios', 'android', 'app']):
            return ContentCategory.MOBILE_APPS
        elif any(kw in text for kw in ['security', 'privacy', 'encryption']):
            return ContentCategory.SECURITY_PRIVACY
        elif any(kw in text for kw in ['saas', 'startup', 'business']):
            return ContentCategory.STARTUP_BUSINESS
        else:
            return ContentCategory.TECH_PROGRAMMING


# Export
producthunt_source = ProductHuntSource()
