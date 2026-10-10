import pytest, asyncio
from src.collectors.youtube import get_trending_videos

@pytest.mark.asyncio
async def test_get_trending_videos():
    result = await get_trending_videos()
    # API key may be missing; ensure request does not crash
    assert isinstance(result, dict)
