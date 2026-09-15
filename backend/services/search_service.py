import logging
import os
from urllib.parse import urlparse

from google import genai

logger = logging.getLogger(__name__)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _normalize_domain(url: str) -> str:
    """Return a clean domain name from a URL."""
    try:
        hostname = urlparse(url).hostname
        if not hostname:
            return ""
        return hostname.replace("www.", "")
    except Exception:
        return ""


def _quality_for_domain(domain: str) -> float:
    """Simple quality signal for educational resources."""
    high_quality_domains = {
        "python.org",
        "realpython.com",
        "coursera.org",
        "edx.org",
        "kaggle.com",
        "codecademy.com",
        "w3schools.com",
        "geeksforgeeks.org",
        "freecodecamp.org",
        "datacamp.com",
        "udemy.com",
        "developers.google.com",
        "developer.mozilla.org",
        "stackoverflow.com",
    }

    if domain in high_quality_domains:
        return 1.0

    return 0.65


def fetch_articles(topic: str) -> list[dict]:
    """
    Use Gemini's Google Search grounding to discover
    educational web resources for the requested topic.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.error("GEMINI_API_KEY is missing.")
        return []

    client = genai.Client(api_key=api_key)

    prompt = f"""
Find high-quality educational resources for learning "{topic}".

Search the web and identify useful tutorials, documentation,
courses, guides, or learning resources.

Prioritize:
- official documentation
- reputable educational platforms
- university-backed courses
- high-quality technical tutorials

Return a concise answer containing the resources you found.
Use Google Search so that the response contains URL citations.
"""

    try:
        interaction = client.interactions.create(
            model=GEMINI_MODEL,
            input=prompt,
            tools=[{"type": "google_search"}],
        )

        resources = []
        seen_urls = set()

        # Gemini Interactions API returns URL citations
        # inside model_output -> text -> annotations.
        for step in interaction.steps:

            if step.type != "model_output":
                continue

            for content_block in step.content:

                if content_block.type != "text":
                    continue

                annotations = getattr(content_block, "annotations", None)

                if not annotations:
                    continue

                for annotation in annotations:

                    if getattr(annotation, "type", None) != "url_citation":
                        continue

                    url = getattr(annotation, "url", None)

                    # Some SDK versions may expose URI instead.
                    if not url:
                        url = getattr(annotation, "uri", None)

                    if not url:
                        continue

                    # Prevent duplicate resources.
                    if url in seen_urls:
                        continue

                    seen_urls.add(url)

                    title = getattr(annotation, "title", None)

                    if not title:
                        title = _normalize_domain(url) or "Web Resource"

                    domain = _normalize_domain(url)

                    resources.append(
                        {
                            "title": title,
                            "link": url,
                            "platform": "website",
                            "domain": domain,
                            "cost": "free",
                            "duration": "unknown",
                            "prerequisites": [],
                            "views": 0,
                            "likes": 0,
                            "quality_score": _quality_for_domain(domain),
                            "source": "google_search",
                        }
                    )

        logger.info(
            "Google Search grounding returned %d web resources.",
            len(resources),
        )

        return resources

    except Exception:
        logger.exception("Gemini Google Search grounding failed.")
        return []