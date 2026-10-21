import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.db.session import SessionLocal
from app.services.inventory import expire_overdue_units

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_daily_expiry_sweep() -> int:
    """Run daily sweep to mark overdue blood units as expired."""
    logger.info("Executing daily expiry sweep...")
    db = SessionLocal()
    try:
        count = expire_overdue_units(db)
        logger.info("Daily expiry sweep completed. Expired units: %d", count)
        return count
    except Exception as exc:
        logger.error("Error during daily expiry sweep: %s", exc, exc_info=True)
        return 0
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler."""
    if not scheduler.running:
        scheduler.add_job(
            run_daily_expiry_sweep,
            trigger="cron",
            hour=0,
            minute=0,
            id="daily_expiry_sweep",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("APScheduler background scheduler started.")


def stop_scheduler():
    """Shutdown the background scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler background scheduler stopped.")
