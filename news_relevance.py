"""Shared editorial filter for Nova Brief's student-focused technology news."""

import html
import math
import re
from typing import Any, Dict, Iterable, List, Tuple


# Keep this list intentionally broad enough to cover the global technology industry,
# while requiring a meaningful company or technology match before publication.
COMPANY_TERMS: Dict[str, Tuple[str, ...]] = {
    "NVIDIA": ("nvidia", "geforce", "cuda"),
    "Google": ("google", "alphabet", "deepmind", "gemini", "waymo", "youtube"),
    "Amazon": ("amazon", "aws", "amazon web services", "alexa"),
    "Microsoft": ("microsoft", "azure", "copilot", "github"),
    "OpenAI": ("openai", "chatgpt", "sora"),
    "Meta": ("meta", "facebook", "instagram", "whatsapp", "llama"),
    "Apple": ("apple", "iphone", "ipad", "macbook", "apple intelligence"),
    "Anthropic": ("anthropic", "claude"),
    "xAI": ("xai", "grok"),
    "Tesla": ("tesla", "optimus"),
    "IBM": ("ibm", "watsonx"),
    "Intel": ("intel",),
    "AMD": ("amd", "ryzen"),
    "Qualcomm": ("qualcomm", "snapdragon"),
    "Oracle": ("oracle",),
    "Salesforce": ("salesforce", "agentforce"),
    "Adobe": ("adobe", "firefly"),
    "Samsung": ("samsung",),
    "TSMC": ("tsmc", "taiwan semiconductor"),
    "ASML": ("asml",),
    "Arm": ("arm holdings", "arm chip", "arm-based"),
    "ByteDance": ("bytedance", "tiktok"),
    "SpaceX": ("spacex", "starlink"),
    "Hugging Face": ("hugging face", "huggingface"),
    "Mistral AI": ("mistral ai",),
    "Cohere": ("cohere",),
    "Perplexity": ("perplexity ai",),
    "Cisco": ("cisco",),
    "Cloudflare": ("cloudflare",),
    "Dell": ("dell technologies", "dell computer", "dell laptop"),
    "HP": ("hewlett packard", "hp enterprise", "hpe"),
    "Lenovo": ("lenovo",),
    "Sony": ("sony", "playstation"),
    "SAP": ("sap",),
    "Mozilla": ("mozilla", "firefox"),
    "Red Hat": ("red hat",),
    "Canonical": ("canonical", "ubuntu"),
    "GitLab": ("gitlab",),
    "Databricks": ("databricks",),
    "Snowflake": ("snowflake computing", "snowflake data cloud"),
}

TOPIC_TERMS: Dict[str, Tuple[str, ...]] = {
    "Artificial intelligence": (
        "ai", "artificial intelligence", "generative ai", "genai", "machine learning",
        "large language model", "language model", "foundation model", "multimodal model",
        "ai model", "ai agent", "ai agents", "agentic ai", "computer vision",
        "neural network", "deep learning", "ai safety", "ai research",
    ),
    "AI products": (
        "chatbot", "copilot", "text-to-image", "text to image", "image generator",
        "voice model", "reasoning model", "model release", "model launch",
    ),
    "Chips and computing": (
        "semiconductor", "microchip", "ai chip", "gpu", "processor", "data center",
        "datacenter", "supercomputer", "high-performance computing", "quantum computing",
    ),
    "Cloud and developers": (
        "cloud computing", "cloud platform", "developer tools", "software development",
        "open source", "open-source", "programming language", "coding assistant", "api release",
    ),
    "Programming and software": (
        "programming", "coding", "software engineering", "web development", "app development",
        "mobile development", "python", "javascript", "typescript", "java programming", "golang",
        "rust language", "c++", "developer framework", "code editor", "ide update", "git repository",
        "linux kernel", "operating system", "database technology", "database release", "devops",
        "kubernetes", "docker", "container platform", "web browser", "browser engine",
    ),
    "Cybersecurity": (
        "cybersecurity", "cyber security", "data breach", "ransomware", "malware",
        "vulnerability", "zero-day", "zero day", "privacy technology",
    ),
    "Robotics and emerging tech": (
        "robotics", "humanoid robot", "autonomous vehicle", "self-driving", "spatial computing",
        "augmented reality", "virtual reality", "satellite internet", "fusion energy",
    ),
    "Science and future technology": (
        "space technology", "space mission", "satellite technology", "rocket technology",
        "biotechnology", "health technology", "medical technology", "digital health",
        "battery technology", "clean energy technology", "renewable technology", "electric vehicle",
        "5g network", "6g network", "telecommunications", "internet infrastructure",
        "edge computing", "internet of things", "iot security", "3d printing",
    ),
    "Digital skills and education": (
        "technology education", "computer science education", "coding education", "digital skills",
        "online learning", "learning platform", "educational technology", "edtech",
        "technology training", "developer training", "certification program", "coding bootcamp",
        "hackathon", "coding competition", "developer conference", "research paper",
    ),
    "Useful product and platform updates": (
        "software update", "security update", "privacy update", "accessibility feature",
        "operating system update", "platform update", "developer preview", "public beta",
        "stable release", "major update", "productivity tool", "collaboration tool",
    ),
    "Student opportunities": (
        "student program", "students program", "student developer", "student competition",
        "scholarship", "fellowship", "internship", "graduate program", "research program",
        "developer academy", "skills program", "free certification", "free course",
        "apprenticeship", "student internship", "graduate internship", "campus program",
        "student grant", "research grant", "university technology", "career opportunity",
    ),
}

# A single generic word such as "technology" must never be enough on its own.
SUPPORTING_TERMS = (
    "technology", "tech industry", "startup", "research", "innovation", "digital infrastructure",
    "developer", "software", "hardware", "launches", "unveils", "announces", "breakthrough",
)

FINANCE_ONLY_TERMS = (
    "stock", "stocks", "stock price", "shares rise", "shares fall", "shares jump", "shares drop",
    "analyst upgrade", "analyst downgrade", "price target", "market cap", "market capitalization",
    "earnings call", "quarterly earnings", "investor sentiment", "buy rating", "sell rating",
    "undervalued", "overvalued", "ipo", "wall street", "investment return",
)

OFF_TOPIC_TERMS = (
    "celebrity", "red carpet", "box office", "movie review", "tv recap", "royal family",
    "fashion trend", "beauty tips", "recipe", "horoscope", "football match", "cricket match",
    "basketball score", "baseball score", "dating advice", "travel deals", "shopping deals",
    "shop deals", "best deals", "sale is live", "coupon code", "limited-time deal",
    "early savings", "record low", "lowest price", "price drop", "discounted price",
    "save on", "deal on", "buy now", "shopping guide", "renders leak", "render leak",
    "rumor suggests", "rumour suggests", "leak reveals",
    "best laptop", "best phone", "should you buy", "buying guide", "unboxing video",
    "amazon rainforest", "amazon river", "amazon jungle", "apple pie", "apple recipe",
    "apple cider", "apple juice", "apple tree", "alphabet learning", "meta-analysis",
)

# Investment reporting may still describe a real product or research event. These
# phrases distinguish that from articles whose only subject is market movement.
TECH_EVENT_TERMS = (
    "launch", "unveil", "release", "announce", "introduce", "build", "develop", "research",
    "chip", "model", "platform", "product", "security", "breach", "vulnerability", "outage",
    "partnership", "acquisition", "open source", "regulation", "policy", "student program",
    "update", "upgrade", "framework", "language", "course", "certification", "scholarship",
    "internship", "hackathon", "breakthrough", "discovery", "mission",
)

REPUTABLE_SOURCE_TERMS = (
    "reuters", "associated press", "ap news", "bbc", "financial times", "the guardian",
    "the verge", "techcrunch", "wired", "ars technica", "mit technology review", "ieee",
    "nature", "science", "the register", "the new stack", "venturebeat", "zdnet", "cnet",
    "openai", "google", "deepmind", "microsoft", "amazon", "aws", "nvidia", "meta",
    "anthropic", "apple", "ibm", "oracle", "github", "mozilla", "linux foundation",
    "stack overflow", "cloudflare", "red hat", "canonical", "nasa", "cern",
)

LOW_SIGNAL_SOURCE_TERMS = (
    "24/7 wall st", "investor's business daily", "barron's", "motley fool", "benzinga",
    "seeking alpha", "yahoo finance", "marketwatch", "tipranks", "substack",
)

HEADLINE_STOP_WORDS = {
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "is", "it", "its",
    "new", "of", "on", "over", "says", "saying", "the", "to", "used", "using", "with",
}


def _normalise(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def _contains(text: str, term: str) -> bool:
    # Word-aware matching prevents short names such as AI and AMD matching inside
    # unrelated words, while still supporting punctuation in multi-word phrases.
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])", text))


def _headline_tokens(title: Any, source: Any = "") -> set:
    normalised_title = _normalise(title)
    normalised_source = _normalise(source)
    if normalised_source and normalised_title.endswith(" - " + normalised_source):
        normalised_title = normalised_title[:-(len(normalised_source) + 3)]
    return {
        token for token in re.findall(r"[a-z0-9]+", normalised_title)
        if len(token) > 1 and token not in HEADLINE_STOP_WORDS
    }


def _near_duplicate(tokens: set, previous: List[set]) -> bool:
    if len(tokens) < 4:
        return False
    for earlier in previous:
        overlap = len(tokens & earlier)
        dice_similarity = (2 * overlap) / (len(tokens) + len(earlier)) if earlier else 0
        if overlap >= 4 and dice_similarity >= 0.62:
            return True
    return False


def assess_news_relevance(article: Dict[str, Any]) -> Dict[str, Any]:
    """Return an explainable editorial relevance assessment for one article."""
    title = _normalise(article.get("title"))
    summary = _normalise(article.get("summary") or article.get("description") or article.get("content"))
    source = _normalise(article.get("source"))
    text = f"{title} {summary}".strip()

    companies = [
        company for company, terms in COMPANY_TERMS.items()
        if any(_contains(text, term) for term in terms)
    ]
    topics = [
        topic for topic, terms in TOPIC_TERMS.items()
        if any(_contains(text, term) for term in terms)
    ]
    supporting_matches = sum(1 for term in SUPPORTING_TERMS if _contains(text, term))
    finance_matches = sum(1 for term in FINANCE_ONLY_TERMS if _contains(text, term))
    off_topic_matches = sum(1 for term in OFF_TOPIC_TERMS if _contains(text, term))

    # One clear company/topic match is the main signal. Additional name-dropping
    # adds only a small amount so clickbait headlines do not outrank real reporting.
    score = 4 if companies else 0
    score += min(max(len(companies) - 1, 0), 2)
    score += 4 if topics else 0
    score += min(max(len(topics) - 1, 0), 2) * 2
    if "Student opportunities" in topics or "Digital skills and education" in topics:
        score += 2
    score += min(supporting_matches, 2)
    score -= finance_matches * 5
    score -= off_topic_matches * 7
    if any(_contains(source, term) for term in REPUTABLE_SOURCE_TERMS):
        score += 2
    if any(_contains(source, term) for term in LOW_SIGNAL_SOURCE_TERMS):
        score -= 4

    has_editorial_anchor = bool(companies or topics)
    has_technology_event = any(_contains(text, term) for term in TECH_EVENT_TERMS)
    is_finance_only = bool(finance_matches and not has_technology_event)
    is_off_topic = bool(off_topic_matches and not topics)
    relevant = bool(title and has_editorial_anchor and score >= 4 and not is_finance_only and not is_off_topic)

    return {
        "is_relevant": relevant,
        "score": score,
        "companies": companies,
        "topics": topics,
    }


def filter_relevant_news(
    articles: Iterable[Dict[str, Any]],
    limit: int = None,
    annotate: bool = True,
) -> List[Dict[str, Any]]:
    """Filter, de-duplicate, and rank articles by editorial value."""
    ranked = []
    seen_urls = set()
    seen_titles = set()

    for position, article in enumerate(articles or []):
        if not isinstance(article, dict):
            continue
        assessment = assess_news_relevance(article)
        if not assessment["is_relevant"]:
            continue

        title_key = _normalise(article.get("title"))
        url_key = _normalise(article.get("url"))
        usable_url = url_key if url_key and url_key != "#" else ""
        if not title_key or title_key in seen_titles or (usable_url and usable_url in seen_urls):
            continue
        seen_titles.add(title_key)
        if usable_url:
            seen_urls.add(usable_url)

        item = dict(article)
        if annotate:
            item["relevance_score"] = assessment["score"]
            item["news_topics"] = assessment["topics"]
            item["companies"] = assessment["companies"]
        ranked.append((assessment["score"], -position, item))

    ranked.sort(key=lambda row: (row[0], row[1]), reverse=True)
    results = []
    seen_headlines: List[set] = []
    for _, _, item in ranked:
        headline_tokens = _headline_tokens(item.get("title"), item.get("source"))
        if _near_duplicate(headline_tokens, seen_headlines):
            continue
        seen_headlines.append(headline_tokens)
        results.append(item)

    if limit is None or limit < 3:
        return results[:limit] if limit is not None else results

    # Preserve quality order while preventing one company or one technology topic
    # from dominating a student briefing. Deferred stories fill any remaining space.
    bucket_cap = max(2, math.ceil(limit / 4))
    selected = []
    deferred = []
    company_counts: Dict[str, int] = {}
    topic_counts: Dict[str, int] = {}
    for item in results:
        primary_company = (item.get("companies") or [""])[0]
        primary_topic = (item.get("news_topics") or [""])[0]
        company_full = primary_company and company_counts.get(primary_company, 0) >= bucket_cap
        topic_full = primary_topic and topic_counts.get(primary_topic, 0) >= bucket_cap
        if company_full or topic_full:
            deferred.append(item)
            continue
        selected.append(item)
        if primary_company:
            company_counts[primary_company] = company_counts.get(primary_company, 0) + 1
        if primary_topic:
            topic_counts[primary_topic] = topic_counts.get(primary_topic, 0) + 1
        if len(selected) >= limit:
            return selected

    selected.extend(deferred[:max(0, limit - len(selected))])
    return selected[:limit]


def is_relevant_technology_article(article: Dict[str, Any]) -> bool:
    return bool(assess_news_relevance(article)["is_relevant"])
