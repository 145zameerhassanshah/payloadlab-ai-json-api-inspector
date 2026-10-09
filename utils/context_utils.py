from typing import List, Dict, Any

try:
    import tiktoken
except ImportError:
    tiktoken = None


DEFAULT_ENCODING = "cl100k_base"


def get_encoder():
    """
    Return a tokenizer encoder.

    cl100k_base is used as a practical estimate for many modern LLMs.
    Exact token counts can vary by model/provider.
    """
    if tiktoken is None:
        return None
    return tiktoken.get_encoding(DEFAULT_ENCODING)


def count_tokens(text: str) -> int:
    """
    Estimate token count for text.
    """
    if not text:
        return 0

    encoder = get_encoder()

    if encoder is not None:
        return len(encoder.encode(text))

    # Fallback estimate if tiktoken is unavailable.
    # Roughly 1 token per ~4 characters for English-like text.
    return max(1, len(text) // 4)


def calculate_input_budget(
    context_limit: int,
    reserved_output_tokens: int,
    system_prompt_tokens: int = 0,
    other_context_tokens: int = 0,
    safety_margin: int = 128,
) -> int:
    """
    Calculate how many tokens remain available for user input.
    """
    budget = (
        context_limit
        - reserved_output_tokens
        - system_prompt_tokens
        - other_context_tokens
        - safety_margin
    )
    return max(0, budget)


def truncate_text(
    text: str,
    max_tokens: int,
    keep: str = "start",
) -> str:
    """
    Truncate text to a token budget.

    keep:
        "start" -> keep the beginning
        "end"   -> keep the end
    """
    if max_tokens <= 0 or not text:
        return ""

    encoder = get_encoder()

    if encoder is None:
        # Fallback approximation.
        char_budget = max_tokens * 4
        return (
            text[:char_budget]
            if keep == "start"
            else text[-char_budget:]
        )

    tokens = encoder.encode(text)

    if len(tokens) <= max_tokens:
        return text

    selected = (
        tokens[:max_tokens]
        if keep == "start"
        else tokens[-max_tokens:]
    )

    return encoder.decode(selected)


def chunk_text(
    text: str,
    chunk_size: int,
    overlap: int = 0,
) -> List[str]:
    """
    Split long text into token-based chunks with optional overlap.
    """
    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")

    if overlap < 0:
        raise ValueError("overlap cannot be negative.")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    encoder = get_encoder()

    if encoder is None:
        # Character fallback using same rough conversion.
        char_chunk = chunk_size * 4
        char_overlap = overlap * 4
        step = max(1, char_chunk - char_overlap)

        return [
            text[start:start + char_chunk]
            for start in range(0, len(text), step)
        ]

    tokens = encoder.encode(text)

    if len(tokens) <= chunk_size:
        return [text]

    chunks = []
    step = chunk_size - overlap

    for start in range(0, len(tokens), step):
        chunk_tokens = tokens[start:start + chunk_size]
        if not chunk_tokens:
            break

        chunks.append(
            encoder.decode(chunk_tokens)
        )

        if start + chunk_size >= len(tokens):
            break

    return chunks


def analyze_context(
    text: str,
    context_limit: int,
    reserved_output_tokens: int,
    system_prompt: str = "",
    other_context_tokens: int = 0,
    safety_margin: int = 128,
) -> Dict[str, Any]:
    """
    Return context-window usage information.
    """
    input_tokens = count_tokens(text)
    system_tokens = count_tokens(system_prompt)

    available_input_budget = calculate_input_budget(
        context_limit=context_limit,
        reserved_output_tokens=reserved_output_tokens,
        system_prompt_tokens=system_tokens,
        other_context_tokens=other_context_tokens,
        safety_margin=safety_margin,
    )

    overflow_tokens = max(
        0,
        input_tokens - available_input_budget,
    )

    utilization = (
        (input_tokens / available_input_budget) * 100
        if available_input_budget > 0
        else 100.0
    )

    if overflow_tokens > 0:
        status = "OVERFLOW"
    elif utilization >= 90:
        status = "WARNING"
    else:
        status = "SAFE"

    return {
        "input_tokens": input_tokens,
        "system_prompt_tokens": system_tokens,
        "context_limit": context_limit,
        "reserved_output_tokens": reserved_output_tokens,
        "other_context_tokens": other_context_tokens,
        "safety_margin": safety_margin,
        "available_input_budget": available_input_budget,
        "overflow_tokens": overflow_tokens,
        "utilization_percent": utilization,
        "status": status,
    }
