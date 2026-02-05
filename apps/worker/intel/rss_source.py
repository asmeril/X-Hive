"""
RSS Feed Content Source for X-Hive

Fetches content from RSS/Atom feeds with automatic categorization
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict
from xml.etree import ElementTree as ET

import aiohttp
import feedparser

from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory,
    ContentQuality,
    ContentSourceError,
)

logger = logging.getLogger(__name__)


# Default RSS feeds organized by category
DEFAULT_FEEDS = {
    # Tech News
    'TechCrunch': 'https://techcrunch.com/feed/',
    'Wired': 'https://www.wired.com/feed/rss',
    'The Verge': 'https://www.theverge.com/rss/index.xml',
    'Ars Technica': 'https://feeds.arstechnica.com/arstechnica/index',
    'MIT Technology Review': 'https://www.technologyreview.com/feed/',
    'VentureBeat': 'https://venturebeat.com/feed/',
    'HackerNews': 'https://news.ycombinator.com/rss',
    
    # AI & ML Focused (verified working feeds only)
    'OpenAI Blog': 'https://openai.com/blog/rss.xml',
    'Google AI Blog': 'https://blog.research.google/feeds/posts/default',
    'DeepMind Blog': 'https://deepmind.google/blog/rss.xml',
    
    # Developer & Programming
    'GitHub Blog': 'https://github.blog/feed/',
    'Dev.to': 'https://dev.to/feed',
}


class RSSSource(BaseContentSource):
    """
    RSS/Atom feed content source.
    
    Features:
    - Multiple feed support
    - Automatic categorization
    - Quality scoring
    - Deduplication by URL
    """
    
    def __init__(
        self,
        feed_name: str = "RSS Aggregator",
        feeds: Optional[Dict[str, str]] = None,
        category: Optional[ContentCategory] = None,
        max_items: int = 20,
    ):
        """
        Initialize RSS source.
        
        Args:
            feed_name: Display name for this source
            feeds: Dictionary of {name: url} feeds (defaults to DEFAULT_FEEDS)
            category: Force category for all items (None = auto-categorize)
            max_items: Maximum items to fetch per feed
        """
        super().__init__()
        self.feed_name = feed_name
        self.feeds = feeds or DEFAULT_FEEDS
        self.forced_category = category
        self.max_items = max_items
        self.source_name = feed_name  # For categorization
        
        logger.info(f"✅ RSSSource initialized: {feed_name} ({len(self.feeds)} feeds)")
    
    def get_source_name(self) -> str:
        """Get source identifier"""
        return self.feed_name
    
    def get_source_type(self) -> str:
        """Get source type"""
        return "rss"
    
    async def fetch_latest(self, limit: int = 10) -> List[ContentItem]:
        """
        Fetch latest content from all configured feeds.
        
        Args:
            limit: Maximum total items to return
            
        Returns:
            List of ContentItem objects
        """
        all_items = []
        
        for feed_name, feed_url in self.feeds.items():
            try:
                items = await self._fetch_feed(feed_name, feed_url)
                all_items.extend(items)
                logger.debug(f"📡 Fetched {len(items)} items from {feed_name}")
            except Exception as e:
                logger.warning(f"Failed to fetch {feed_name}: {e}")
                continue
        
        # Sort by published date (newest first)
        all_items.sort(key=lambda x: x.published_at or datetime.min, reverse=True)
        
        # Return top items
        return all_items[:limit]
    
    async def _fetch_feed(self, feed_name: str, feed_url: str) -> List[ContentItem]:
        """
        Fetch content from a single RSS feed.
        
        Args:
            feed_name: Display name of the feed
            feed_url: RSS/Atom feed URL
            
        Returns:
            List of ContentItem objects
        """
        try:
            # Fetch feed content
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        raise ContentSourceError(f"HTTP {response.status} for {feed_url}")
                    
                    content = await response.text()
            
            # Parse RSS/Atom feed
            feed = feedparser.parse(content)
            
            if feed.bozo:
                logger.warning(f"Feed parsing warning for {feed_name}: {feed.bozo_exception}")
            
            # Convert entries to ContentItems
            items = []
            for entry in feed.entries[:self.max_items]:
                try:
                    item = self._parse_entry(entry, feed_name)
                    items.append(item)
                except Exception as e:
                    logger.warning(f"Failed to parse entry from {feed_name}: {e}")
                    continue
            
            return items
        
        except asyncio.TimeoutError:
            raise ContentSourceError(f"Timeout fetching {feed_url}")
        except Exception as e:
            raise ContentSourceError(f"Error fetching {feed_url}: {e}")
    
    def _parse_entry(self, entry, feed_name: str) -> ContentItem:
        """
        Parse RSS entry into ContentItem.
        
        Args:
            entry: feedparser entry object
            feed_name: Name of the source feed
            
        Returns:
            ContentItem object
        """
        # Extract basic fields
        title = entry.get('title', 'Untitled').strip()
        url = entry.get('link', '')
        description = entry.get('summary', '') or entry.get('description', '')
        author = entry.get('author', '')
        
        # Parse published date
        published_at = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6])
            except:
                pass
        
        # Store feed_name temporarily for categorization
        self.source_name = feed_name
        
        # Auto-categorize based on title/description
        category = self.forced_category or self._auto_categorize(title, description)
        
        # Extract tags
        tags = []
        if hasattr(entry, 'tags'):
            tags = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
        
        # Create ContentItem
        return ContentItem(
            title=title,
            url=url,
            source_type=self.get_source_type(),
            source_name=feed_name,
            description=description,
            author=author,
            published_at=published_at,
            category=category,
            tags=tags,
        )
    
    def _auto_categorize(self, title: str, description: str) -> ContentCategory:
        """Auto-categorize content based on keywords"""
        
        text = f"{title} {description}".lower()
        
        # Source-based categorization (highest priority)
        source_lower = self.source_name.lower() if hasattr(self, 'source_name') else ''
        
        if any(name in source_lower for name in ['huggingface', 'openai', 'deepmind', 'anthropic', 'google ai', 'papers with code']):
            return ContentCategory.AI_ML
        
        # AI/ML keywords (high priority)
        ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'ml', 
            'deep learning', 'gpt', 'llm', 'large language model',
            'neural', 'transformer', 'diffusion', 'stable diffusion',
            'chatgpt', 'claude', 'gemini', 'mistral', 'llama',
            'huggingface', 'hugging face', 'model', 'dataset',
            'training', 'fine-tuning', 'inference', 'embedding'
        ]
        if any(kw in text for kw in ai_keywords):
            return ContentCategory.AI_ML
        
        # Startup keywords
        startup_keywords = ['startup', 'funding', 'venture capital', 'vc', 'investment', 'series a', 'series b', 'acquisition']
        if any(kw in text for kw in startup_keywords):
            return ContentCategory.STARTUP
        
        # Programming keywords
        programming_keywords = ['programming', 'developer', 'code', 'github', 'open source', 'python', 'javascript', 'rust', 'typescript']
        if any(kw in text for kw in programming_keywords):
            return ContentCategory.PROGRAMMING
        
        # Productivity keywords
        productivity_keywords = ['productivity', 'workflow', 'automation', 'tool', 'app', 'efficiency']
        if any(kw in text for kw in productivity_keywords):
            return ContentCategory.PRODUCTIVITY
        
        # Blockchain keywords
        blockchain_keywords = ['blockchain', 'crypto', 'bitcoin', 'ethereum', 'web3', 'nft', 'defi']
        if any(kw in text for kw in blockchain_keywords):
            return ContentCategory.BLOCKCHAIN
        
        # Cybersecurity keywords
        security_keywords = ['security', 'cybersecurity', 'vulnerability', 'exploit', 'hack', 'malware', 'privacy']
        if any(kw in text for kw in security_keywords):
            return ContentCategory.CYBERSECURITY
        
        # Default
        return ContentCategory.TECH_NEWS


# Predefined source instances

tech_news_source = RSSSource(
    feed_name="Tech News Aggregator",
    category=ContentCategory.TECH_NEWS,
    max_items=20
)

ai_news_source = RSSSource(
    feed_name="AI & ML News Aggregator",
    category=ContentCategory.AI_ML,
    max_items=30
)

# AI-only feeds (verified working feeds only)
ai_only_feeds = {
    'OpenAI Blog': 'https://openai.com/blog/rss.xml',
    'Google AI Blog': 'https://blog.research.google/feeds/posts/default',
    'DeepMind Blog': 'https://deepmind.google/blog/rss.xml',
}

ai_research_source = RSSSource(
    feed_name="AI Research News",
    category=ContentCategory.AI_ML,
    max_items=25
)
ai_research_source.feeds = ai_only_feeds


# Example usage
async def test_rss_source():
    """Test RSS source functionality"""
    
    print("🧪 Testing RSS Source\n")
    
    # Test AI-focused source
    print("📡 Fetching AI/ML content...")
    items = await ai_research_source.fetch_with_tracking(limit=10)
    
    print(f"\n✅ Fetched {len(items)} items\n")
    
    for i, item in enumerate(items[:5], 1):
        print(f"{i}. [{item.category}] {item.title}")
        print(f"   Source: {item.source_name}")
        print(f"   URL: {item.url}")
        print()
    
    # Print stats
    stats = huggingface_source.get_stats()
    print(f"📊 Stats: {stats}")


if __name__ == "__main__":
    asyncio.run(test_rss_source())
