import random

from utils.retry import (
    SimulatedRateLimitError,
    SimulatedServerError,
    SimulatedTimeoutError,
)


def simulate_api_operation(
    note_id: int,
    failure_mode: str = "mixed",
):
    """
    Simulate an API operation for testing
    retry and failure-handling behavior.
    """

    if failure_mode == "none":
        return (
            f"Note {note_id} processed successfully."
        )


    if failure_mode == "rate_limit":
        raise SimulatedRateLimitError(
            "Simulated HTTP 429 rate limit."
        )


    if failure_mode == "timeout":
        raise SimulatedTimeoutError(
            "Simulated request timeout."
        )


    if failure_mode == "server_error":
        raise SimulatedServerError(
            "Simulated HTTP 503 service unavailable."
        )


    if failure_mode == "mixed":

        chance = random.random()

        if chance < 0.15:
            raise SimulatedRateLimitError(
                "Simulated HTTP 429."
            )

        if chance < 0.25:
            raise SimulatedTimeoutError(
                "Simulated timeout."
            )

        if chance < 0.35:
            raise SimulatedServerError(
                "Simulated HTTP 503."
            )

        return (
            f"Note {note_id} processed successfully."
        )


    raise ValueError(
        f"Unknown failure mode: {failure_mode}"
    )