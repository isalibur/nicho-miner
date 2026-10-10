import aiohttp

BASE_URL = "https://trends.google.com/trends/api"


async def get_google_trends(keyword: str, timeframe: str = "today 12-m"):
    async with aiohttp.ClientSession() as session:
        params = {
            "hl": "en-US",
            "tz": -180,
            "cat": "0",
            "geo": "US",
            "q": keyword,
            "date": timeframe,
        }
        try:
            async with session.get(f"{BASE_URL}/explore", params=params) as resp:
                return await resp.json()
        except Exception:
            return {}
