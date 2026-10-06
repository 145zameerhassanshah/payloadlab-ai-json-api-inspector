from typing import Dict, Any, List


def validate_payload(
    payload: Dict[str, Any]
) -> List[str]:
    """
    Validate expected fields in an LLM request payload.

    Returns a list of validation errors.
    An empty list means the payload is valid.
    """

    errors = []

    if not isinstance(payload, dict):
        return [
            "Payload must be a dictionary."
        ]

    if "model" not in payload:
        errors.append(
            "Missing required field: model"
        )

    elif not isinstance(
        payload["model"],
        str
    ):
        errors.append(
            "Field 'model' must be a string."
        )

    elif not payload["model"].strip():
        errors.append(
            "Field 'model' cannot be empty."
        )


    if "messages" not in payload:
        errors.append(
            "Missing required field: messages"
        )

    elif not isinstance(
        payload["messages"],
        list
    ):
        errors.append(
            "Field 'messages' must be a list."
        )

    elif len(
        payload["messages"]
    ) == 0:
        errors.append(
            "Field 'messages' cannot be empty."
        )


    if "temperature" in payload:

        temperature = payload[
            "temperature"
        ]

        if not isinstance(
            temperature,
            (int, float)
        ):
            errors.append(
                "Field 'temperature' must be a number."
            )

        elif not 0 <= temperature <= 2:
            errors.append(
                "Field 'temperature' must be between 0 and 2."
            )


    if "max_tokens" in payload:

        max_tokens = payload[
            "max_tokens"
        ]

        if not isinstance(
            max_tokens,
            int
        ):
            errors.append(
                "Field 'max_tokens' must be an integer."
            )

        elif max_tokens <= 0:
            errors.append(
                "Field 'max_tokens' must be greater than 0."
            )


    return errors