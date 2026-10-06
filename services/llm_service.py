import time
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


def send_llm_request(
    payload: dict,
    max_retries: int = 3,
) -> dict:

    # 1. Validate payload
    payload_errors = validate_payload(payload)

    if payload_errors:
        return {
            "success": False,
            "stage": "payload_validation",
            "errors": payload_errors,
            "raw_response": None,
            "parsed_content": None,
            "metadata": None,
        }

    # 2. Check API key
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
        }

    # 3. Headers
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    # 4. Endpoint
    endpoint = (
        f"{OPENROUTER_BASE_URL}/chat/completions"
    )

    response = None

    # 5. API request with retry
    for attempt in range(max_retries):

        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=(10, 90),
            )

            break

        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as error:

            print(
                f"Network attempt {attempt + 1} failed: "
                f"{error}"
            )

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
                continue

            return {
                "success": False,
                "stage": "network",
                "errors": [
                    "The connection to the AI service was interrupted. "
                    "Please try again."
                ],
                "raw_response": None,
                "parsed_content": None,
                "metadata": None,
            }

        except requests.exceptions.RequestException as error:

            return {
                "success": False,
                "stage": "network",
                "errors": [
                    f"Request error: {error}"
                ],
                "raw_response": None,
                "parsed_content": None,
                "metadata": None,
            }

    # 6. Parse JSON
    try:
        response_data = response.json()

    except ValueError:

        return {
            "success": False,
            "stage": "response_json",
            "errors": [
                "The API response was not valid JSON."
            ],
            "raw_response": response.text,
            "parsed_content": None,
            "metadata": None,
        }

    # 7. Handle HTTP/API error
    if not response.ok:

        error_message = (
            response_data.get("error", {}).get(
                "message",
                f"API returned HTTP {response.status_code}."
            )
            if isinstance(response_data, dict)
            else f"API returned HTTP {response.status_code}."
        )

        return {
            "success": False,
            "stage": "api_error",
            "errors": [error_message],
            "raw_response": response_data,
            "parsed_content": None,
            "metadata": None,
        }

    # 8. Parse nested response
    try:
        content = parse_llm_response(
            response_data
        )

        metadata = extract_response_metadata(
            response_data
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
        }

    # 9. Success
    return {
        "success": True,
        "stage": "complete",
        "errors": [],
        "raw_response": response_data,
        "parsed_content": content,
        "metadata": metadata,
    }