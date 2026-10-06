from typing import Any, Dict


def parse_llm_response(
    response: Dict[str, Any]
) -> str:

    if not isinstance(response, dict):
        raise ValueError(
            "Response must be a dictionary."
        )

    choices = response.get("choices")

    if choices is None:
        raise ValueError(
            "Missing expected field: choices"
        )

    if not isinstance(choices, list):
        raise ValueError(
            "Field 'choices' must be a list."
        )

    if not choices:
        raise ValueError(
            "Field 'choices' is empty."
        )

    first_choice = choices[0]

    if not isinstance(first_choice, dict):
        raise ValueError(
            "First choice must be an object."
        )

    message = first_choice.get("message")

    if not isinstance(message, dict):
        raise ValueError(
            "Missing or invalid field: message"
        )

    content = message.get("content")

    if not isinstance(content, str):
        raise ValueError(
            "Missing or invalid field: content"
        )

    if not content.strip():
        raise ValueError(
            "Field 'content' cannot be empty."
        )

    return content.strip()


def extract_response_metadata(
    response: Dict[str, Any]
) -> Dict[str, Any]:

    usage = response.get(
        "usage",
        {}
    )

    if not isinstance(usage, dict):
        usage = {}

    return {
        "id": response.get("id"),
        "model": response.get("model"),
        "prompt_tokens": usage.get(
            "prompt_tokens"
        ),
        "completion_tokens": usage.get(
            "completion_tokens"
        ),
        "total_tokens": usage.get(
            "total_tokens"
        ),
    }