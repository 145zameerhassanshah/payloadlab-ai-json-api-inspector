# PayloadLab AI

## LLM API Inspector & Reliability Toolkit

PayloadLab AI is a developer-focused Streamlit application designed to help users understand, construct, validate, debug, and reliably operate JSON-based LLM API workflows.

The application combines two major capabilities:

1. **JSON & API Inspection** — build structured request payloads, validate expected fields, inspect nested responses, extract assistant content, and review useful metadata.
2. **API Reliability & Batch Recovery** — process batches of synthetic patient notes while handling rate limits, request timeouts, connection failures, and temporary server errors using retries, exponential backoff, logging, checkpointing, and resume processing.

---

## Project Objective

The objective of this project is to build practical understanding of reliable LLM API engineering.

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

The project builds on basic LLM API integration by exposing both the request/response structures and the reliability mechanisms that are normally hidden behind higher-level SDKs.

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

## Example Request Payload

```json
{
  "model": "openrouter/free",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful AI assistant."
    },
    {
      "role": "user",
      "content": "Explain JSON payloads simply."
    }
  ],
  "temperature": 0.2,
  "max_tokens": 500
}
