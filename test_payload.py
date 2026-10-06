import json

from payload_builder import build_chat_payload


payload = build_chat_payload(
    model="openrouter/free",
    system_prompt="You are a helpful AI assistant.",
    user_prompt="Explain JSON payloads simply.",
    temperature=0.2,
    max_tokens=300,
)


print("\nPYTHON PAYLOAD:\n")
print(payload)


print("\nFORMATTED JSON PAYLOAD:\n")
print(
    json.dumps(
        payload,
        indent=4,
    )
)