import json

from config import DEFAULT_MODEL
from payload_builder import build_chat_payload
from services.llm_service import send_llm_request


payload = build_chat_payload(
    model=DEFAULT_MODEL,
    system_prompt=(
        "You are a helpful assistant. "
        "Answer clearly and briefly."
    ),
    user_prompt=(
        "Explain JSON payloads in simple words."
    ),
    temperature=0.2,
    max_tokens=300,
)


print("\nREQUEST PAYLOAD:\n")

print(
    json.dumps(
        payload,
        indent=4,
    )
)


result = send_llm_request(
    payload
)


print("\nSUCCESS:")
print(result["success"])


print("\nSTAGE:")
print(result["stage"])


print("\nERRORS:")
print(result["errors"])


if result["success"]:

    print("\nPARSED CONTENT:\n")
    print(
        result["parsed_content"]
    )

    print("\nMETADATA:\n")
    print(
        json.dumps(
            result["metadata"],
            indent=4,
        )
    )

    print("\nRAW RESPONSE:\n")
    print(
        json.dumps(
            result["raw_response"],
            indent=4,
        )
    )