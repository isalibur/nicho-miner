import pytest, asyncio
from src.collectors.google_trends import get_google_trends

@pytest.mark.asyncio
async def test_get_google_trends():
    result = await get_google_trends("python")
    assert isinstance(result, dict)
