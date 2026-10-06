from payload_builder import build_chat_payload
from validators import validate_payload


valid_payload = build_chat_payload(
    model="openrouter/free",
    system_prompt="You are helpful.",
    user_prompt="Explain APIs.",
)


valid_errors = validate_payload(
    valid_payload
)


print("\nVALID PAYLOAD ERRORS:")
print(valid_errors)


invalid_payload = {
    "model": "",
    "messages": [],
    "temperature": "high",
    "max_tokens": -10,
}


invalid_errors = validate_payload(
    invalid_payload
)


print("\nINVALID PAYLOAD ERRORS:")

for error in invalid_errors:
    print("-", error)