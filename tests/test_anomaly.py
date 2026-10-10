import pytest
from src.collectors.anomaly import calculate_anomalies, extract_niche_keywords


def test_calculate_anomalies_detects_viral_video():
    videos = [
        {"video_id": "1", "title": "Normal", "channel_id": "c1", "channel_title": "Test", "published_at": "2024-01-01T00:00:00Z", "views": 1000, "likes": 10, "comments": 5, "days_since_published": 30},
        {"video_id": "2", "title": "Normal 2", "channel_id": "c1", "channel_title": "Test", "published_at": "2024-01-01T00:00:00Z", "views": 1200, "likes": 12, "comments": 6, "days_since_published": 30},
        {"video_id": "3", "title": "VIRAL!", "channel_id": "c1", "channel_title": "Test", "published_at": "2024-01-01T00:00:00Z", "views": 50000, "likes": 500, "comments": 50, "days_since_published": 30},
    ]
    anomalies = calculate_anomalies(videos)
    assert len(anomalies) > 0
    assert any(a["video_id"] == "3" for a in anomalies)


def test_calculate_anomalies_empty_for_uniform_videos():
    videos = [
        {"video_id": "1", "title": "A", "channel_id": "c1", "channel_title": "T", "published_at": "2024-01-01T00:00:00Z", "views": 1000, "likes": 10, "comments": 5, "days_since_published": 30},
        {"video_id": "2", "title": "B", "channel_id": "c1", "channel_title": "T", "published_at": "2024-01-01T00:00:00Z", "views": 1000, "likes": 10, "comments": 5, "days_since_published": 30},
        {"video_id": "3", "title": "C", "channel_id": "c1", "channel_title": "T", "published_at": "2024-01-01T00:00:00Z", "views": 1000, "likes": 10, "comments": 5, "days_since_published": 30},
    ]
    anomalies = calculate_anomalies(videos)
    assert len(anomalies) == 0


def test_extract_niche_keywords_filters_stopwords():
    titles = [
        "Python tutorial for beginners",
        "Python advanced tips",
        "Learn Python fast",
    ]
    keywords = extract_niche_keywords(titles, top_n=5)
    assert len(keywords) > 0
    kw_names = [k["keyword"] for k in keywords]
    assert "python" in kw_names
    assert "for" not in kw_names
    assert "the" not in kw_names


def test_extract_niche_keywords_empty_titles():
    keywords = extract_niche_keywords([], top_n=5)
    assert keywords == []
