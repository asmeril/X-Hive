import re
from typing import List, Set, Tuple


STOPWORDS: Set[str] = {
    "the", "and", "for", "with", "this", "that", "from", "have", "will", "your", "about", "into", "over",
    "bir", "ve", "ile", "için", "gibi", "olan", "olan", "daha", "çok", "şöyle", "böyle", "ancak", "olarak",
    "tweet", "thread", "reply", "yaz", "detay", "konu", "haber", "göre", "max", "kadar", "sadece",
}


def _tokenize(value: str) -> List[str]:
    normalized = re.sub(r"[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ\s]", " ", (value or "").lower())
    tokens = [token.strip() for token in normalized.split() if token.strip()]
    return [token for token in tokens if len(token) >= 4 and token not in STOPWORDS]


def build_focus_keywords(title: str, body: str, limit: int = 14) -> List[str]:
    tokens = _tokenize(f"{title} {body}")
    uniq: List[str] = []
    seen = set()
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        uniq.append(token)
        if len(uniq) >= limit:
            break
    return uniq


def relevance_score(tweet_text: str, focus_keywords: List[str]) -> Tuple[int, List[str]]:
    lower_tweet = (tweet_text or "").lower()
    hits = [keyword for keyword in focus_keywords if keyword in lower_tweet]
    return len(hits), hits


def is_relevant_for_sniper(tweet_text: str, focus_keywords: List[str], minimum_hits: int = 2) -> Tuple[bool, int, List[str]]:
    score, hits = relevance_score(tweet_text, focus_keywords)
    return score >= minimum_hits, score, hits
