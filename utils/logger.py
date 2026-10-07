import logging
from pathlib import Path


LOG_DIR = Path("logs")
LOG_DIR.mkdir(
    exist_ok=True
)

LOG_FILE = LOG_DIR / "batch_processing.log"


def get_logger():
    """
    Create and return the application logger.
    """

    logger = logging.getLogger(
        "payloadlab_batch"
    )

    logger.setLevel(
        logging.INFO
    )

    if not logger.handlers:

        file_handler = logging.FileHandler(
            LOG_FILE,
            encoding="utf-8"
        )

        formatter = logging.Formatter(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(message)s"
        )

        file_handler.setFormatter(
            formatter
        )

        logger.addHandler(
            file_handler
        )

    return logger