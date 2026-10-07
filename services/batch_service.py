import json
from pathlib import Path
from typing import Dict, Any

from config import DEFAULT_MODEL
from payload_builder import build_chat_payload
from services.failure_simulator import (
    simulate_api_operation,
)
from services.llm_service import (
    send_llm_request,
)
from utils.retry import (
    run_with_retry,
)
from utils.checkpoint import (
    load_checkpoint,
    save_checkpoint,
)
from utils.logger import get_logger


logger = get_logger()

NOTES_FILE = Path(
    "data/synthetic_notes.json"
)

TOTAL_NOTES = 50


def load_patient_notes() -> list[dict]:
    """
    Load the 50 synthetic patient notes.
    """

    with open(
        NOTES_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        notes = json.load(file)

    if not isinstance(notes, list):
        raise ValueError(
            "synthetic_notes.json must "
            "contain a JSON array."
        )

    return notes


def get_batch_status(
    checkpoint: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Return dashboard-friendly batch counts.
    """

    completed_ids = set(
        checkpoint.get(
            "completed",
            [],
        )
    )

    failed_ids = set(
        checkpoint.get(
            "failed",
            [],
        )
    )

    completed_count = len(
        completed_ids
    )

    failed_count = len(
        failed_ids
    )

    not_processed = max(
        TOTAL_NOTES
        - completed_count
        - failed_count,
        0,
    )

    success_rate = (
        completed_count
        / TOTAL_NOTES
        * 100
    )

    return {
        "completed": completed_count,
        "failed": failed_count,
        "not_processed": not_processed,
        "success_rate": success_rate,
    }


def summarize_note_simulated(
    note: Dict[str, Any],
    failure_mode: str = "mixed",
) -> str:
    """
    Simulate an LLM summarization request.
    """

    note_id = note["id"]

    simulate_api_operation(
        note_id=note_id,
        failure_mode=failure_mode,
    )

    return (
        f"Summary for note {note_id}: "
        f"{note['note']}"
    )


def summarize_note_live(
    note: Dict[str, Any],
    max_retries: int,
    base_delay: float,
) -> str:
    """
    Send one synthetic patient note to
    the real LLM API for summarization.
    """

    payload = build_chat_payload(
        model=DEFAULT_MODEL,
        system_prompt=(
            "You summarize synthetic clinical "
            "notes for a software reliability "
            "exercise. Give a concise factual "
            "summary. Preserve uncertainty and "
            "measurements. Do not invent a "
            "diagnosis, treatment, or facts."
        ),
        user_prompt=(
            "Summarize this synthetic patient "
            f"note:\n\n{note['note']}"
        ),
        temperature=0.1,
        max_tokens=250,
    )

    result = send_llm_request(
        payload=payload,
        max_retries=max_retries,
        base_delay=base_delay,
    )

    if not result["success"]:
        error_text = "; ".join(
            result["errors"]
        )

        raise RuntimeError(
            f"{result['stage']}: "
            f"{error_text}"
        )

    return result["parsed_content"]


def process_batch(
    mode: str = "simulation",
    failure_mode: str = "mixed",
    max_retries: int = 3,
    base_delay: float = 0.5,
) -> Dict[str, Any]:
    """
    Process all notes with progress
    checkpointing.

    mode:
        simulation
        live
    """

    if mode not in {
        "simulation",
        "live",
    }:
        raise ValueError(
            "mode must be 'simulation' "
            "or 'live'."
        )

    notes = load_patient_notes()
    checkpoint = load_checkpoint()

    completed = set(
        checkpoint.get(
            "completed",
            [],
        )
    )

    logger.info(
        "Batch started | "
        f"mode={mode} | "
        f"total_notes={len(notes)} | "
        f"already_completed={len(completed)}"
    )

    for note in notes:
        note_id = note["id"]

        if note_id in completed:
            logger.info(
                "Skipping completed note | "
                f"note_id={note_id}"
            )
            continue

        logger.info(
            "Processing note | "
            f"note_id={note_id} | "
            f"mode={mode}"
        )

        try:
            if mode == "simulation":

                def operation():
                    return summarize_note_simulated(
                        note=note,
                        failure_mode=failure_mode,
                    )

                summary = run_with_retry(
                    operation=operation,
                    max_retries=max_retries,
                    base_delay=base_delay,
                )

            else:
                summary = summarize_note_live(
                    note=note,
                    max_retries=max_retries,
                    base_delay=base_delay,
                )

            checkpoint[
                "results"
            ][str(note_id)] = summary

            if (
                note_id
                not in checkpoint["completed"]
            ):
                checkpoint[
                    "completed"
                ].append(note_id)

            if (
                note_id
                in checkpoint["failed"]
            ):
                checkpoint[
                    "failed"
                ].remove(note_id)

            save_checkpoint(
                checkpoint
            )

            completed.add(
                note_id
            )

            logger.info(
                "Note completed | "
                f"note_id={note_id}"
            )

        except KeyboardInterrupt:
            logger.warning(
                "Batch interrupted by user | "
                f"last_note_id={note_id}"
            )

            save_checkpoint(
                checkpoint
            )

            raise

        except Exception as error:
            logger.error(
                "Note failed | "
                f"note_id={note_id} | "
                f"error={type(error).__name__} | "
                f"message={error}"
            )

            if (
                note_id
                not in checkpoint["failed"]
            ):
                checkpoint[
                    "failed"
                ].append(note_id)

            save_checkpoint(
                checkpoint
            )

    logger.info(
        "Batch processing finished | "
        f"completed={len(checkpoint['completed'])} | "
        f"failed={len(checkpoint['failed'])}"
    )

    return checkpoint
