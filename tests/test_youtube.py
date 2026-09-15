import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from services.youtube_service import classify_duration, parse_youtube_duration


def test_parse_youtube_duration():
    assert parse_youtube_duration("PT1H2M30S") == 63
    assert parse_youtube_duration("PT8M") == 8


def test_classify_duration():
    assert classify_duration(9) == "short"
    assert classify_duration(10) == "medium"
    assert classify_duration(30) == "medium"
    assert classify_duration(31) == "long"
