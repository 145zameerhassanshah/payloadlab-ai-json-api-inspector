import random
import time
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

import requests

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
)
from validators import validate_payload
from response_parser import (
    parse_llm_response,
    extract_response_metadata,
)
from utils.logger import get_logger


logger = get_logger()

RETRYABLE_STATUS_CODES = {
    429,
    500,
    502,
    503,
    504,
}


def _calculate_backoff(
    attempt: int,
    base_delay: float,
    max_delay: float = 30.0,
) -> float:
    """
    Exponential backoff with jitter.
    """

    exponential_delay = base_delay * (2 ** attempt)
    jitter = random.uniform(0, 1)

    return min(
        exponential_delay + jitter,
        max_delay,
    )


def _retry_after_seconds(
    response: requests.Response,
) -> float | None:
    """
    Read Retry-After when the provider sends it.

    Supports either:
    - integer/decimal seconds
    - HTTP date
    """

    value = response.headers.get(
        "Retry-After"
    )

    if not value:
        return None

    try:
        return max(
            float(value),
            0.0,
        )
    except ValueError:
        pass

    try:
        retry_date = parsedate_to_datetime(
            value
        )

        if retry_date.tzinfo is None:
            retry_date = retry_date.replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(
            timezone.utc
        )

        return max(
            (
                retry_date.astimezone(
                    timezone.utc
                )
                - now
            ).total_seconds(),
            0.0,
        )
    except Exception:
        return None


def send_llm_request(
    payload: dict,
    max_retries: int = 3,
    base_delay: float = 1.0,
    connect_timeout: float = 10.0,
    read_timeout: float = 90.0,
) -> dict:
    """
    Send an LLM request with graceful handling for:

    - invalid payloads
    - missing API configuration
    - HTTP 429 rate limits
    - transient 5xx server errors
    - connection errors
    - request timeouts
    - invalid JSON responses
    - malformed nested LLM responses
    """

    payload_errors = validate_payload(
        payload
    )

    if payload_errors:
        return {
            "success": False,
            "stage": "payload_validation",
            "errors": payload_errors,
            "raw_response": None,
            "parsed_content": None,
            "metadata": None,
            "status_code": None,
            "attempts": 0,
        }

    if not OPENROUTER_API_KEY:
        return {
            "success": False,
            "stage": "configuration",
            "errors": [
                "OPENROUTER_API_KEY is missing."
            ],
            "raw_response": None,
            "parsed_content": None,
            "metadata": None,
            "status_code": None,
            "attempts": 0,
        }

    headers = {
        "Authorization": (
            f"Bearer {OPENROUTER_API_KEY}"
        ),
        "Content-Type": "application/json",
    }

    endpoint = (
        f"{OPENROUTER_BASE_URL}"
        "/chat/completions"
    )

    response = None

    for attempt in range(
        max_retries + 1
    ):
        attempt_number = attempt + 1

        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=(
                    connect_timeout,
                    read_timeout,
                ),
            )

        except requests.exceptions.Timeout as error:
            logger.warning(
                "API timeout | "
                f"attempt={attempt_number} | "
                f"error={error}"
            )

            if attempt >= max_retries:
                return {
                    "success": False,
                    "stage": "timeout",
                    "errors": [
                        "The AI request timed out "
                        "after all retry attempts."
                    ],
                    "raw_response": None,
                    "parsed_content": None,
                    "metadata": None,
                    "status_code": None,
                    "attempts": attempt_number,
                }

            wait_time = _calculate_backoff(
                attempt,
                base_delay,
            )

            logger.info(
                "Retrying after timeout | "
                f"wait={wait_time:.2f}s"
            )

            time.sleep(wait_time)
            continue

        except requests.exceptions.ConnectionError as error:
            logger.warning(
                "Connection failure | "
                f"attempt={attempt_number} | "
                f"error={error}"
            )

            if attempt >= max_retries:
                return {
                    "success": False,
                    "stage": "network",
                    "errors": [
                        "The connection to the AI "
                        "service failed after all "
                        "retry attempts."
                    ],
                    "raw_response": None,
                    "parsed_content": None,
                    "metadata": None,
                    "status_code": None,
                    "attempts": attempt_number,
                }

            wait_time = _calculate_backoff(
                attempt,
                base_delay,
            )

            logger.info(
                "Retrying after connection failure | "
                f"wait={wait_time:.2f}s"
            )

            time.sleep(wait_time)
            continue

        except requests.exceptions.RequestException as error:
            logger.error(
                "Non-retryable request error | "
                f"error={error}"
            )

            return {
                "success": False,
                "stage": "network",
                "errors": [
                    f"Request error: {error}"
                ],
                "raw_response": None,
                "parsed_content": None,
                "metadata": None,
                "status_code": None,
                "attempts": attempt_number,
            }

        status_code = response.status_code

        if status_code in RETRYABLE_STATUS_CODES:
            try:
                response_data = response.json()
            except ValueError:
                response_data = response.text

            logger.warning(
                "Retryable HTTP failure | "
                f"status={status_code} | "
                f"attempt={attempt_number}"
            )

            if attempt >= max_retries:
                error_message = (
                    response_data.get(
                        "error",
                        {},
                    ).get(
                        "message",
                        f"HTTP {status_code}"
                    )
                    if isinstance(
                        response_data,
                        dict,
                    )
                    else f"HTTP {status_code}"
                )

                return {
                    "success": False,
                    "stage": (
                        "rate_limit"
                        if status_code == 429
                        else "server_error"
                    ),
                    "errors": [
                        error_message
                    ],
                    "raw_response": response_data,
                    "parsed_content": None,
                    "metadata": None,
                    "status_code": status_code,
                    "attempts": attempt_number,
                }

            retry_after = _retry_after_seconds(
                response
            )

            if retry_after is not None:
                wait_time = retry_after
            else:
                wait_time = _calculate_backoff(
                    attempt,
                    base_delay,
                )

            logger.info(
                "Retry scheduled | "
                f"status={status_code} | "
                f"wait={wait_time:.2f}s"
            )

            time.sleep(wait_time)
            continue

        try:
            response_data = response.json()
        except ValueError:
            return {
                "success": False,
                "stage": "response_json",
                "errors": [
                    "The API response was not "
                    "valid JSON."
                ],
                "raw_response": response.text,
                "parsed_content": None,
                "metadata": None,
                "status_code": status_code,
                "attempts": attempt_number,
            }

        if not response.ok:
            error_message = (
                response_data.get(
                    "error",
                    {},
                ).get(
                    "message",
                    f"API returned HTTP "
                    f"{status_code}."
                )
                if isinstance(
                    response_data,
                    dict,
                )
                else (
                    f"API returned HTTP "
                    f"{status_code}."
                )
            )

            logger.error(
                "Non-retryable API error | "
                f"status={status_code} | "
                f"message={error_message}"
            )

            return {
                "success": False,
                "stage": "api_error",
                "errors": [
                    error_message
                ],
                "raw_response": response_data,
                "parsed_content": None,
                "metadata": None,
                "status_code": status_code,
                "attempts": attempt_number,
            }

        try:
            content = parse_llm_response(
                response_data
            )

            metadata = (
                extract_response_metadata(
                    response_data
                )
            )

        except ValueError as error:
            return {
                "success": False,
                "stage": "response_validation",
                "errors": [
                    str(error)
                ],
                "raw_response": response_data,
                "parsed_content": None,
                "metadata": None,
                "status_code": status_code,
                "attempts": attempt_number,
            }

        logger.info(
            "API request succeeded | "
            f"status={status_code} | "
            f"attempts={attempt_number}"
        )

        return {
            "success": True,
            "stage": "complete",
            "errors": [],
            "raw_response": response_data,
            "parsed_content": content,
            "metadata": metadata,
            "status_code": status_code,
            "attempts": attempt_number,
        }

    return {
        "success": False,
        "stage": "unknown",
        "errors": [
            "Request ended without a result."
        ],
        "raw_response": None,
        "parsed_content": None,
        "metadata": None,
        "status_code": None,
        "attempts": max_retries + 1,
    }
