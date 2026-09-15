import math
import re


STOPWORDS = {
    "a", "an", "and", "for", "from", "how", "in", "is", "of", "on",
    "the", "to", "tutorial", "with", "learn", "learning",
}


def _tokens(text: str):
    return {
        token
        for token in re.findall(r"[a-z0-9+#.]+", (text or "").lower())
        if token not in STOPWORDS
    }


def title_relevance(topic: str, title: str) -> float:
    """Simple explainable lexical relevance score between 0 and 1."""
    topic_tokens = _tokens(topic)
    title_tokens = _tokens(title)
    if not topic_tokens:
        return 0.0
    return len(topic_tokens & title_tokens) / len(topic_tokens)


def _engagement_score(resource) -> float:
    """Log-scaled YouTube engagement signal; 0 for sources without view data."""
    views = resource.get("views", 0)
    if not views:
        return resource.get("quality_signal", 0.0)

    # 1M views ~= 1.0, with diminishing returns for very large channels.
    return min(1.0, math.log10(views + 1) / 6.0)


def _duration_score(resource, preferred_duration: str) -> float:
    if preferred_duration == "all":
        return 0.5
    return 1.0 if resource.get("duration") == preferred_duration else 0.0


def rank_resources(resources, topic: str, preferred_duration: str = "all"):
    """
    Rank resources using transparent weighted signals:
      50% title relevance
      30% quality/engagement
      20% duration preference
    """
    ranked = []

    for resource in resources:
        relevance = title_relevance(topic, resource.get("title", ""))
        quality = _engagement_score(resource)
        duration = _duration_score(resource, preferred_duration)

        score = (
            (0.50 * relevance)
            + (0.30 * quality)
            + (0.20 * duration)
        )

        reasons = []
        if relevance >= 0.75:
            reasons.append("Strong topic match")
        elif relevance >= 0.40:
            reasons.append("Relevant to your topic")

        if resource.get("platform") == "youtube" and resource.get("views", 0) > 10000:
            reasons.append("Strong viewer engagement")
        elif resource.get("platform") == "website" and resource.get("quality_signal", 0) >= 0.7:
            reasons.append("Educational source")

        if preferred_duration != "all" and resource.get("duration") == preferred_duration:
            reasons.append("Matches your duration preference")

        if not reasons:
            reasons.append("Matches your search")

        resource = dict(resource)
        resource["score"] = round(score * 100)
        resource["reasons"] = reasons[:3]
        ranked.append(resource)

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked
