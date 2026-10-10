import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.collectors.anomaly import find_anomalous_niches
from src.db import init_db, save_niches, save_anomalies, save_keywords

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def run_collection():
    logger.info("Iniciando coleta de anomalias...")
    try:
        init_db()
        result = await find_anomalous_niches(region="US", max_channels=20)

        save_niches(result["niches"])
        logger.info(f"{len(result['niches'])} nichos salvos")

        save_anomalies(result["anomalies"])
        logger.info(f"{len(result['anomalies'])} anomalias salvas")

        save_keywords(result["keywords"])
        logger.info(f"{len(result['keywords'])} keywords salvas")

        logger.info("Coleta finalizada com sucesso")
    except Exception as e:
        logger.error(f"Erro na coleta: {e}")


def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_collection,
        CronTrigger(hour="*/6"),
        id="niche_collection",
        name="Coleta de nichos a cada 6 horas",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler agendado: coleta a cada 6 horas")

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler encerrado")


if __name__ == "__main__":
    main()
