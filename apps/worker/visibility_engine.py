"""
X-Hive Visibility Engine — Dağıtım & Görünürlük Stratejileri

4 temel strateji:
1. Akıllı Etiketleme (Smart Mentioning) — İçerikte geçen kişi/şirketlerin X handle'ını bul
2. Trend Anahtar Kelime Enjeksiyonu — Şu an X'te trend olan kelimeleri thread'e doğal yedir
3. Görsel Çekme (Image Extraction) — Kaynak haberin OG image'ını indir
4. Sniper Reply — Büyük hesapların tweetlerine saniyeler içinde akıllı reply at

Tüm fonksiyonlar async, pipeline'a takılabilir şekilde tasarlandı.
"""

import asyncio
import aiohttp
import logging
import re
import json
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# 1. SMART MENTIONING — Akıllı Etiketleme
# ═══════════════════════════════════════════════════════════

# Bilinen şirket/kişi → X handle eşlemesi (güncellenebilir)
KNOWN_HANDLES: Dict[str, str] = {
    # AI Companies
    "openai": "@OpenAI",
    "open ai": "@OpenAI",
    "chatgpt": "@OpenAI",
    "gpt-4": "@OpenAI",
    "gpt-5": "@OpenAI",
    "gpt4": "@OpenAI",
    "gpt5": "@OpenAI",
    "sam altman": "@sama",
    "altman": "@sama",
    "anthropic": "@AnthropicAI",
    "claude": "@AnthropicAI",
    "google": "@Google",
    "google ai": "@GoogleAI",
    "gemini": "@GoogleAI",
    "deepmind": "@GoogleDeepMind",
    "demis hassabis": "@demaborland",
    "meta ai": "@MetaAI",
    "meta": "@Meta",
    "llama": "@MetaAI",
    "mark zuckerberg": "@faborland",
    "zuckerberg": "@faborland",
    "mistral": "@MistralAI",
    "mistral ai": "@MistralAI",
    "hugging face": "@huggingface",
    "huggingface": "@huggingface",
    "stability ai": "@StabilityAI",
    "midjourney": "@midaborland",
    "cohere": "@CohereAI",
    "nvidia": "@nvidia",
    "jensen huang": "@nvidia",
    "perplexity": "@perplexity_ai",
    "groq": "@GroqInc",
    "xai": "@xaborland",
    "grok": "@xaborland",

    # Tech Giants
    "apple": "@Apple",
    "tim cook": "@tim_cook",
    "microsoft": "@Microsoft",
    "satya nadella": "@sataborland",
    "amazon": "@amazon",
    "aws": "@awscloud",
    "tesla": "@Tesla",
    "elon musk": "@elonmusk",
    "spacex": "@SpaceX",

    # Crypto/Web3
    "bitcoin": "@Bitcoin",
    "ethereum": "@ethereum",
    "vitalik": "@VitalikButerin",
    "vitalik buterin": "@VitalikButerin",
    "binance": "@binance",
    "coinbase": "@coinbase",
    "solana": "@solana",

    # AI Researchers / Influencers
    "andrej karpathy": "@karpathy",
    "karpathy": "@karpathy",
    "yann lecun": "@ylecun",
    "lecun": "@ylecun",
    "andrew ng": "@AndrewYNg",
    "ilya sutskever": "@ilyasut",
    "dario amodei": "@DarioAmodei",
    "jim fan": "@DrJimFan",
    "emad mostaque": "@EMostaque",
    
    # Startup / VC
    "y combinator": "@ycombinator",
    "yc": "@ycombinator",
    "paul graham": "@paulg",
    "a16z": "@a16z",
    "marc andreessen": "@pmarca",
    "sequoia": "@sequoia",
    
    # News Sources
    "techcrunch": "@TechCrunch",
    "the verge": "@verge",
    "wired": "@WIRED",
    "ars technica": "@aaborland",
    "mit technology review": "@techreview",
    "bloomberg": "@business",
    "reuters": "@Reuters",
}


async def extract_mentions(title: str, summary: str = "") -> List[str]:
    """
    İçerikten otomatik X handle'ları çıkar.
    Haber başlığı ve özetinden KNOWN_HANDLES sözlüğüne bakarak eşleşenleri döndürür.
    
    Args:
        title: Haber başlığı
        summary: Haber özeti
        
    Returns:
        Deduplicated list of X handles (e.g. ["@OpenAI", "@sama"])
    """
    text = f"{title} {summary}".lower()
    found_handles = []
    
    # Uzun key'lerden kısa key'lere sırala (daha spesifik eşleşmeleri önce bul)
    sorted_keys = sorted(KNOWN_HANDLES.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        if key in text:
            handle = KNOWN_HANDLES[key]
            if handle not in found_handles:
                found_handles.append(handle)
    
    # Max 3 mention (çok fazla mention spam sayılır)
    result = found_handles[:3]
    if result:
        logger.info(f"🏷️ Smart mentions extracted: {result}")
    return result


# ═══════════════════════════════════════════════════════════
# 2. TREND KEYWORD INJECTION — Trend Anahtar Kelime
# ═══════════════════════════════════════════════════════════

# Statik trend keyword havuzu (periyodik olarak güncellenebilir)
# Bu liste AI tarafından güncellenecek, veya Google Trends'ten çekilecek
EVERGREEN_KEYWORDS = [
    "AI", "AGI", "LLM", "GPT", "Machine Learning",
    "Crypto", "Bitcoin", "DeFi", "Web3",
    "Startup", "VC", "Funding",
    "Open Source", "Developer",
]


async def get_trending_keywords() -> List[str]:
    """
    X'te şu an trend olan anahtar kelimeleri çek.
    Önce Google Trends'ten çekmeye çalış, başarısız olursa statik listeyi kullan.
    
    Returns:
        List of trending keyword strings
    """
    try:
        # Google Trends source'undan çekmeyi dene
        from intel.google_trends_source import GoogleTrendsSource
        gt = GoogleTrendsSource()
        items = await gt.fetch_latest()
        
        # Trend başlıklarını keyword olarak kullan
        keywords = [item.title for item in items[:10] if hasattr(item, 'title')]
        if keywords:
            logger.info(f"📈 Live trending keywords: {keywords[:5]}...")
            return keywords
    except Exception as e:
        logger.warning(f"⚠️ Could not fetch live trends: {e}")
    
    # Fallback: Evergreen keywords
    logger.info(f"📈 Using evergreen keywords (live fetch failed)")
    return EVERGREEN_KEYWORDS


async def suggest_keywords_for_content(title: str, summary: str = "") -> List[str]:
    """
    İçerik için en uygun 2-3 aranabilir anahtar kelimeyi öner.
    Hashtag DEĞİL — doğal metin içine yerleştirilecek kelimeler.
    
    Args:
        title: Haber başlığı
        summary: Haber özeti/detayı
        
    Returns:
        List of 2-3 keywords to weave into thread text
    """
    text = f"{title} {summary}".lower()
    
    # Kategorize et ve uygun anahtar kelimeleri bul
    keyword_map = {
        "ai": ["AI", "yapay zeka", "artificial intelligence"],
        "gpt": ["GPT", "LLM", "ChatGPT"],
        "llm": ["LLM", "large language model"],
        "machine learning": ["Machine Learning", "ML"],
        "deep learning": ["Deep Learning", "AI"],
        "neural": ["neural network", "AI"],
        "bitcoin": ["Bitcoin", "BTC", "Crypto"],
        "ethereum": ["Ethereum", "ETH", "DeFi"],
        "crypto": ["Crypto", "blockchain", "Web3"],
        "blockchain": ["blockchain", "Web3"],
        "startup": ["startup", "girişim"],
        "funding": ["funding", "yatırım", "VC"],
        "open source": ["open source", "açık kaynak"],
        "python": ["Python", "programming"],
        "developer": ["developer", "geliştirici"],
        "robotics": ["robotics", "robot"],
        "quantum": ["quantum computing", "kuantum"],
        "cybersecurity": ["cybersecurity", "siber güvenlik"],
        "apple": ["Apple", "iPhone", "iOS"],
        "google": ["Google", "Gemini"],
        "microsoft": ["Microsoft", "Copilot"],
        "tesla": ["Tesla", "EV"],
        "spacex": ["SpaceX", "uzay"],
    }
    
    found = []
    for key, keywords in keyword_map.items():
        if key in text:
            for kw in keywords:
                if kw not in found:
                    found.append(kw)
    
    # Max 3 keyword
    result = found[:3]
    if result:
        logger.info(f"🔑 Suggested keywords: {result}")
    return result


# ═══════════════════════════════════════════════════════════
# 3. IMAGE EXTRACTION — Görsel Çekme (OG Image)
# ═══════════════════════════════════════════════════════════

async def extract_og_image(url: str) -> Optional[str]:
    """
    Bir URL'den Open Graph (og:image) görselini çek.
    X/Twitter, görsel içeren tweetleri %300 daha fazla gösterir.
    
    Args:
        url: Haber/makale URL'si
        
    Returns:
        OG image URL string, veya None
    """
    if not url or not url.startswith("http"):
        return None
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
        }
        
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers, allow_redirects=True, ssl=False) as resp:
                if resp.status != 200:
                    return None
                
                html = await resp.text()
                
                # og:image meta tag'ini bul
                patterns = [
                    r'<meta\s+property=["\']og:image["\']\s+content=["\'](.*?)["\']',
                    r'<meta\s+content=["\'](.*?)["\']\s+property=["\']og:image["\']',
                    r'<meta\s+name=["\']twitter:image["\']\s+content=["\'](.*?)["\']',
                    r'<meta\s+content=["\'](.*?)["\']\s+name=["\']twitter:image["\']',
                    r'<meta\s+name=["\']twitter:image:src["\']\s+content=["\'](.*?)["\']',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        img_url = match.group(1)
                        # Relative URL'yi absolute'a çevir
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        elif img_url.startswith("/"):
                            parsed = urlparse(url)
                            img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
                        
                        logger.info(f"🖼️ OG image found: {img_url[:80]}...")
                        return img_url
                
                logger.debug(f"🖼️ No OG image found for: {url[:60]}")
                return None
                
    except Exception as e:
        logger.warning(f"⚠️ OG image extraction failed for {url[:60]}: {e}")
        return None


async def download_image(image_url: str, save_dir: str = "data/images") -> Optional[str]:
    """
    Görseli indirip yerel dosyaya kaydet.
    
    Args:
        image_url: İndirilecek görsel URL'si
        save_dir: Kayıt dizini
        
    Returns:
        Yerel dosya yolu, veya None
    """
    if not image_url:
        return None
    
    try:
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Dosya adı oluştur
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = ".jpg"  # Varsayılan
        parsed_url = urlparse(image_url)
        path_ext = Path(parsed_url.path).suffix
        if path_ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            ext = path_ext
        
        filename = f"og_{timestamp}{ext}"
        filepath = save_path / filename
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(image_url, headers=headers, ssl=False) as resp:
                if resp.status != 200:
                    return None
                
                content = await resp.read()
                if len(content) < 1000:  # Çok küçük, muhtemelen hata
                    return None
                
                with open(filepath, 'wb') as f:
                    f.write(content)
                
                logger.info(f"🖼️ Image downloaded: {filepath} ({len(content) // 1024}KB)")
                return str(filepath)
                
    except Exception as e:
        logger.warning(f"⚠️ Image download failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# 4. SNIPER REPLY — Büyük Hesaplara Akıllı Reply
# ═══════════════════════════════════════════════════════════

# İzlenecek büyük hesaplar ve konuları
#
# trigger_topics: Bunlardan EN AZ BİRİ metinde geçmezse bu hedef hiç seçilmez.
#   → Dar ve spesifik tutulmalı. "AI" gibi genel kelimeler konulmamalı.
# score_topics:   Eşleşince puanı artırır ama tek başına nitelendirmez.
# priority:       0-10 arası temel öncelik puanı.
#
SNIPER_TARGETS: Dict[str, Dict[str, Any]] = {
    "sama": {
        "name": "Sam Altman",
        "trigger_topics": ["openai", "sam altman", "chatgpt", "gpt-5", "gpt5", "altman", "agi"],
        "score_topics": ["AI", "startup", "GPT"],
        "priority": 10,
    },
    "elonmusk": {
        "name": "Elon Musk",
        "trigger_topics": ["elon musk", "tesla", "spacex", "xai", "grok", "musk", "x.com"],
        "score_topics": ["AI", "twitter", "electric vehicle"],
        "priority": 10,
    },
    "karpathy": {
        "name": "Andrej Karpathy",
        "trigger_topics": ["karpathy", "nanogpt", "minbpe", "neural network", "deep learning", "backpropagation"],
        "score_topics": ["LLM", "AI research", "ML"],
        "priority": 9,
    },
    "ylecun": {
        "name": "Yann LeCun",
        "trigger_topics": ["yann lecun", "lecun", "meta ai", "world model", "objective-driven ai"],
        "score_topics": ["deep learning", "AI research", "ML"],
        "priority": 8,
    },
    "AnthropicAI": {
        "name": "Anthropic",
        "trigger_topics": ["anthropic", "claude", "claude 3", "constitutional ai", "dario amodei"],
        "score_topics": ["AI safety", "LLM"],
        "priority": 8,
    },
    "OpenAI": {
        "name": "OpenAI",
        "trigger_topics": ["openai", "chatgpt", "gpt-4", "gpt-5", "gpt4", "gpt5", "dall-e", "sora", "o1", "o3"],
        "score_topics": ["AGI", "API", "AI"],
        "priority": 9,
    },
    "GoogleDeepMind": {
        "name": "Google DeepMind",
        "trigger_topics": ["deepmind", "gemini", "demis hassabis", "alphafold", "gemma"],
        "score_topics": ["AI research", "google ai"],
        "priority": 8,
    },
    "MistralAI": {
        "name": "Mistral AI",
        "trigger_topics": ["mistral", "mixtral", "le chat", "mistral ai"],
        "score_topics": ["open source AI", "LLM"],
        "priority": 7,
    },
    "huggingface": {
        "name": "Hugging Face",
        "trigger_topics": ["hugging face", "huggingface", "transformers library", "spaces", "gradio", "diffusers"],
        "score_topics": ["open source", "model hub"],
        "priority": 7,
    },
    "TechCrunch": {
        "name": "TechCrunch",
        "trigger_topics": ["techcrunch", "startup funding", "series a", "series b", "ipo", "acquisition"],
        "score_topics": ["startup", "tech", "funding"],
        "priority": 6,
    },
    "verge": {
        "name": "The Verge",
        "trigger_topics": ["the verge", "consumer tech", "apple event", "android", "pixel", "iphone"],
        "score_topics": ["gadgets", "software review"],
        "priority": 6,
    },
    "VitalikButerin": {
        "name": "Vitalik Buterin",
        "trigger_topics": ["vitalik", "ethereum", "eth", "defi", "web3", "smart contract", "blockchain"],
        "score_topics": ["crypto", "decentralized"],
        "priority": 7,
    },
    "pmarca": {
        "name": "Marc Andreessen",
        "trigger_topics": ["andreessen", "a16z", "marc andreessen", "pmarca"],
        "score_topics": ["VC", "venture capital", "startup"],
        "priority": 7,
    },
    "paulg": {
        "name": "Paul Graham",
        "trigger_topics": ["paul graham", "y combinator", "ycombinator", "pg essay"],
        "score_topics": ["startup", "programming"],
        "priority": 7,
    },
    "NASA": {
        "name": "NASA",
        "trigger_topics": ["nasa", "space mission", "mars", "moon", "artemis", "rocket launch", "iss"],
        "score_topics": ["space", "astronomy"],
        "priority": 6,
    },
    "Reuters": {
        "name": "Reuters",
        "trigger_topics": ["reuters", "breaking news", "geopolitics", "war", "iran", "sanctions", "military"],
        "score_topics": ["news", "international"],
        "priority": 6,
    },
    "awscloud": {
        "name": "AWS",
        "trigger_topics": ["amazon web services", "aws", "amazon cloud", "ec2", "s3 bucket", "lambda"],
        "score_topics": ["cloud computing", "devops"],
        "priority": 6,
    },
    "binance": {
        "name": "Binance",
        "trigger_topics": ["binance", "bnb", "cz binance", "changpeng zhao", "crypto exchange"],
        "score_topics": ["crypto", "trading"],
        "priority": 6,
    },
}


def find_sniper_targets(title: str, summary: str = "") -> List[Dict[str, Any]]:
    """
    İçerik konusuna göre hangi büyük hesapların tweetlerine reply atılabileceğini belirle.

    Kural:
    - trigger_topics listesinden EN AZ BİRİ metinde geçmeli, VEYA hesabın adı geçmeli.
    - Sadece genel "AI" / "ML" gibi kelimeler eşleşirse → o hedef SEÇİLMEZ.
    - score_topics eşleşmeleri yalnızca puanı artırır.

    Returns:
        List of matching sniper targets with username and priority (max 4)
    """
    text = f"{title} {summary}".lower()
    matches = []

    for username, info in SNIPER_TARGETS.items():
        trigger_topics = [t.lower() for t in info.get("trigger_topics", [])]
        score_topics   = [t.lower() for t in info.get("score_topics", [])]

        # Tetikleyici: hesap adı/username geçiyor mu?
        name_match = info["name"].lower() in text or username.lower() in text

        # Tetikleyici: trigger_topics'ten en az biri geçiyor mu?
        trigger_hit = any(t in text for t in trigger_topics)

        # Nitelendirme koşulu: name_match VEYA trigger_hit gerekli
        if not (name_match or trigger_hit):
            continue

        # Puan hesapla
        trigger_count = sum(1 for t in trigger_topics if t in text)
        score_count   = sum(1 for t in score_topics   if t in text)
        score = trigger_count * 3 + score_count * 1 + (4 if name_match else 0) + info["priority"]

        matches.append({
            "username": username,
            "handle": f"@{username}",
            "name": info["name"],
            "relevance_score": score,
            "topic_matches": trigger_count + score_count,
        })

    # Skora göre sırala, max 4 hedef döndür
    matches.sort(key=lambda x: x["relevance_score"], reverse=True)
    result = matches[:4]
    if result:
        logger.info(f"🎯 Sniper targets found: {[m['handle'] for m in result]}")
    else:
        logger.debug("🎯 No sniper targets matched for this content")
    return result


# ═══════════════════════════════════════════════════════════
# PIPELINE: Tüm görünürlük stratejilerini tek seferde çalıştır
# ═══════════════════════════════════════════════════════════

async def enrich_content_visibility(content_item, summary: str = "") -> Dict[str, Any]:
    """
    Tek bir içerik item'ı için tüm görünürlük verilerini topla.
    
    Bu fonksiyon pipeline'a takılarak her thread için:
    - Mention handle'ları
    - Trend keyword'leri  
    - OG image URL'si
    - Sniper reply targetları
    
    döndürür.
    
    Args:
        content_item: ContentItem veya dict
        summary: Ek özet bilgisi
        
    Returns:
        Dict with visibility enrichment data
    """
    # Field extraction
    if hasattr(content_item, 'title'):
        title = content_item.title or ""
        url = content_item.url or ""
        desc = content_item.ai_summary or getattr(content_item, 'description', '') or ""
    else:
        title = content_item.get("title", "")
        url = content_item.get("url", "")
        desc = content_item.get("ai_summary", content_item.get("summary", content_item.get("description", "")))
    
    full_summary = f"{desc} {summary}".strip()
    
    # Paralel olarak 4 stratejiyi çalıştır
    mentions_task = extract_mentions(title, full_summary)
    keywords_task = suggest_keywords_for_content(title, full_summary)
    image_task = extract_og_image(url)
    # Sniper reply sync fonksiyon, asyncio.to_thread ile sar
    sniper_result = find_sniper_targets(title, full_summary)
    
    mentions, keywords, image_url = await asyncio.gather(
        mentions_task, keywords_task, image_task
    )
    
    result = {
        "mentions": mentions,         # ["@OpenAI", "@sama"]
        "keywords": keywords,         # ["AI", "GPT", "LLM"]
        "image_url": image_url,       # "https://example.com/og.jpg" or None
        "sniper_targets": sniper_result,  # [{username, handle, name, score}]
    }
    
    logger.info(
        f"🔍 Visibility enriched: "
        f"{len(mentions)} mentions, "
        f"{len(keywords)} keywords, "
        f"{'🖼️ image' if image_url else '❌ no image'}, "
        f"{len(sniper_result)} sniper targets"
    )
    
    return result


async def enrich_batch(items_with_scores: List[Dict]) -> List[Dict]:
    """
    Birden fazla scored item için visibility verilerini topla.
    
    Args:
        items_with_scores: generate_viral_threads'den gelen [{item, viral_score, tr_thread, en_thread}]
        
    Returns:
        Aynı liste, ama her dict'e mentions, keywords, image_url, sniper_targets eklenir
    """
    logger.info(f"🔍 Enriching visibility for {len(items_with_scores)} items...")
    
    tasks = []
    for entry in items_with_scores:
        item = entry["item"]
        tasks.append(enrich_content_visibility(item))
    
    # Paralel çalıştır (ama rate limit korumasıyla)
    enrichments = []
    for i, task in enumerate(tasks):
        try:
            result = await task
            enrichments.append(result)
        except Exception as e:
            logger.error(f"⚠️ Visibility enrichment failed for item {i}: {e}")
            enrichments.append({
                "mentions": [],
                "keywords": [],
                "image_url": None,
                "sniper_targets": [],
            })
        
        # Rate limiting (image fetch -> HTTP call)
        if i < len(tasks) - 1:
            await asyncio.sleep(0.5)
    
    # Merge enrichment data into original entries
    for entry, enrichment in zip(items_with_scores, enrichments):
        entry["mentions"] = enrichment["mentions"]
        entry["keywords"] = enrichment["keywords"]
        entry["image_url"] = enrichment["image_url"]
        entry["sniper_targets"] = enrichment["sniper_targets"]
    
    logger.info(f"✅ Visibility enrichment complete for {len(items_with_scores)} items")
    return items_with_scores
