import asyncio
import re
from collections import Counter
from datetime import datetime, timezone

import aiohttp
import pandas as pd

from ..config import YOUTUBE_API_KEY
from .youtube import get_trending_videos, search_videos

BASE_URL = "https://www.googleapis.com/youtube/v3"

STOPWORDS = {
    "a",
    "o",
    "e",
    "de",
    "do",
    "da",
    "em",
    "um",
    "uma",
    "para",
    "com",
    "no",
    "na",
    "os",
    "as",
    "dos",
    "das",
    "que",
    "se",
    "por",
    "the",
    "and",
    "is",
    "in",
    "on",
    "at",
    "to",
    "of",
    "for",
    "an",
    "as",
    "this",
    "that",
    "it",
    "be",
    "are",
    "was",
    "como",
    "você",
    "seu",
    "sua",
    "meu",
    "minha",
    "nos",
    "nós",
    "lhe",
    "ele",
    "ela",
    "eles",
    "elas",
    "eu",
    "tu",
    "me",
    "te",
    "lhe",
    "nos",
    "vos",
    "lhes",
    "que",
    "qual",
    "quais",
    "onde",
    "quando",
    "porque",
    "pois",
    "mas",
    "ou",
    "nem",
    "já",
    "também",
    "só",
    "após",
    "antes",
    "entre",
    "sobre",
    "até",
    "desde",
    "contra",
    "perante",
    "video",
    "vídeo",
    "youtube",
    "canal",
    "inscreva",
    "like",
    "compartilhe",
    "deixa",
    "deixe",
    "veja",
    "vejam",
    "assista",
    "assistam",
    "clique",
    "cliquem",
    "link",
    "links",
    "descrição",
    "descrições",
    "comentário",
    "comentários",
    "comente",
    "comentem",
    "compartilhe",
    "compartilhem",
    "inscreva-se",
    "inscrevam-se",
    "ative",
    "ativem",
    "sininho",
    "sino",
    "notificação",
    "notificações",
    "grátis",
    "grátis",
    "gratuito",
    "gratuita",
    "promoção",
    "promoções",
    "oferta",
    "ofertas",
    "desconto",
    "descontos",
    "cupom",
    "cupons",
    "cupom",
    "cupons",
    "brinde",
    "brindes",
    "sorteio",
    "sorteios",
    "ganhe",
    "ganhem",
    "ganhar",
    "ganhe",
    "prêmio",
    "prêmios",
    "concurso",
    "concurso",
    "participe",
    "participem",
    "participação",
    "participações",
    "live",
    "ao",
    "vivo",
    "estreia",
    "estreias",
    "lançamento",
    "lançamentos",
    "novo",
    "novos",
    "nova",
    "novas",
    "atualização",
    "atualizações",
    "update",
    "updates",
    "tutorial",
    "tutoriais",
    "dica",
    "dicas",
    "truque",
    "truques",
    "segredo",
    "segredos",
    "erro",
    "erros",
    "problema",
    "problemas",
    "solução",
    "soluções",
    "resposta",
    "respostas",
    "pergunta",
    "perguntas",
    "resposta",
    "respostas",
    "comentário",
    "comentários",
    "comente",
    "comentem",
    "compartilhe",
    "compartilhem",
    "inscreva-se",
    "inscrevam-se",
    "ative",
    "ativem",
    "sininho",
    "sino",
    "notificação",
    "notificações",
}


async def get_channel_id_from_video(
    video_id: str, session: aiohttp.ClientSession
) -> str | None:
    params = {
        "part": "snippet",
        "id": video_id,
        "key": YOUTUBE_API_KEY,
    }
    async with session.get(f"{BASE_URL}/videos", params=params) as resp:
        data = await resp.json()
        items = data.get("items", [])
        if items:
            return items[0].get("snippet", {}).get("channelId")
        return None


async def get_channel_videos(
    channel_id: str, max_results: int = 50, session: aiohttp.ClientSession | None = None
) -> list[dict]:
    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True

    try:
        uploads_playlist = f"UU{channel_id[2:]}"
        params = {
            "part": "snippet,contentDetails",
            "playlistId": uploads_playlist,
            "maxResults": min(max_results, 50),
            "key": YOUTUBE_API_KEY,
        }
        async with session.get(f"{BASE_URL}/playlistItems", params=params) as resp:
            playlist_data = await resp.json()

        video_ids = [
            item.get("contentDetails", {}).get("videoId")
            for item in playlist_data.get("items", [])
            if item.get("contentDetails", {}).get("videoId")
        ]

        if not video_ids:
            return []

        videos_params = {
            "part": "snippet,statistics",
            "id": ",".join(video_ids),
            "key": YOUTUBE_API_KEY,
        }
        async with session.get(f"{BASE_URL}/videos", params=videos_params) as resp:
            videos_data = await resp.json()

        videos = []
        for item in videos_data.get("items", []):
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            published = snippet.get("publishedAt", "")
            days_since = 30
            if published:
                try:
                    pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    days_since = max((datetime.now(timezone.utc) - pub_date).days, 1)
                except ValueError:
                    pass

            videos.append(
                {
                    "video_id": item.get("id"),
                    "title": snippet.get("title", ""),
                    "channel_id": channel_id,
                    "channel_title": snippet.get("channelTitle", ""),
                    "published_at": published,
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0)),
                    "days_since_published": days_since,
                }
            )
        return videos
    finally:
        if close_session:
            await session.close()


def calculate_anomalies(videos: list[dict]) -> list[dict]:
    if len(videos) < 3:
        return []

    df = pd.DataFrame(videos)
    mean_views = df["views"].mean()
    median_views = df["views"].median()

    df["views_per_day"] = df["views"] / df["days_since_published"]
    df["engagement_ratio"] = df["views"] / (df["comments"] + 1)

    anomalies = []
    for _, row in df.iterrows():
        is_viral = row["views"] > median_views * 10
        is_fast_growth = row["views_per_day"] > 10000
        is_low_competition = row["engagement_ratio"] > 1000

        anomaly_score = 0
        if is_viral:
            anomaly_score += 40
        if is_fast_growth:
            anomaly_score += 30
        if is_low_competition:
            anomaly_score += 30

        if anomaly_score > 0:
            anomalies.append(
                {
                    "video_id": row["video_id"],
                    "title": row["title"],
                    "channel_id": row["channel_id"],
                    "channel_title": row["channel_title"],
                    "views": row["views"],
                    "z_score": round(
                        (row["views"] - mean_views) / (df["views"].std() or 1), 2
                    ),
                    "views_per_day": round(row["views_per_day"], 2),
                    "engagement_ratio": round(row["engagement_ratio"], 2),
                    "anomaly_score": anomaly_score,
                    "is_viral": is_viral,
                    "is_fast_growth": is_fast_growth,
                    "is_low_competition": is_low_competition,
                }
            )

    return sorted(anomalies, key=lambda x: x["anomaly_score"], reverse=True)


def extract_niche_keywords(titles: list[str], top_n: int = 10) -> list[dict]:
    words = []
    for title in titles:
        tokens = re.findall(r"\b[a-zA-ZÀ-ÿ]{3,}\b", title.lower())
        words.extend([w for w in tokens if w not in STOPWORDS])

    counter = Counter(words)
    total = sum(counter.values()) or 1

    return [
        {"keyword": word, "frequency": count, "weight": round(count / total, 4)}
        for word, count in counter.most_common(top_n)
    ]


async def get_channel_stats(channel_id: str, session: aiohttp.ClientSession) -> dict:
    params = {
        "part": "snippet,statistics",
        "id": channel_id,
        "key": YOUTUBE_API_KEY,
    }
    async with session.get(f"{BASE_URL}/channels", params=params) as resp:
        data = await resp.json()
        items = data.get("items", [])
        if not items:
            return {}
        item = items[0]
        stats = item.get("statistics", {})
        snippet = item.get("snippet", {})
        created = snippet.get("publishedAt", "")
        age_days = 90
        if created:
            try:
                created_date = datetime.fromisoformat(created.replace("Z", "+00:00"))
                age_days = (datetime.now(timezone.utc) - created_date).days
            except ValueError:
                pass
        return {
            "channel_id": channel_id,
            "title": snippet.get("title", ""),
            "created_at": created,
            "age_days": age_days,
            "subscribers": int(stats.get("subscriberCount", 0)),
            "video_count": int(stats.get("videoCount", 0)),
            "view_count": int(stats.get("viewCount", 0)),
        }


async def find_deep_niches(
    query: str = "",
    max_results: int = 20,
) -> dict:
    if not YOUTUBE_API_KEY:
        return {"niches": [], "anomalies": [], "keywords": [], "channels": []}

    search_query = query if query else "new channel 2024"
    search_data = await search_videos(search_query, max_results=50)
    items = search_data.get("items", [])

    channel_ids = []
    for item in items:
        channel_id = item.get("snippet", {}).get("channelId")
        if channel_id and channel_id not in channel_ids:
            channel_ids.append(channel_id)

    filtered_channels = []
    all_anomalies = []
    all_titles = []

    async with aiohttp.ClientSession() as session:
        stats_tasks = [get_channel_stats(ch_id, session) for ch_id in channel_ids[:30]]
        stats_results = await asyncio.gather(*stats_tasks, return_exceptions=True)

        for stats in stats_results:
            if isinstance(stats, Exception) or not stats:
                continue
            is_new = stats["age_days"] <= 90
            is_small = 5000 <= stats["subscribers"] <= 15000
            is_few_videos = stats["video_count"] < 10
            if is_new and is_small and is_few_videos:
                filtered_channels.append(stats)

        video_tasks = [
            get_channel_videos(ch["channel_id"], session=session)
            for ch in filtered_channels
        ]
        video_results = await asyncio.gather(*video_tasks, return_exceptions=True)

        for ch, videos in zip(filtered_channels, video_results):
            if isinstance(videos, Exception) or not videos:
                continue
            all_titles.extend([v["title"] for v in videos])
            anomalies = calculate_anomalies(videos)
            for a in anomalies:
                a["channel_id"] = ch["channel_id"]
                a["channel_title"] = ch["title"]
            all_anomalies.extend(anomalies)

    all_anomalies.sort(key=lambda x: x["anomaly_score"], reverse=True)
    keywords = extract_niche_keywords(all_titles)

    niches = []
    seen_keywords = set()
    for anomaly in all_anomalies[:50]:
        title_words = re.findall(r"\b[a-zA-ZÀ-ÿ]{3,}\b", anomaly["title"].lower())
        niche_words = [w for w in title_words if w not in STOPWORDS]
        niche_key = " ".join(sorted(set(niche_words[:3])))

        if niche_key and niche_key not in seen_keywords:
            seen_keywords.add(niche_key)
            niches.append(
                {
                    "niche": niche_key,
                    "anomaly_score": anomaly["anomaly_score"],
                    "avg_views": anomaly["views"],
                    "growth_rate": anomaly["views_per_day"],
                    "competition_level": (
                        "low" if anomaly["is_low_competition"] else "medium"
                    ),
                    "source_video": anomaly["title"],
                    "channel": anomaly["channel_title"],
                }
            )

    return {
        "niches": niches[:20],
        "anomalies": all_anomalies[:50],
        "keywords": keywords,
        "channels": filtered_channels,
    }


async def find_anomalous_niches(region: str = "US", max_channels: int = 20) -> dict:
    if not YOUTUBE_API_KEY:
        return {"niches": [], "anomalies": [], "keywords": []}

    trending = await get_trending_videos(region)
    items = trending.get("items", [])

    channel_ids = set()
    for item in items:
        channel_id = item.get("snippet", {}).get("channelId")
        if channel_id:
            channel_ids.add(channel_id)
        if len(channel_ids) >= max_channels:
            break

    all_anomalies = []
    all_titles = []

    async with aiohttp.ClientSession() as session:
        tasks = [get_channel_videos(ch_id, session=session) for ch_id in channel_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for videos in results:
            if isinstance(videos, Exception) or not videos:
                continue
            all_titles.extend([v["title"] for v in videos])
            anomalies = calculate_anomalies(videos)
            all_anomalies.extend(anomalies)

    all_anomalies.sort(key=lambda x: x["anomaly_score"], reverse=True)
    keywords = extract_niche_keywords(all_titles)

    niches = []
    seen_keywords = set()
    for anomaly in all_anomalies[:50]:
        title_words = re.findall(r"\b[a-zA-ZÀ-ÿ]{3,}\b", anomaly["title"].lower())
        niche_words = [w for w in title_words if w not in STOPWORDS]
        niche_key = " ".join(sorted(set(niche_words[:3])))

        if niche_key and niche_key not in seen_keywords:
            seen_keywords.add(niche_key)
            niches.append(
                {
                    "niche": niche_key,
                    "anomaly_score": anomaly["anomaly_score"],
                    "avg_views": anomaly["views"],
                    "growth_rate": anomaly["views_per_day"],
                    "competition_level": (
                        "low" if anomaly["is_low_competition"] else "medium"
                    ),
                    "source_video": anomaly["title"],
                    "channel": anomaly["channel_title"],
                }
            )

    return {
        "niches": niches[:20],
        "anomalies": all_anomalies[:50],
        "keywords": keywords,
    }
