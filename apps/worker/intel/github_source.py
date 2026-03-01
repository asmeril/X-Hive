"""
GitHub Trending Source for X-Hive

Scrapes trending repositories from github.com/trending
No API key required (public data).
"""

import aiohttp
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from typing import List, Optional, Dict
import re

from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory,
    ContentSourceError
)

logger = logging.getLogger(__name__)


class GitHubTrendingSource(BaseContentSource):
    """
    GitHub Trending repositories scraper.
    
    Scrapes trending repos from github.com/trending
    No API key required (public data).
    
    Features:
    - Language filtering (Python, JavaScript, etc.)
    - Time period filtering (daily, weekly, monthly)
    - Auto-categorization based on repo content
    - Stars/forks engagement metrics
    - AI/ML content prioritization
    """
    
    BASE_URL = "https://github.com/trending"
    
    # Language filters for AI/ML content
    AI_LANGUAGES = ['python', 'jupyter-notebook', 'c++', 'javascript', 'rust']
    
    def __init__(
        self,
        language: Optional[str] = None,
        since: str = 'daily',  # 'daily', 'weekly', 'monthly'
        max_repos: int = 25
    ):
        """
        Initialize GitHub Trending source.
        
        Args:
            language: Filter by language (e.g., 'python', 'javascript')
            since: Time period ('daily', 'weekly', 'monthly')
            max_repos: Maximum repos to fetch
        """
        
        super().__init__()
        
        self.language = language
        self.since = since
        self.max_repos = max_repos
    
    def get_source_name(self) -> str:
        """Return source name"""
        return "GitHub Trending"
    
    def get_source_type(self) -> str:
        """Return source type"""
        return "github"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch trending repositories from GitHub"""
        
        all_items = []
        
        # If no specific language, fetch from AI-focused languages
        languages = [self.language] if self.language else self.AI_LANGUAGES
        
        for lang in languages:
            try:
                items = await self._fetch_trending(lang)
                all_items.extend(items)
                
                logger.info(f"✅ Fetched {len(items)} repos from GitHub Trending ({lang or 'all'})")
            
            except Exception as e:
                logger.error(f"❌ Failed to fetch GitHub Trending ({lang}): {e}")
                continue
        
        # Deduplicate by URL
        seen = set()
        unique_items = []
        
        for item in all_items:
            if item.url not in seen:
                seen.add(item.url)
                unique_items.append(item)
        
        # Sort by relevance score
        unique_items.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return unique_items[:self.max_repos]
    
    async def _fetch_trending(self, language: Optional[str] = None) -> List[ContentItem]:
        """
        Fetch trending repos for a specific language.
        
        Args:
            language: Programming language filter
        
        Returns:
            List of ContentItem objects
        """
        
        # Build URL
        url = self.BASE_URL
        params = {'since': self.since}
        
        if language:
            url = f"{self.BASE_URL}/{language}"
        
        query_string = '&'.join(f"{k}={v}" for k, v in params.items())
        full_url = f"{url}?{query_string}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(full_url, timeout=10) as response:
                    if response.status != 200:
                        raise ContentSourceError(f"GitHub returned status {response.status}")
                    
                    html = await response.text()
            
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find repo cards
            articles = soup.find_all('article', class_='Box-row')
            
            items = []
            
            for article in articles:
                try:
                    item = self._parse_repo(article, language)
                    
                    if item:
                        items.append(item)
                    else:
                        logger.debug(f"Skipped article - failed to parse")
                
                except Exception as e:
                    logger.debug(f"Failed to parse repo: {e}", exc_info=True)
                    continue
            
            logger.info(f"Parsed {len(items)} items from {len(articles)} articles")
            
            return items
        
        except Exception as e:
            raise ContentSourceError(f"Failed to fetch GitHub Trending: {e}")
    
    def _parse_repo(self, article, language: Optional[str]) -> Optional[ContentItem]:
        """
        Parse GitHub repo article to ContentItem.
        
        Args:
            article: BeautifulSoup article element
            language: Language filter
        
        Returns:
            ContentItem or None
        """
        
        # Extract repo name and URL
        h2 = article.find('h2', class_='h3')
        
        if not h2:
            # Try alternative selector
            h2 = article.find('h2')
        
        if not h2:
            return None
        
        link = h2.find('a')
        
        if not link:
            return None
        
        repo_path = link.get('href', '').strip()
        repo_url = f"https://github.com{repo_path}"
        
        # Repo name (owner/repo)
        repo_name = repo_path.strip('/')
        
        # Extract description
        description_elem = article.find('p', class_='col-9')
        description = description_elem.get_text(strip=True) if description_elem else ""
        
        # Extract language
        lang_elem = article.find('span', itemprop='programmingLanguage')
        repo_language = lang_elem.get_text(strip=True) if lang_elem else (language or 'Unknown')
        
        # Extract stars (today)
        stars_today = 0
        stars_elem = article.find('span', class_='d-inline-block float-sm-right')
        
        if stars_elem:
            stars_text = stars_elem.get_text(strip=True)
            # Extract number (e.g., "1,234 stars today" -> 1234)
            match = re.search(r'([\d,]+)', stars_text)
            if match:
                stars_today = int(match.group(1).replace(',', ''))
        
        # Extract total stars
        total_stars = 0
        stars_link = article.find('a', href=re.compile(r'/stargazers$'))
        
        if stars_link:
            stars_text = stars_link.get_text(strip=True)
            match = re.search(r'([\d,]+)', stars_text)
            if match:
                total_stars = int(match.group(1).replace(',', ''))
        
        # Extract forks
        forks = 0
        forks_link = article.find('a', href=re.compile(r'/forks$'))
        
        if forks_link:
            forks_text = forks_link.get_text(strip=True)
            match = re.search(r'([\d,]+)', forks_text)
            if match:
                forks = int(match.group(1).replace(',', ''))
        
        # Auto-categorize
        category = self._auto_categorize(repo_name, description, repo_language)
        
        # Calculate scores
        relevance = self._calculate_relevance(description, repo_language, total_stars)
        engagement = self._calculate_engagement(stars_today, total_stars, forks)
        
        # Extract topics (hashtags)
        tags = [repo_language.lower()] if repo_language != 'Unknown' else []
        
        # Create title
        title = f"{repo_name} - {description[:100]}" if description else repo_name
        
        return ContentItem(
            title=title,
            url=repo_url,
            source_type='github',
            source_name='GitHub Trending',
            description=description,
            published_at=datetime.now(),  # Trending is "now"
            category=category,
            tags=tags,
            relevance_score=relevance,
            engagement_score=engagement,
            metadata={
                'repo_name': repo_name,
                'language': repo_language,
                'stars_today': stars_today,
                'total_stars': total_stars,
                'forks': forks
            }
        )
    
    def _auto_categorize(self, repo_name: str, description: str, language: str) -> ContentCategory:
        """Auto-categorize based on repo content"""
        
        text = f"{repo_name} {description}".lower()
        
        # AI/ML keywords (highest priority)
        ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'ml',
            'deep learning', 'neural', 'gpt', 'llm', 'transformer',
            'pytorch', 'tensorflow', 'model', 'training', 'inference',
            'diffusion', 'stable diffusion', 'chatbot', 'nlp', 'cv',
            'computer vision', 'openai', 'anthropic', 'gemini'
        ]
        
        if any(kw in text for kw in ai_keywords):
            return ContentCategory.AI_ML
        
        # Programming tools
        if any(kw in text for kw in ['framework', 'library', 'tool', 'cli', 'api', 'sdk']):
            return ContentCategory.PROGRAMMING
        
        # Blockchain/Crypto
        if any(kw in text for kw in ['blockchain', 'crypto', 'web3', 'ethereum', 'bitcoin']):
            return ContentCategory.BLOCKCHAIN
        
        # Productivity
        if any(kw in text for kw in ['productivity', 'automation', 'workflow', 'task']):
            return ContentCategory.PRODUCTIVITY
        
        # Cybersecurity
        if any(kw in text for kw in ['security', 'vulnerability', 'exploit', 'pentest', 'hacking']):
            return ContentCategory.CYBERSECURITY
        
        return ContentCategory.TECH_NEWS
    
    def _calculate_relevance(self, description: str, language: str, total_stars: int) -> float:
        """Calculate relevance score (0-1)"""
        
        score = 0.5  # Base
        
        # Boost for AI/ML keywords in description
        if any(kw in description.lower() for kw in ['ai', 'ml', 'learning', 'model', 'gpt', 'llm']):
            score += 0.3
        
        # Boost for popular languages
        if language.lower() in ['python', 'javascript', 'rust', 'typescript', 'go']:
            score += 0.1
        
        # Boost for high star count
        if total_stars > 10000:
            score += 0.1
        elif total_stars > 1000:
            score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_engagement(self, stars_today: int, total_stars: int, forks: int) -> float:
        """Calculate engagement score (0-1)"""
        
        # Normalize stars today (100+ = max)
        stars_score = min(stars_today / 100, 1.0) if stars_today > 0 else 0.0
        
        # Normalize total stars (10k+ = max)
        total_score = min(total_stars / 10000, 1.0) if total_stars > 0 else 0.0
        
        # Normalize forks (1k+ = max)
        forks_score = min(forks / 1000, 1.0) if forks > 0 else 0.0
        
        # Weighted average (today's stars matter most)
        return (stars_score * 0.5) + (total_score * 0.3) + (forks_score * 0.2)
    
    async def health_check(self) -> bool:
        """Check if GitHub Trending is accessible"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, timeout=5) as response:
                    return response.status == 200
        except:
            return False


# Predefined instances
github_trending_source = GitHubTrendingSource(
    since='daily',
    max_repos=25
)

github_ai_source = GitHubTrendingSource(
    language='python',
    since='weekly',
    max_repos=15
)


# Test example
async def test_github_source():
    """Test GitHub Trending source"""
    
    source = GitHubTrendingSource(since='daily', max_repos=10)
    
    print("Fetching GitHub Trending repos...")
    items = await source.fetch_latest()
    
    print(f"\n✅ Fetched {len(items)} repos\n")
    
    for idx, item in enumerate(items[:5], 1):
        print(f"{idx}. {item.title}")
        print(f"   URL: {item.url}")
        print(f"   Category: {item.category.name}")
        print(f"   Stars today: {item.metadata.get('stars_today', 0)}")
        print(f"   Total stars: {item.metadata.get('total_stars', 0)}")
        print(f"   Relevance: {item.relevance_score:.2f}")
        print(f"   Engagement: {item.engagement_score:.2f}")
        print()


# Global instance
github_source = GitHubTrendingSource()
