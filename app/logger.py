import sys
from loguru import logger


def configure_logging() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        serialize=False,
        backtrace=False,
        diagnose=False,
    )
