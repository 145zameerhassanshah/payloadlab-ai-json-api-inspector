from utils.logger import get_logger


logger = get_logger()

logger.info(
    "Batch processing test started."
)

logger.warning(
    "Simulated rate limit warning."
)

logger.error(
    "Simulated API failure."
)


print(
    "Logging test complete."
)