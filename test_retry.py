from utils.retry import (
    run_with_retry,
    SimulatedRateLimitError,
)


attempt_counter = {
    "count": 0
}


def test_operation():

    attempt_counter["count"] += 1

    print(
        f"Running attempt "
        f"{attempt_counter['count']}"
    )

    # First two attempts fail
    if attempt_counter["count"] <= 2:

        raise SimulatedRateLimitError(
            "Simulated HTTP 429 rate limit."
        )

    # Third attempt succeeds
    return (
        "Request processed successfully "
        "after temporary rate-limit failures."
    )


try:

    result = run_with_retry(
        operation=test_operation,
        max_retries=3,
        base_delay=0.5,
    )

    print("\nSUCCESS:")
    print(result)

except Exception as error:

    print("\nFAILED:")

    print(
        type(error).__name__,
        str(error),
    )