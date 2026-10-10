import pytest
import aiohttp
from unittest.mock import AsyncMock, patch, MagicMock
from src.collectors.youtube import search_videos


@pytest.mark.asyncio
async def test_search_videos_returns_results():
    mock_response = {
        "items": [
            {
                "id": {"videoId": "abc123"},
                "snippet": {
                    "title": "Jazz Music for Relaxation",
                    "channelId": "UC123",
                    "channelTitle": "Jazz Channel",
                    "publishedAt": "2024-01-01T00:00:00Z",
                },
            }
        ]
    }

    mock_resp = AsyncMock()
    mock_resp.json = AsyncMock(return_value=mock_response)

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_resp), __aexit__=AsyncMock(return_value=None)))

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await search_videos("jazz")
        assert "items" in result
        assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_search_videos_empty_key():
    with patch("src.collectors.youtube.YOUTUBE_API_KEY", ""):
        result = await search_videos("jazz")
        assert result == {}
