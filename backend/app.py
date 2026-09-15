import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

from flask import Flask, render_template, request

from backend.services.gemini_service import generate_prerequisites
from backend.services.recommender import rank_resources
from backend.services.search_service import fetch_articles
from backend.services.youtube_service import fetch_youtube_videos
from backend.services.runtime_controls import TTLCache, RateLimiter



app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_TOPIC_LENGTH = 120
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

resource_cache = TTLCache(max_size=128)
rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)


def normalize_topic(raw_topic: str) -> str:
    """Normalize and constrain user input before sending it to external APIs."""
    topic = " ".join((raw_topic or "").strip().split())
    return topic[:MAX_TOPIC_LENGTH]


def fetch_resources(topic: str, duration_preference: str):
    """Fetch independent external sources concurrently, then rank them."""
    cache_key = f"{topic.lower()}::{duration_preference}"
    cached = resource_cache.get(cache_key)
    if cached:
        return cached

    prerequisites = generate_prerequisites(topic)

    resources = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(fetch_youtube_videos, topic): "youtube",
            executor.submit(fetch_articles, topic): "website",
        }
        for future in as_completed(futures):
            source = futures[future]
            try:
                resources.extend(future.result())
            except Exception:
                # Individual provider failures should not take down the whole request.
                logger.exception("Unexpected %s provider failure", source)

    result = rank_resources(resources, topic, duration_preference), prerequisites
    resource_cache.set(cache_key, result, CACHE_TTL_SECONDS)
    return result


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/results")
def results():
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
    if not rate_limiter.allow(client_ip):
        return render_template(
            "error.html",
            title="Too many requests",
            message="Please wait a moment before requesting more recommendations.",
        ), 429

    topic = normalize_topic(request.args.get("topic"))
    duration = request.args.get("duration", "all")

    allowed_durations = {"all", "short", "medium", "long"}
    if duration not in allowed_durations:
        duration = "all"

    resources = []
    prerequisites = []

    if topic:
        resources, prerequisites = fetch_resources(topic, duration)

    return render_template(
        "results.html",
        topic=topic,
        resources=resources,
        prerequisites=prerequisites,
        duration=duration,
    )


@app.get("/health")
def health():
    """Simple deployment health endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    # Debug is intentionally off by default for safer deployment.
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
