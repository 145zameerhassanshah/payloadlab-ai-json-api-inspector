from utils.context_utils import (
    count_tokens,
    analyze_context,
    truncate_text,
    chunk_text,
)


sample_text = (
    "Artificial intelligence systems process text as tokens. "
    * 500
)

analysis = analyze_context(
    text=sample_text,
    context_limit=2048,
    reserved_output_tokens=400,
    system_prompt=(
        "You are a helpful assistant."
    ),
)

print("CONTEXT ANALYSIS")
print(analysis)

print("\nTRUNCATION TEST")
truncated = truncate_text(
    sample_text,
    max_tokens=500,
)
print("Tokens after truncation:", count_tokens(truncated))

print("\nCHUNKING TEST")
chunks = chunk_text(
    sample_text,
    chunk_size=500,
    overlap=50,
)
print("Chunks created:", len(chunks))
print(
    "Chunk token counts:",
    [count_tokens(chunk) for chunk in chunks],
)
