from __future__ import annotations

import logging

from src.core.container import create_container
from src.core.logging_setup import configure_logging
from src.ui.app import main as app_main

logger = logging.getLogger(__name__)


def run() -> None:
    container = create_container()
    log_path = configure_logging(container.config)
    logger.info("Logging to %s", log_path)
    try:
        app_main(container.config)
    except Exception:  # noqa: BLE001
        logger.exception("Application crashed.")
        raise


if __name__ == "__main__":
    run()
