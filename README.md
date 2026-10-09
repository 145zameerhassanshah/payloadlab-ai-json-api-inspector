# PayloadLab AI

## LLM API Inspector, Reliability & Context Management Toolkit

PayloadLab AI is a developer-focused Streamlit application designed to help users understand, construct, validate, debug, and reliably operate JSON-based LLM API workflows.

The application combines three major capabilities:

1. **JSON & API Inspection** — build structured request payloads, validate expected fields, inspect nested responses, extract assistant content, and review useful metadata.
2. **API Reliability & Batch Recovery** — process batches of synthetic patient notes while handling rate limits, request timeouts, connection failures, and temporary server errors using retries, exponential backoff, logging, checkpointing, and resume processing.
3. **Context Management** — count tokens, calculate safe context budgets, detect context-window overflow, and handle oversized inputs using truncation, chunking, overlap, and summarization strategies.

---

## Project Objective

The objective of this project is to build practical understanding of reliable and scalable LLM API engineering.

The project covers:

- JSON payload construction
- API request structures
- nested response parsing
- data validation
- secure environment-variable management
- rate-limit handling
- request timeout handling
- transient server-error recovery
- retry logic
- exponential backoff
- jitter
- structured logging
- batch processing
- checkpoint persistence
- resumable processing
- token counting
- context-window management
- token-budget calculation
- overflow detection
- truncation
- chunking
- chunk overlap
- hierarchical summarization

The project builds on basic LLM API integration by exposing request/response structures, reliability mechanisms, and context-management strategies that are normally hidden behind higher-level SDK abstractions.

---

## Core Features

### JSON Inspector

- JSON request payload construction
- Dynamic LLM request generation
- Request payload preview
- Required field validation
- Datatype validation
- Nested JSON response parsing
- Raw response inspection
- Parsed AI response extraction
- Response metadata extraction
- Token usage inspection
- HTTP/API error handling
- Secure API-key management
- Environment variable configuration
- `.env.example` support
- Git-safe secret handling

### Batch Reliability Lab

- Batch processing of 50 synthetic patient notes
- Simulation mode
- Live LLM API mode
- HTTP `429` rate-limit handling
- HTTP `500`, `502`, `503`, `504` handling
- Request timeout recovery
- Connection failure handling
- Retry logic
- Exponential backoff
- Random jitter
- `Retry-After` header support
- Maximum retry protection
- Structured failure logging
- Checkpoint-based progress persistence
- Incremental result saving
- Failed-note tracking
- Resume processing
- Skip already-completed notes
- Partial failure handling
- Streamlit recovery dashboard
- Saved summary inspection
- Reliability log viewer

### Context Management Lab

- Token counting
- Context-window analysis
- Input-token budget calculation
- Reserved output-token handling
- System-prompt token accounting
- Other-context token accounting
- Safety margin support
- Context utilization percentage
- `SAFE`, `WARNING`, and `OVERFLOW` states
- Context overflow detection
- Start/head truncation
- End/tail truncation
- Token-based chunking
- Configurable chunk size
- Configurable chunk overlap
- Long-input summarization
- Hierarchical chunk summarization
- Original vs processed token comparison
- Individual chunk inspection
- Streamlit context-safety dashboard

---

## JSON Learning Concepts

This project demonstrates:

- JSON objects
- JSON arrays
- Strings
- Numbers
- Booleans
- Null values
- Python dictionaries
- Python lists
- Serialization
- Deserialization
- Nested JSON
- Safe field access
- Required field validation

---

## API Reliability Concepts

This project also demonstrates:

- API failure modes
- HTTP status codes
- retryable vs non-retryable errors
- `try/except`
- request timeouts
- network connection failures
- server errors
- rate limits
- retry policies
- exponential backoff
- jitter
- `Retry-After`
- structured logging
- batch processing
- checkpointing
- incremental persistence
- resume/recovery
- partial failure handling

---

## Context Management Concepts

### Tokens

LLMs process text as tokens rather than simple words or characters.

A single word may contain one or multiple tokens depending on the tokenizer and model.

### Context Window

A context window is the maximum number of tokens a model can consider in a single request.

The available context may include:

- system prompt
- user input
- chat history
- retrieved documents
- tool output
- generated response budget

### Token Budget

PayloadLab calculates the available input budget using:

```text
Available Input Budget
=
Context Window
- Reserved Output Tokens
- System Prompt Tokens
- Other Context Tokens
<<<<<<< HEAD
- Safety Margin
=======
- Safety Margin
>>>>>>> 992f2ca98444d14775a68695e12bdab725663583
