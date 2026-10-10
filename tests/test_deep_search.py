import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.collectors.anomaly import get_channel_stats, find_deep_niches


@pytest.mark.asyncio
async def test_get_channel_stats_returns_filtered_fields():
    mock_response = {
        "items": [
            {
                "snippet": {"title": "New Channel", "publishedAt": "2026-09-01T00:00:00Z"},
                "statistics": {"subscriberCount": "8000", "videoCount": "5", "viewCount": "100000"},
            }
        ]
    }
    mock_resp = AsyncMock()
    mock_resp.json = AsyncMock(return_value=mock_response)
    mock_session = MagicMock()
    mock_session.get = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_resp), __aexit__=AsyncMock(return_value=None))
    )

    result = await get_channel_stats("UC123", mock_session)
    assert result["channel_id"] == "UC123"
    assert result["subscribers"] == 8000
    assert result["video_count"] == 5
    assert result["age_days"] <= 90


@pytest.mark.asyncio
async def test_find_deep_niches_empty_key():
    with patch("src.collectors.anomaly.YOUTUBE_API_KEY", ""):
        result = await find_deep_niches(query="jazz")
        assert result == {"niches": [], "anomalies": [], "keywords": [], "channels": []}


@pytest.mark.asyncio
async def test_find_deep_niches_filters_new_small_channels():
    search_response = {
        "items": [
            {"snippet": {"channelId": "UC_NEW"}},
            {"snippet": {"channelId": "UC_OLD"}},
        ]
    }
    new_stats = {
        "channel_id": "UC_NEW",
        "title": "New Jazz",
        "age_days": 30,
        "subscribers": 8000,
        "video_count": 5,
        "view_count": 50000,
    }
    old_stats = {
        "channel_id": "UC_OLD",
        "title": "Old Big",
        "age_days": 1000,
        "subscribers": 500000,
        "video_count": 200,
        "view_count": 50000000,
    }
    videos = [
        {"video_id": "1", "title": "Jazz test", "channel_id": "UC_NEW", "channel_title": "New Jazz",
         "published_at": "2026-01-01T00:00:00Z", "views": 50000, "likes": 500, "comments": 10, "days_since_published": 5},
        {"video_id": "2", "title": "Jazz normal", "channel_id": "UC_NEW", "channel_title": "New Jazz",
         "published_at": "2026-01-01T00:00:00Z", "views": 1000, "likes": 10, "comments": 5, "days_since_published": 30},
        {"video_id": "3", "title": "Jazz other", "channel_id": "UC_NEW", "channel_title": "New Jazz",
         "published_at": "2026-01-01T00:00:00Z", "views": 1200, "likes": 12, "comments": 6, "days_since_published": 30},
    ]

    with patch("src.collectors.anomaly.YOUTUBE_API_KEY", "fake-key"), patch(
        "src.collectors.anomaly.search_videos", AsyncMock(return_value=search_response)
    ), patch(
        "src.collectors.anomaly.get_channel_stats",
        AsyncMock(side_effect=[new_stats, old_stats]),
    ), patch(
        "src.collectors.anomaly.get_channel_videos", AsyncMock(return_value=videos)
    ):
        result = await find_deep_niches(query="jazz")
        assert len(result["channels"]) == 1
        assert result["channels"][0]["channel_id"] == "UC_NEW"
