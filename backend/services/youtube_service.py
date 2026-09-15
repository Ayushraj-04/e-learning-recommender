import logging
import math
import os
import re

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def parse_youtube_duration(duration_str: str) -> int:
    """Convert ISO-8601 YouTube duration to total minutes, rounded up."""
    match = re.fullmatch(
        r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",
        duration_str or "",
    )
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return math.ceil((hours * 60) + minutes + (seconds / 60))


def classify_duration(minutes: int) -> str:
    if minutes < 10:
        return "short"
    if minutes <= 30:
        return "medium"
    return "long"


def fetch_youtube_videos(topic: str):
    """Search YouTube and retrieve metadata used by the ranking layer."""
    if not YOUTUBE_API_KEY:
        logger.warning("YOUTUBE_API_KEY is not configured.")
        return []

    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

        search_response = (
            youtube.search()
            .list(
                q=f"{topic} tutorial",
                part="snippet",
                type="video",
                maxResults=8,
            )
            .execute()
        )

        video_ids = [
            item["id"]["videoId"]
            for item in search_response.get("items", [])
            if item.get("id", {}).get("videoId")
        ]
        if not video_ids:
            return []

        video_response = (
            youtube.videos()
            .list(
                part="snippet,contentDetails,statistics",
                id=",".join(video_ids),
            )
            .execute()
        )

        resources = []
        for item in video_response.get("items", []):
            duration_minutes = parse_youtube_duration(
                item.get("contentDetails", {}).get("duration", "")
            )
            stats = item.get("statistics", {})

            resources.append(
                {
                    "title": item.get("snippet", {}).get("title", "Untitled video"),
                    "link": f"https://www.youtube.com/watch?v={item['id']}",
                    "platform": "youtube",
                    "duration": classify_duration(duration_minutes),
                    "duration_minutes": duration_minutes,
                    "cost": "free",
                    "views": int(stats.get("viewCount", 0) or 0),
                    "likes": int(stats.get("likeCount", 0) or 0),
                }
            )

        return resources

    except HttpError:
        logger.exception("YouTube API request failed.")
        return []
    except Exception:
        logger.exception("Unexpected YouTube integration failure.")
        return []
