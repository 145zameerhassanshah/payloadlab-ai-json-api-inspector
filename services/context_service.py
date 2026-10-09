from typing import Dict, Any, List

from config import DEFAULT_MODEL
from payload_builder import build_chat_payload
from services.llm_service import send_llm_request
from utils.context_utils import (
    count_tokens,
    truncate_text,
    chunk_text,
)


def apply_truncation(
    text: str,
    token_budget: int,
    keep: str = "start",
) -> Dict[str, Any]:
    processed = truncate_text(
        text=text,
        max_tokens=token_budget,
        keep=keep,
    )

    return {
        "strategy": "truncation",
        "processed_text": processed,
        "chunks": [processed] if processed else [],
        "original_tokens": count_tokens(text),
        "processed_tokens": count_tokens(processed),
    }


def apply_chunking(
    text: str,
    chunk_size: int,
    overlap: int,
) -> Dict[str, Any]:
    chunks = chunk_text(
        text=text,
        chunk_size=chunk_size,
        overlap=overlap,
    )

    return {
        "strategy": "chunking",
        "processed_text": None,
        "chunks": chunks,
        "original_tokens": count_tokens(text),
        "processed_tokens": sum(
            count_tokens(chunk)
            for chunk in chunks
        ),
    }


def summarize_chunk_with_llm(
    chunk: str,
    max_retries: int = 2,
) -> str:
    payload = build_chat_payload(
        model=DEFAULT_MODEL,
        system_prompt=(
            "You compress long input for an LLM context-management "
            "workflow. Preserve the most important facts, numbers, "
            "uncertainty, decisions, and relationships. Do not invent "
            "information. Return a concise faithful summary."
        ),
        user_prompt=(
            "Summarize the following chunk while preserving essential "
            f"information:\n\n{chunk}"
        ),
        temperature=0.1,
        max_tokens=500,
    )

    result = send_llm_request(
        payload=payload,
        max_retries=max_retries,
        base_delay=0.5,
    )

    if not result["success"]:
        raise RuntimeError(
            f"{result['stage']}: "
            + "; ".join(result["errors"])
        )

    return result["parsed_content"]


def apply_summarization(
    text: str,
    token_budget: int,
    chunk_size: int = 1800,
    overlap: int = 150,
) -> Dict[str, Any]:
    """
    Hierarchical summarization approach:
    1. Split long input into chunks.
    2. Summarize each chunk with the LLM.
    3. Combine summaries.
    4. If still too long, truncate the combined result to the target budget.
    """
    chunks = chunk_text(
        text=text,
        chunk_size=chunk_size,
        overlap=overlap,
    )

    summaries: List[str] = []

    for index, chunk in enumerate(chunks, start=1):
        summary = summarize_chunk_with_llm(
            chunk=chunk,
        )
        summaries.append(
            f"Chunk {index} summary:\n{summary}"
        )

    combined = "\n\n".join(summaries)

    if count_tokens(combined) > token_budget:
        combined = truncate_text(
            text=combined,
            max_tokens=token_budget,
            keep="start",
        )

    return {
        "strategy": "summarization",
        "processed_text": combined,
        "chunks": chunks,
        "chunk_summaries": summaries,
        "original_tokens": count_tokens(text),
        "processed_tokens": count_tokens(combined),
    }
