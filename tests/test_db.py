import pytest
from src.db import (
    init_db, save_niches, save_anomalies, save_keywords,
    get_niches, get_anomalies, get_keywords,
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


def test_save_and_get_niches():
    niches = [
        {"niche": "test niche", "anomaly_score": 80, "avg_views": 10000,
         "growth_rate": 500.0, "competition_level": "low",
         "source_video": "Test Video", "channel": "TestChannel"}
    ]
    save_niches(niches)
    result = get_niches()
    assert len(result) == 1
    assert result[0]["niche"] == "test niche"


def test_save_and_get_anomalies():
    anomalies = [
        {"video_id": "abc123", "title": "Viral Video", "channel_id": "ch1",
         "channel_title": "TestChannel", "views": 50000, "z_score": 3.5,
         "views_per_day": 10000.0, "engagement_ratio": 2000.0,
         "anomaly_score": 100, "is_viral": True,
         "is_fast_growth": True, "is_low_competition": True}
    ]
    save_anomalies(anomalies)
    result = get_anomalies()
    assert len(result) == 1
    assert result[0]["video_id"] == "abc123"


def test_save_and_get_keywords():
    keywords = [
        {"keyword": "python", "frequency": 10, "weight": 0.5},
        {"keyword": "tutorial", "frequency": 8, "weight": 0.4},
    ]
    save_keywords(keywords)
    result = get_keywords()
    assert len(result) == 2


def test_duplicate_video_id_replaced():
    anomalies = [
        {"video_id": "dup1", "title": "First", "channel_id": "ch1",
         "channel_title": "T", "views": 100, "z_score": 1.0,
         "views_per_day": 10.0, "engagement_ratio": 100.0,
         "anomaly_score": 50, "is_viral": False,
         "is_fast_growth": False, "is_low_competition": False},
        {"video_id": "dup1", "title": "Second", "channel_id": "ch1",
         "channel_title": "T", "views": 200, "z_score": 2.0,
         "views_per_day": 20.0, "engagement_ratio": 200.0,
         "anomaly_score": 60, "is_viral": True,
         "is_fast_growth": False, "is_low_competition": False},
    ]
    save_anomalies(anomalies)
    result = get_anomalies()
    assert len(result) == 1
    assert result[0]["title"] == "Second"
