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
    """Content categories for classification"""
    AI_ML = "ai_ml"                              # 30% target
    TECH_PROGRAMMING = "tech_programming"        # 20% target
    STARTUP_BUSINESS = "startup_business"        # 15% target
    GAMING_ENTERTAINMENT = "gaming_entertainment" # 10% target
    CRYPTO_WEB3 = "crypto_web3"                  # 10% target
    MOBILE_APPS = "mobile_apps"                  # 5% target
    SECURITY_PRIVACY = "security_privacy"        # 5% target
    SCIENCE = "science"                          # 5% target


# Category distribution targets for balanced content
CATEGORY_TARGETS = {
    ContentCategory.AI_ML: 0.30,
    ContentCategory.TECH_PROGRAMMING: 0.20,
    ContentCategory.STARTUP_BUSINESS: 0.15,
    ContentCategory.GAMING_ENTERTAINMENT: 0.10,
    ContentCategory.CRYPTO_WEB3: 0.10,
    ContentCategory.MOBILE_APPS: 0.05,
    ContentCategory.SECURITY_PRIVACY: 0.05,
    ContentCategory.SCIENCE: 0.05,
}


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
    category: ContentCategory = ContentCategory.AI_ML
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
    
    def categorize_by_keywords(
        self, 
        text: str, 
        default: ContentCategory = None
    ) -> ContentCategory:
        """
        Auto-categorize content based on keywords.
        
        Args:
            text: Text to analyze (title + description)
            default: Default category if no match
            
        Returns:
            ContentCategory
        """
        text_lower = text.lower()
        
        # AI/ML keywords
        ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'ml',
            'deep learning', 'neural', 'llm', 'gpt', 'chatgpt',
            'gemini', 'claude', 'transformer', 'diffusion', 'model',
            'nlp', 'computer vision', 'image generation'
        ]
        if any(kw in text_lower for kw in ai_keywords):
            return ContentCategory.AI_ML
        
        # Crypto/Web3 keywords
        crypto_keywords = [
            'crypto', 'bitcoin', 'ethereum', 'blockchain',
            'web3', 'nft', 'defi', 'solana', 'dao', 'token',
            'cryptocurrency', 'smart contract'
        ]
        if any(kw in text_lower for kw in crypto_keywords):
            return ContentCategory.CRYPTO_WEB3
        
        # Gaming keywords
        gaming_keywords = [
            'game', 'gaming', 'gamedev', 'unity', 'unreal',
            'ps5', 'xbox', 'nintendo', 'steam', 'esports',
            'indie game', 'game engine'
        ]
        if any(kw in text_lower for kw in gaming_keywords):
            return ContentCategory.GAMING_ENTERTAINMENT
        
        # Security keywords
        security_keywords = [
            'security', 'vulnerability', 'hack', 'breach',
            'cyber', 'infosec', 'netsec', 'exploit', 'cve',
            'penetration', 'encryption', 'privacy'
        ]
        if any(kw in text_lower for kw in security_keywords):
            return ContentCategory.SECURITY_PRIVACY
        
        # Startup/Business keywords
        startup_keywords = [
            'startup', 'funding', 'vc', 'venture capital',
            'investment', 'yc', 'entrepreneur', 'saas', 'launch',
            'series a', 'seed round', 'pitch'
        ]
        if any(kw in text_lower for kw in startup_keywords):
            return ContentCategory.STARTUP_BUSINESS
        
        # Mobile/Apps keywords
        mobile_keywords = [
            'app', 'mobile', 'ios', 'android', 'iphone',
            'flutter', 'react native', 'swift', 'kotlin',
            'app store', 'google play'
        ]
        if any(kw in text_lower for kw in mobile_keywords):
            return ContentCategory.MOBILE_APPS
        
        # Science keywords
        science_keywords = [
            'science', 'research', 'study', 'physics',
            'chemistry', 'biology', 'astronomy', 'arxiv', 'paper',
            'scientific', 'discovery', 'experiment'
        ]
        if any(kw in text_lower for kw in science_keywords):
            return ContentCategory.SCIENCE
        
        # Default to tech/programming
        return default or ContentCategory.TECH_PROGRAMMING


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


def filter_by_category(items: List[ContentItem], categories: List[ContentCategory]) -> List[ContentItem]:
    """
    Filter content items by category.
    
    Args:
        items: List of ContentItem objects
        categories: List of ContentCategory to include
        
    Returns:
        Filtered list of ContentItem objects
    """
    if not categories:
        return items
    
    return [item for item in items if item.category in categories]


def group_by_category(items: List[ContentItem]) -> Dict[ContentCategory, List[ContentItem]]:
    """
    Group content items by category.
    
    Args:
        items: List of ContentItem objects
        
    Returns:
        Dictionary mapping ContentCategory to list of items
    """
    grouped: Dict[ContentCategory, List[ContentItem]] = {
        category: [] for category in ContentCategory
    }
    
    for item in items:
        grouped[item.category].append(item)
    
    return grouped


def get_category_distribution(items: List[ContentItem]) -> Dict[ContentCategory, float]:
    """
    Calculate the distribution of content across categories.
    
    Args:
        items: List of ContentItem objects
        
    Returns:
        Dictionary mapping ContentCategory to percentage (0.0-1.0)
    """
    if not items:
        return {category: 0.0 for category in ContentCategory}
    
    grouped = group_by_category(items)
    total = len(items)
    
    return {
        category: len(items_list) / total
        for category, items_list in grouped.items()
    }


def get_category_balance_score(items: List[ContentItem]) -> float:
    """
    Calculate how well content distribution matches target distribution.
    
    A score of 1.0 means perfect match with target distribution.
    A score of 0.0 means completely mismatched.
    
    Args:
        items: List of ContentItem objects
        
    Returns:
        Balance score (0.0-1.0)
    """
    if not items:
        return 0.0
    
    current_dist = get_category_distribution(items)
    
    # Calculate total difference from target
    total_diff = 0.0
    for category, target in CATEGORY_TARGETS.items():
        current = current_dist.get(category, 0.0)
        total_diff += abs(current - target)
    
    # Score is inversely proportional to total difference
    # Max difference is 2.0 (when completely opposite)
    balance_score = max(0.0, 1.0 - (total_diff / 2.0))
    
    return balance_score
