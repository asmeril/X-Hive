"""
Base Content Source System for X-Hive Intel Gathering

Provides abstract base classes and data structures for content collection
from various sources (RSS, Telegram, GitHub, Reddit, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class ContentCategory(str, Enum):
    """Content categories"""
    AI_ML = "ai_ml"
    TECH_NEWS = "tech_news"
    STARTUP = "startup"
    PRODUCTIVITY = "productivity"
    PROGRAMMING = "programming"
    BLOCKCHAIN = "blockchain"
    CYBERSECURITY = "cybersecurity"
    DESIGN = "design"
    BUSINESS = "business"
    OTHER = "other"


class ContentQuality(str, Enum):
    """Content quality levels"""
    HIGH = "high"          # Must-share content
    MEDIUM = "medium"      # Good content
    LOW = "low"            # Skip or low priority


@dataclass
class ContentItem:
    """
    Raw content item from any source.
    
    This is the universal format all sources convert to.
    """
    
    # Required fields
    title: str
    url: str
    source_type: str  # "rss", "telegram", "github", etc.
    source_name: str  # Specific source (e.g., "TechCrunch", "AINews")
    
    # Optional fields
    description: str = ""
    content: str = ""  # Full content if available
    author: str = ""
    published_at: Optional[datetime] = None
    
    # Metadata
    category: ContentCategory = ContentCategory.OTHER
    quality: Optional[ContentQuality] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Extra source-specific data
    
    # Processing
    collected_at: datetime = field(default_factory=datetime.now)
    processed: bool = False
    ai_summary: str = ""
    suggested_tweet: str = ""
    
    # Scoring
    relevance_score: float = 0.0  # 0-1, how relevant to our audience
    engagement_score: float = 0.0  # 0-1, predicted engagement
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'title': self.title,
            'url': self.url,
            'source_type': self.source_type,
            'source_name': self.source_name,
            'description': self.description,
            'content': self.content[:500] if self.content else "",  # Truncate for storage
            'author': self.author,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'category': self.category,
            'quality': self.quality,
            'tags': self.tags,
            'collected_at': self.collected_at.isoformat(),
            'processed': self.processed,
            'ai_summary': self.ai_summary,
            'suggested_tweet': self.suggested_tweet,
            'relevance_score': self.relevance_score,
            'engagement_score': self.engagement_score,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentItem':
        """Create ContentItem from dictionary"""
        return cls(
            title=data['title'],
            url=data['url'],
            source_type=data['source_type'],
            source_name=data['source_name'],
            description=data.get('description', ''),
            content=data.get('content', ''),
            author=data.get('author', ''),
            published_at=datetime.fromisoformat(data['published_at']) if data.get('published_at') else None,
            category=ContentCategory(data.get('category', ContentCategory.OTHER)),
            quality=ContentQuality(data['quality']) if data.get('quality') else None,
            tags=data.get('tags', []),
            collected_at=datetime.fromisoformat(data['collected_at']) if data.get('collected_at') else datetime.now(),
            processed=data.get('processed', False),
            ai_summary=data.get('ai_summary', ''),
            suggested_tweet=data.get('suggested_tweet', ''),
            relevance_score=data.get('relevance_score', 0.0),
            engagement_score=data.get('engagement_score', 0.0),
        )


class BaseContentSource(ABC):
    """
    Abstract base class for all content sources.
    
    Subclasses must implement:
    - fetch_latest(): Retrieve new content
    - get_source_name(): Return source identifier
    """
    
    def __init__(self):
        """Initialize source"""
        self.last_fetch: Optional[datetime] = None
        self.fetch_count: int = 0
        self.error_count: int = 0
    
    @abstractmethod
    async def fetch_latest(self, limit: int = 10) -> List[ContentItem]:
        """
        Fetch latest content from this source.
        
        Args:
            limit: Maximum number of items to fetch
            
        Returns:
            List of ContentItem objects
            
        Raises:
            ContentSourceError: If fetch fails
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """
        Get unique identifier for this source.
        
        Returns:
            Source name string
        """
        pass
    
    def get_source_type(self) -> str:
        """
        Get source type (rss, telegram, etc.).
        
        Default implementation returns class name.
        Override if needed.
        """
        return self.__class__.__name__.lower().replace('source', '')
    
    async def fetch_with_tracking(self) -> List[ContentItem]:
        """
        Fetch content with automatic tracking.
        
        Wrapper around fetch_latest() that tracks:
        - Last fetch time
        - Fetch count
        - Error count
        """
        try:
            items = await self.fetch_latest()
            self.last_fetch = datetime.now()
            self.fetch_count += 1
            return items
        except Exception as e:
            self.error_count += 1
            raise ContentSourceError(f"Failed to fetch from {self.get_source_name()}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get source statistics"""
        return {
            'source_name': self.get_source_name(),
            'source_type': self.get_source_type(),
            'last_fetch': self.last_fetch.isoformat() if self.last_fetch else None,
            'fetch_count': self.fetch_count,
            'error_count': self.error_count,
        }


class ContentSourceError(Exception):
    """Base exception for content source errors"""
    pass


class RateLimitError(ContentSourceError):
    """Raised when source rate limit is hit"""
    pass


class AuthenticationError(ContentSourceError):
    """Raised when source authentication fails"""
    pass


# Utility functions for content filtering

def filter_by_keywords(items: List[ContentItem], keywords: List[str]) -> List[ContentItem]:
    """
    Filter content items by keywords in title/description.
    
    Args:
        items: List of ContentItem objects
        keywords: List of keywords to search for (case-insensitive)
        
    Returns:
        Filtered list of ContentItem objects
    """
    if not keywords:
        return items
    
    filtered = []
    keywords_lower = [k.lower() for k in keywords]
    
    for item in items:
        text = f"{item.title} {item.description}".lower()
        if any(keyword in text for keyword in keywords_lower):
            filtered.append(item)
    
    return filtered


def filter_by_quality(items: List[ContentItem], min_quality: ContentQuality = ContentQuality.MEDIUM) -> List[ContentItem]:
    """
    Filter content items by minimum quality level.
    
    Args:
        items: List of ContentItem objects
        min_quality: Minimum quality level (HIGH, MEDIUM, LOW)
        
    Returns:
        Filtered list of ContentItem objects
    """
    quality_order = {
        ContentQuality.HIGH: 3,
        ContentQuality.MEDIUM: 2,
        ContentQuality.LOW: 1,
    }
    
    min_score = quality_order.get(min_quality, 1)
    
    return [
        item for item in items
        if item.quality and quality_order.get(item.quality, 0) >= min_score
    ]


def deduplicate_by_url(items: List[ContentItem]) -> List[ContentItem]:
    """
    Remove duplicate content items by URL.
    
    Args:
        items: List of ContentItem objects
        
    Returns:
        Deduplicated list (keeps first occurrence)
    """
    seen_urls = set()
    unique_items = []
    
    for item in items:
        if item.url not in seen_urls:
            seen_urls.add(item.url)
            unique_items.append(item)
    
    return unique_items


def sort_by_relevance(items: List[ContentItem], reverse: bool = True) -> List[ContentItem]:
    """
    Sort content items by relevance score.
    
    Args:
        items: List of ContentItem objects
        reverse: If True, sort descending (highest first)
        
    Returns:
        Sorted list of ContentItem objects
    """
    return sorted(items, key=lambda x: x.relevance_score, reverse=reverse)
