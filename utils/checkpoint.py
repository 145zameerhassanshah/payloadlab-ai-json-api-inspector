import json
from pathlib import Path
from typing import Dict, Any


DATA_DIR = Path("data")
DATA_DIR.mkdir(
    exist_ok=True
)

CHECKPOINT_FILE = (
    DATA_DIR / "progress.json"
)

TEMP_CHECKPOINT_FILE = (
    DATA_DIR / "progress.tmp.json"
)


def create_empty_checkpoint() -> Dict[str, Any]:
    return {
        "completed": [],
        "failed": [],
        "results": {},
    }


def _normalize_checkpoint(
    checkpoint: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Guarantee required checkpoint fields.
    """

    if not isinstance(
        checkpoint,
        dict,
    ):
        return create_empty_checkpoint()

    checkpoint.setdefault(
        "completed",
        [],
    )

    checkpoint.setdefault(
        "failed",
        [],
    )

    checkpoint.setdefault(
        "results",
        {},
    )

    return checkpoint


def load_checkpoint() -> Dict[str, Any]:
    """
    Load saved batch progress.
    """

    if not CHECKPOINT_FILE.exists():
        return create_empty_checkpoint()

    try:
        with open(
            CHECKPOINT_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            checkpoint = json.load(
                file
            )

        return _normalize_checkpoint(
            checkpoint
        )

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return create_empty_checkpoint()


def save_checkpoint(
    checkpoint: Dict[str, Any],
) -> None:
    """
    Save progress using a temporary file,
    then replace the real checkpoint.

    This reduces the risk of leaving a
    half-written JSON file if the program
    stops while saving.
    """

    normalized = _normalize_checkpoint(
        checkpoint
    )

    with open(
        TEMP_CHECKPOINT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            normalized,
            file,
            indent=4,
            ensure_ascii=False,
        )

    TEMP_CHECKPOINT_FILE.replace(
        CHECKPOINT_FILE
    )


def reset_checkpoint() -> None:
    """
    Delete saved progress.
    """

    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()

    if TEMP_CHECKPOINT_FILE.exists():
        TEMP_CHECKPOINT_FILE.unlink()
