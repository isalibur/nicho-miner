import pytest
from src.db import (
    init_db, save_niches, save_anomalies, save_keywords,
    search_niches, search_anomalies, search_keywords,
    get_niches_with_url, get_anomalies_with_url,
)


@pytest.fixture(autouse=True)
def clean_db():
    from src.db import get_connection
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM niches")
    conn.execute("DELETE FROM anomalies")
    conn.execute("DELETE FROM keywords")
    conn.commit()
    conn.close()
    yield


def test_search_niches_by_name():
    niches = [
        {"niche": "python tutorial", "anomaly_score": 80, "avg_views": 10000,
         "growth_rate": 500.0, "competition_level": "low",
         "source_video": "Test", "channel": "Python Channel"},
        {"niche": "cooking recipes", "anomaly_score": 70, "avg_views": 8000,
         "growth_rate": 400.0, "competition_level": "medium",
         "source_video": "Test 2", "channel": "Cooking Channel"},
    ]
    save_niches(niches)
    result = search_niches("python")
    assert len(result) == 1
    assert result[0]["niche"] == "python tutorial"


def test_search_niches_by_channel():
    niches = [
        {"niche": "python tutorial", "anomaly_score": 80, "avg_views": 10000,
         "growth_rate": 500.0, "competition_level": "low",
         "source_video": "Test", "channel": "Python Channel"},
        {"niche": "cooking recipes", "anomaly_score": 70, "avg_views": 8000,
         "growth_rate": 400.0, "competition_level": "medium",
         "source_video": "Test 2", "channel": "Cooking Channel"},
    ]
    save_niches(niches)
    result = search_niches("cooking")
    assert len(result) == 1
    assert result[0]["channel"] == "Cooking Channel"


def test_search_anomalies_by_title():
    anomalies = [
        {"video_id": "v1", "title": "Python Tutorial", "channel_id": "ch1",
         "channel_title": "Python Channel", "views": 50000, "z_score": 3.5,
         "views_per_day": 10000.0, "engagement_ratio": 2000.0,
         "anomaly_score": 100, "is_viral": True,
         "is_fast_growth": True, "is_low_competition": True},
        {"video_id": "v2", "title": "Cooking Show", "channel_id": "ch2",
         "channel_title": "Cooking Channel", "views": 30000, "z_score": 2.5,
         "views_per_day": 5000.0, "engagement_ratio": 1000.0,
         "anomaly_score": 80, "is_viral": False,
         "is_fast_growth": True, "is_low_competition": True},
    ]
    save_anomalies(anomalies)
    result = search_anomalies("python")
    assert len(result) == 1
    assert result[0]["title"] == "Python Tutorial"


def test_search_keywords():
    keywords = [
        {"keyword": "python", "frequency": 10, "weight": 0.5},
        {"keyword": "cooking", "frequency": 8, "weight": 0.4},
    ]
    save_keywords(keywords)
    result = search_keywords("pyt")
    assert len(result) == 1
    assert result[0]["keyword"] == "python"


def test_get_niches_with_url():
    niches = [
        {"niche": "python tutorial", "anomaly_score": 80, "avg_views": 10000,
         "growth_rate": 500.0, "competition_level": "low",
         "source_video": "Test", "channel": "Python Channel"},
    ]
    save_niches(niches)
    result = get_niches_with_url()
    assert len(result) == 1
    assert "channel_url" in result[0]


def test_get_anomalies_with_url():
    anomalies = [
        {"video_id": "v1", "title": "Test", "channel_id": "UC123",
         "channel_title": "Test Channel", "views": 1000, "z_score": 1.0,
         "views_per_day": 100.0, "engagement_ratio": 500.0,
         "anomaly_score": 50, "is_viral": False,
         "is_fast_growth": False, "is_low_competition": False},
    ]
    save_anomalies(anomalies)
    result = get_anomalies_with_url()
    assert len(result) == 1
    assert result[0]["channel_url"] == "https://youtube.com/channel/UC123"
