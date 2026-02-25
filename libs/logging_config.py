import os
import sys
import logging

from loguru import logger as _loguru_logger
from libs.config import CONSOLE_LOG_LEVEL

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

STD_FORMAT = "%(asctime)s | %(name)s | %(levelname)-8s | %(message)s"
STD_DATE   = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(level=os.getenv("STD_LOG_LEVEL", "INFO").upper(), format=STD_FORMAT, datefmt=STD_DATE)

_loguru_logger.remove()

log = _loguru_logger

log.add(
    sys.stdout,
    colorize=True,
    level=CONSOLE_LOG_LEVEL.upper(),
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<cyan>[ ctrader-openapi-proxy ]</cyan> | "
        "<level>{level: <8}</level> | <level>{message}</level>"
    ),
)

log.add(
    os.path.join(LOG_DIR, "proxy.log"),
    rotation="100 MB",
    retention="30 days",
    level="DEBUG",
    colorize=False,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    enqueue=True,
    backtrace=True,
    diagnose=False,
)

logger = log
