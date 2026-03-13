import os
import logging
import faulthandler
from pathlib import Path

from waitress import serve
from django.contrib.staticfiles.handlers import StaticFilesHandler


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from config.wsgi import application

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "server.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("app")


if __name__ == "__main__":
    try:
        with open(LOG_DIR / "server-fault.log", "a", encoding="utf-8") as fault_log:
            faulthandler.enable(file=fault_log, all_threads=True)
        logger.info("Starting Waitress server on http://127.0.0.1:8000")
        serve(StaticFilesHandler(application), host="127.0.0.1", port=8000, threads=8)
    except KeyboardInterrupt:
        logger.info("Waitress server stopped by user")
        raise
    except Exception:
        logger.exception("Waitress server crashed")
        raise
