import random
import time
from typing import Callable, Any

from utils.logger import get_logger


logger = get_logger()


class SimulatedRateLimitError(Exception):
    pass


class SimulatedServerError(Exception):
    pass


class SimulatedTimeoutError(Exception):
    pass


def calculate_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    use_jitter: bool = True,
) -> float:
    """
    Calculate exponential backoff delay.
    """

    delay = base_delay * (2 ** attempt)

    if use_jitter:
        delay += random.uniform(
            0,
            1
        )

    return min(
        delay,
        max_delay
    )


def run_with_retry(
    operation: Callable[[], Any],
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> Any:
    """
    Execute an operation with retry logic.

    Retries temporary failures using
    exponential backoff with jitter.
    """

    for attempt in range(
        max_retries + 1
    ):

        try:
            return operation()

        except (
            SimulatedRateLimitError,
            SimulatedTimeoutError,
            SimulatedServerError,
            TimeoutError,
            ConnectionError,
        ) as error:

            logger.warning(
                "Temporary failure | "
                f"attempt={attempt + 1} | "
                f"error={type(error).__name__} | "
                f"message={error}"
            )

            if attempt >= max_retries:

                logger.error(
                    "Maximum retries reached | "
                    f"error={type(error).__name__}"
                )

                raise

            wait_time = calculate_backoff(
                attempt=attempt,
                base_delay=base_delay,
            )

            logger.info(
                "Retry scheduled | "
                f"wait={wait_time:.2f}s"
            )

            time.sleep(
                wait_time
            )