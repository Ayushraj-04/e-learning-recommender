import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from services.recommender import rank_resources, title_relevance


def test_title_relevance():
    assert title_relevance("python", "Python Tutorial for Beginners") == 1.0


def test_rank_prefers_topic_match():
    resources = [
        {
            "title": "Cooking tutorial",
            "platform": "website",
            "duration": "medium",
            "quality_signal": 0.9,
        },
        {
            "title": "Python tutorial for beginners",
            "platform": "website",
            "duration": "medium",
            "quality_signal": 0.5,
        },
    ]

    ranked = rank_resources(resources, "python", "all")
    assert ranked[0]["title"] == "Python tutorial for beginners"


def test_duration_preference_changes_score():
    resources = [
        {
            "title": "Python tutorial",
            "platform": "website",
            "duration": "short",
            "quality_signal": 0.5,
        },
        {
            "title": "Python tutorial",
            "platform": "website",
            "duration": "long",
            "quality_signal": 0.5,
        },
    ]

    ranked = rank_resources(resources, "python", "short")
    assert ranked[0]["duration"] == "short"
