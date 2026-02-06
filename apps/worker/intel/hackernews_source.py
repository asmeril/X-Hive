"""
Hacker News Content Source

Fetches top, new, and best stories from Hacker News API.
"""

import aiohttp
import logging
from typing import List, Optional
from datetime import datetime
from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory,
    ContentSourceError,
    CATEGORY_TARGETS
)

logger = logging.getLogger(__name__)


class HackerNewsSource(BaseContentSource):
    """
    Hacker News content aggregator.
    
    Fetches top/new stories from HN.
    """
    
    API_BASE = "https://hacker-news.firebaseio.com/v0"
    ALGOLIA_BASE = "https://hn.algolia.com/api/v1"
    
    def __init__(
        self,
        story_type: str = 'top',  # 'top', 'new', 'best', 'ask', 'show'
        limit: int = 30
    ):
        super().__init__()
        self.story_type = story_type
        self.limit = limit
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "Hacker News"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch latest HN stories"""
        
        items = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get story IDs
                async with session.get(f"{self.API_BASE}/{self.story_type}stories.json") as resp:
                    story_ids = await resp.json()
                
                # Fetch top N stories
                for story_id in story_ids[:self.limit]:
                    try:
                        async with session.get(f"{self.API_BASE}/item/{story_id}.json") as resp:
                            story = await resp.json()
                        
                        if not story or story.get('type') != 'story':
                            continue
                        
                        # Create ContentItem
                        item = ContentItem(
                            title=story.get('title', ''),
                            url=story.get('url') or f"https://news.ycombinator.com/item?id={story_id}",
                            source_type='hackernews',
                            source_name='Hacker News',
                            published_at=datetime.fromtimestamp(story.get('time', 0)),
                            author=story.get('by'),
                            description=story.get('text', '')[:500] if story.get('text') else None
                        )
                        
                        # Categorize
                        item.category = self._categorize_story(story)
                        
                        # Scores
                        item.relevance_score = self._calculate_relevance(story)
                        item.engagement_score = self._calculate_engagement(story)
                        
                        items.append(item)
                    
                    except Exception as e:
                        logger.error(f"Error fetching story {story_id}: {e}")
                        continue
            
            logger.info(f"✅ Fetched {len(items)} stories from Hacker News")
        
        except Exception as e:
            logger.error(f"❌ Error fetching HN stories: {e}")
        
        return items
    
    def _categorize_story(self, story) -> ContentCategory:
        """Auto-categorize HN story"""
        title = story.get('title', '').lower()
        text = story.get('text', '').lower() if story.get('text') else ''
        url = story.get('url', '').lower()
        
        # AI/ML keywords
        if any(kw in title or kw in text for kw in ['ai', 'machine learning', 'llm', 'gpt', 'neural']):
            return ContentCategory.AI_ML
        
        # Startup keywords
        if any(kw in title for kw in ['launch', 'show hn', 'yc', 'funding', 'startup']):
            return ContentCategory.STARTUP_BUSINESS
        
        # Security
        if any(kw in title or kw in text for kw in ['security', 'vulnerability', 'hack', 'breach']):
            return ContentCategory.SECURITY_PRIVACY
        
        # Crypto
        if any(kw in title for kw in ['crypto', 'bitcoin', 'ethereum', 'blockchain']):
            return ContentCategory.CRYPTO_WEB3
        
        # Gaming
        if any(kw in title for kw in ['game', 'gaming', 'unity', 'unreal']):
            return ContentCategory.GAMING_ENTERTAINMENT
        
        # Science
        if any(kw in title for kw in ['physics', 'biology', 'chemistry', 'research', 'study']):
            return ContentCategory.SCIENCE
        
        # Default: tech/programming
        return ContentCategory.TECH_PROGRAMMING
    
    def _calculate_relevance(self, story) -> float:
        """Calculate relevance based on HN score"""
        score = story.get('score', 0)
        # Normalize (100+ points = high relevance)
        return min(score / 100, 1.0)
    
    def _calculate_engagement(self, story) -> float:
        """Calculate engagement based on comments"""
        comments = story.get('descendants', 0)
        # Normalize (50+ comments = high engagement)
        return min(comments / 50, 1.0)


# Export
hackernews_source = HackerNewsSource()
