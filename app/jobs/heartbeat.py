from datetime import datetime, timezone
from loguru import logger


def heartbeat() -> None:
    logger.info(
        "GraceFinance growth worker alive at {}",
        datetime.now(timezone.utc).isoformat(),
    )
