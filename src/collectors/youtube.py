import aiohttp

from ..config import YOUTUBE_API_KEY

BASE_URL = "https://www.googleapis.com/youtube/v3"


async def fetch_video_stats(video_id: str, session: aiohttp.ClientSession):
    params = {
        "part": "statistics",
        "id": video_id,
        "key": YOUTUBE_API_KEY,
    }
    async with session.get(f"{BASE_URL}/videos", params=params) as resp:
        return await resp.json()


async def get_trending_videos(region: str = "US"):
    if not YOUTUBE_API_KEY:
        return {}
    async with aiohttp.ClientSession() as session:
        params = {
            "part": "snippet",
            "chart": "mostPopular",
            "regionCode": region,
            "maxResults": 50,
            "key": YOUTUBE_API_KEY,
        }
        async with session.get(BASE_URL + "/videos", params=params) as resp:
            return await resp.json()


async def search_videos(query: str, max_results: int = 25):
    if not YOUTUBE_API_KEY:
        return {}
    async with aiohttp.ClientSession() as session:
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "order": "relevance",
            "key": YOUTUBE_API_KEY,
        }
        async with session.get(f"{BASE_URL}/search", params=params) as resp:
            return await resp.json()
