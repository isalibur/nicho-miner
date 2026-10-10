import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.collectors.anomaly import find_anomalous_niches
from src.db import init_db, save_niches, save_anomalies, save_keywords


async def main():
    init_db()
    result = await find_anomalous_niches(region="US", max_channels=20)

    save_niches(result["niches"])
    save_anomalies(result["anomalies"])
    save_keywords(result["keywords"])

    print(f"Salvos: {len(result['niches'])} nichos, {len(result['anomalies'])} anomalias, {len(result['keywords'])} keywords")


if __name__ == "__main__":
    asyncio.run(main())
