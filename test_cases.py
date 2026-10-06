from validators import validate_payload
from response_parser import parse_llm_response


print("\n--- TEST 1: VALID PAYLOAD ---")

valid_payload = {
    "model": "openrouter/free",
    "messages": [
        {
            "role": "user",
            "content": "Explain APIs simply."
        }
    ],
    "temperature": 0.3,
    "max_tokens": 300,
}

errors = validate_payload(valid_payload)

print("Errors:", errors)