import aiohttp
from ..config import AHREFS_API_KEY

AHREFS_BASE_URL = "https://apiv2.ahrefs.com"


async def get_keyword_difficulty(keyword: str):
    if not AHREFS_API_KEY:
        return {}
    async with aiohttp.ClientSession() as session:
        params = {
            "token": AHREFS_API_KEY,
            "target": keyword,
            "mode": "exact",
            "output": "json",
        }
        try:
            async with session.get(
                f"{AHREFS_BASE_URL}/v3/site-explorer/keywords-difficulty", params=params
            ) as resp:
                return await resp.json()
        except Exception:
            return {}


async def get_search_volume(keyword: str):
    if not AHREFS_API_KEY:
        return {}
    async with aiohttp.ClientSession() as session:
        params = {
            "token": AHREFS_API_KEY,
            "target": keyword,
            "mode": "exact",
            "output": "json",
        }
        try:
            async with session.get(
                f"{AHREFS_BASE_URL}/v3/site-explorer/keywords-metrics", params=params
            ) as resp:
                return await resp.json()
        except Exception:
            return {}
