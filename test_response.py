from response_parser import parse_llm_response


# --------------------------------------------------
# VALID RESPONSE
# --------------------------------------------------

valid_response = {
    "id": "response_123",
    "model": "demo-model",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "JSON is a structured data format."
            }
        }
    ]
}


print("\nVALID RESPONSE:")

try:
    result = parse_llm_response(
        valid_response
    )

    print(result)

except ValueError as error:
    print("Validation Error:", error)


# --------------------------------------------------
# INVALID RESPONSE
# Missing content
# --------------------------------------------------

invalid_response = {
    "id": "response_456",
    "choices": [
        {
            "message": {
                "role": "assistant"
            }
        }
    ]
}


print("\nINVALID RESPONSE:")

try:
    result = parse_llm_response(
        invalid_response
    )

    print(result)

except ValueError as error:
    print("Validation Error:", error)