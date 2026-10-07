from services.batch_service import (
    process_batch,
)


checkpoint = process_batch(
    failure_mode="mixed",
    max_retries=3,
    base_delay=0.1,
)


print("\nBATCH COMPLETE")

print(
    "Completed:",
    len(
        checkpoint["completed"]
    )
)

print(
    "Failed:",
    len(
        checkpoint["failed"]
    )
)

print(
    "Saved Results:",
    len(
        checkpoint["results"]
    )
)