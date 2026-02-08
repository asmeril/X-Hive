"""
HuggingFace Trending Models, Papers, and Spaces Aggregator

Scrapes:
- Trending models
- Recent papers
- Trending Spaces (demos)
"""

import aiohttp
from bs4 import BeautifulSoup
import logging
from typing import List, Optional
from datetime import datetime, timezone
import re

from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory
)
from .cookie_loader import get_cookie_loader
from .cookie_manager import get_cookie_manager

logger = logging.getLogger(__name__)


class HuggingFaceSource(BaseContentSource):
    """
    HuggingFace trending models, papers, and spaces aggregator.
    
    Scrapes:
    - Trending models (with download/like counts)
    - Recent papers from HuggingFace Papers
    - Trending Spaces (AI demos and applications)
    """
    
    BASE_URL = "https://huggingface.co"
    
    def __init__(
        self,
        models_limit: int = 20,
        papers_limit: int = 20,
        spaces_limit: int = 10
    ):
        """
        Initialize HuggingFace scraper.
        
        Args:
            models_limit: Max trending models to fetch
            papers_limit: Max recent papers to fetch
            spaces_limit: Max trending spaces to fetch
        """
        super().__init__()
        
        # Initialize cookie manager for HuggingFace authentication
        self.cookie_manager = get_cookie_manager()
        self.models_limit = models_limit
        self.papers_limit = papers_limit
        self.spaces_limit = spaces_limit
        
        # Load cookies from huggingface.json if available
        cookies = self.cookie_manager.get_cookies_for_site_json('huggingface')
        if cookies:
            logger.info(f"✅ Loaded {len(cookies)} cookies for HuggingFace")
        else:
            logger.warning("⚠️  No HuggingFace cookies found - proceeding with public access")
        
        logger.info(
            f"✅ HuggingFaceSource initialized "
            f"(models={models_limit}, papers={papers_limit}, spaces={spaces_limit})"
        )
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "HuggingFace"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch trending models, papers, and spaces"""
        
        items = []
        
        # Fetch trending models
        try:
            models = await self._fetch_trending_models()
            items.extend(models)
            logger.debug(f"Fetched {len(models)} trending models")
        except Exception as e:
            logger.error(f"❌ Error fetching models: {e}")
        
        # Fetch recent papers
        try:
            papers = await self._fetch_recent_papers()
            items.extend(papers)
            logger.debug(f"Fetched {len(papers)} recent papers")
        except Exception as e:
            logger.error(f"❌ Error fetching papers: {e}")
        
        # Fetch trending spaces
        try:
            spaces = await self._fetch_trending_spaces()
            items.extend(spaces)
            logger.debug(f"Fetched {len(spaces)} trending spaces")
        except Exception as e:
            logger.error(f"❌ Error fetching spaces: {e}")
        
        logger.info(f"✅ HuggingFace: Fetched {len(items)} items")
        return items
    
    async def _fetch_trending_models(self) -> List[ContentItem]:
        """Fetch trending models from HuggingFace"""
        
        url = f"{self.BASE_URL}/models?sort=trending"
        
        items = []
        
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        }
        
        # Add HuggingFace cookies if available
        cookies = self.cookie_manager.get_cookies_for_site_json('huggingface')
        cookie_dict = cookies if cookies else {}
        if cookie_dict:
            logger.debug(f"Using {len(cookie_dict)} cookies for HuggingFace")
        
        try:
            async with aiohttp.ClientSession(cookies=cookie_dict) as session:
                async with session.get(
                    url, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    
                    if response.status != 200:
                        logger.warning(f"HTTP {response.status} for trending models")
                        return items
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find model cards
                    # HuggingFace uses article tags for model cards
                    model_cards = soup.find_all('article', limit=self.models_limit * 2)
                    
                    for card in model_cards[:self.models_limit]:
                        try:
                            # Get model link
                            link = card.find('a', href=True)
                            if not link:
                                continue
                            
                            model_url = link['href']
                            if not model_url.startswith('http'):
                                model_url = self.BASE_URL + model_url
                            
                            # Get model name (from URL or title)
                            model_name = model_url.split('/')[-1]
                            
                            # Try to get display name
                            title_elem = card.find(['h3', 'h4'])
                            if title_elem:
                                display_name = title_elem.get_text(strip=True)
                            else:
                                display_name = model_name
                            
                            # Get description
                            desc_elem = card.find('p')
                            description = desc_elem.get_text(strip=True) if desc_elem else None
                            
                            # Get downloads/likes count
                            downloads = 0
                            likes = 0
                            
                            stats = card.find_all('span')
                            for stat in stats:
                                text = stat.get_text(strip=True)
                                if 'download' in text.lower():
                                    downloads = self._parse_number(text)
                                elif 'like' in text.lower():
                                    likes = self._parse_number(text)
                            
                            # Create item
                            item = ContentItem(
                                title=f"🤗 {display_name}",
                                url=model_url,
                                source_type='huggingface',
                                source_name='HuggingFace - Models',
                                published_at=datetime.now(timezone.utc),
                                category=ContentCategory.AI_ML,
                                description=description
                            )
                            
                            # Calculate scores based on popularity
                            item.relevance_score = min(0.9, 0.6 + (downloads / 100000))
                            item.engagement_score = min(0.9, 0.5 + (likes / 1000))
                            
                            items.append(item)
                        
                        except Exception as e:
                            logger.debug(f"Error parsing model card: {e}")
                            continue
        
        except Exception as e:
            logger.error(f"❌ Error fetching trending models: {e}")
        
        return items
    
    async def _fetch_recent_papers(self) -> List[ContentItem]:
        """Fetch recent papers from HuggingFace Papers"""
        
        url = f"{self.BASE_URL}/papers"
        
        items = []
        
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        }
        
        # Add HuggingFace cookies if available
        cookies = self.cookie_manager.get_cookies_for_site_json('huggingface')
        cookie_dict = cookies if cookies else {}
        if cookie_dict:
            logger.debug(f"Using {len(cookie_dict)} cookies for HuggingFace")
        
        try:
            async with aiohttp.ClientSession(cookies=cookie_dict) as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    
                    if response.status != 200:
                        logger.warning(f"HTTP {response.status} for papers")
                        return items
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find paper cards
                    paper_cards = soup.find_all('article', limit=self.papers_limit * 2)
                    
                    for card in paper_cards[:self.papers_limit]:
                        try:
                            # Get paper link
                            link = card.find('a', href=True)
                            if not link:
                                continue
                            
                            paper_url = link['href']
                            if not paper_url.startswith('http'):
                                paper_url = self.BASE_URL + paper_url
                            
                            # Get title
                            title_elem = card.find(['h3', 'h4'])
                            if not title_elem:
                                continue
                            
                            title = title_elem.get_text(strip=True)
                            
                            # Get abstract
                            abstract_elem = card.find('p')
                            abstract = abstract_elem.get_text(strip=True) if abstract_elem else None
                            
                            # Create item
                            item = ContentItem(
                                title=f"📄 {title}",
                                url=paper_url,
                                source_type='huggingface',
                                source_name='HuggingFace - Papers',
                                published_at=datetime.now(timezone.utc),
                                category=ContentCategory.AI_ML,
                                description=abstract[:300] if abstract else None
                            )
                            
                            item.relevance_score = 0.85
                            item.engagement_score = 0.75
                            
                            items.append(item)
                        
                        except Exception as e:
                            logger.debug(f"Error parsing paper card: {e}")
                            continue
        
        except Exception as e:
            logger.error(f"❌ Error fetching papers: {e}")
        
        return items
    
    async def _fetch_trending_spaces(self) -> List[ContentItem]:
        """Fetch trending Spaces (AI demos and applications)"""
        
        url = f"{self.BASE_URL}/spaces?sort=trending"
        
        items = []
        
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        }
        
        # Add HuggingFace cookies if available
        cookies = self.cookie_manager.get_cookies_for_site_json('huggingface')
        cookie_dict = cookies if cookies else {}
        if cookie_dict:
            logger.debug(f"Using {len(cookie_dict)} cookies for HuggingFace")
        
        try:
            async with aiohttp.ClientSession(cookies=cookie_dict) as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    
                    if response.status != 200:
                        logger.warning(f"HTTP {response.status} for spaces")
                        return items
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find space cards
                    space_cards = soup.find_all('article', limit=self.spaces_limit * 2)
                    
                    for card in space_cards[:self.spaces_limit]:
                        try:
                            # Get space link
                            link = card.find('a', href=True)
                            if not link:
                                continue
                            
                            space_url = link['href']
                            if not space_url.startswith('http'):
                                space_url = self.BASE_URL + space_url
                            
                            # Get title
                            title_elem = card.find(['h3', 'h4'])
                            if not title_elem:
                                continue
                            
                            title = title_elem.get_text(strip=True)
                            
                            # Get description
                            desc_elem = card.find('p')
                            description = desc_elem.get_text(strip=True) if desc_elem else None
                            
                            # Create item
                            item = ContentItem(
                                title=f"🚀 {title}",
                                url=space_url,
                                source_type='huggingface',
                                source_name='HuggingFace - Spaces',
                                published_at=datetime.now(timezone.utc),
                                category=ContentCategory.AI_ML,
                                description=description
                            )
                            
                            item.relevance_score = 0.75
                            item.engagement_score = 0.7
                            
                            items.append(item)
                        
                        except Exception as e:
                            logger.debug(f"Error parsing space card: {e}")
                            continue
        
        except Exception as e:
            logger.error(f"❌ Error fetching spaces: {e}")
        
        return items
    
    def _parse_number(self, text: str) -> int:
        """Parse number from text (e.g., '1.2k' -> 1200)"""
        try:
            text = text.strip().lower()
            
            # Remove non-numeric except k, m, b
            clean = re.sub(r'[^\d.kmb]', '', text)
            
            if 'k' in clean:
                return int(float(clean.replace('k', '')) * 1000)
            elif 'm' in clean:
                return int(float(clean.replace('m', '')) * 1000000)
            elif 'b' in clean:
                return int(float(clean.replace('b', '')) * 1000000000)
            else:
                return int(float(clean)) if clean else 0
        except:
            return 0


# Global instance
huggingface_source = HuggingFaceSource()
