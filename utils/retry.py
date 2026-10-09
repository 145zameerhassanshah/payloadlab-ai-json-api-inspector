import random
import time
from typing import Callable, Any

from utils.logger import get_logger


logger = get_logger()


class SimulatedRateLimitError(Exception):
    """Simulated HTTP 429 failure."""


class SimulatedServerError(Exception):
    """Simulated temporary 5xx failure."""


class SimulatedTimeoutError(Exception):
    """Simulated request timeout."""


def calculate_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    use_jitter: bool = True,
) -> float:
    """
    Exponential backoff with optional
    random jitter.
    """

    delay = (
        base_delay
        * (2 ** attempt)
    )

    if use_jitter:
        delay += random.uniform(
            0,
            1,
        )

    return min(
        delay,
        max_delay,
    )


def run_with_retry(
    operation: Callable[[], Any],
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> Any:
    """
    Retry only temporary failures.

    Total attempts =
    initial attempt + max_retries.
    """

    retryable_errors = (
        SimulatedRateLimitError,
        SimulatedTimeoutError,
        SimulatedServerError,
        TimeoutError,
        ConnectionError,
    )

    for attempt in range(
        max_retries + 1
    ):
        try:
            return operation()

        except retryable_errors as error:
            attempt_number = (
                attempt + 1
            )

            logger.warning(
                "Temporary failure | "
                f"attempt={attempt_number} | "
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
