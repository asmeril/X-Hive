"""
Product Hunt Content Source

Fetches daily top products from Product Hunt API.
"""

import aiohttp
import logging
from typing import List, Optional
from datetime import datetime, date
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
        
        if not self.api_token:
            raise ValueError("Product Hunt API token not found in .env")
        
        self.days_back = days_back
        self.limit = limit
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "Product Hunt"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch latest Product Hunt products"""
        
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
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.API_BASE,
                    json={'query': query},
                    headers=headers
                ) as resp:
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
                item.category = self._categorize_product(topics, post['name'])
                
                # Scores
                item.relevance_score = min(post['votesCount'] / 500, 1.0)
                item.engagement_score = min(post['commentsCount'] / 50, 1.0)
                
                items.append(item)
            
            logger.info(f"✅ Fetched {len(items)} products from Product Hunt")
        
        except Exception as e:
            logger.error(f"❌ Error fetching Product Hunt: {e}")
        
        return items
    
    def _categorize_product(self, topics: List[str], name: str) -> ContentCategory:
        """Categorize product based on topics"""
        
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


# Export
producthunt_source = ProductHuntSource()
