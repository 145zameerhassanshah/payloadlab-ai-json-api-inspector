# PayloadLab AI

## JSON Payload & LLM API Response Inspector

PayloadLab AI is a developer-focused Streamlit application designed to help users understand, construct, validate, and debug JSON-based LLM API communication.

The application allows users to build structured request payloads, validate expected fields, send API requests, inspect nested JSON responses, extract assistant content, and review useful response metadata.

---

## Project Objective

The objective of this project is to develop a deeper understanding of JSON payloads, API request structures, nested response parsing, data validation, and secure environment-variable management.

The project builds on basic LLM API integration by exposing the request and response structures that are normally hidden behind SDK calls.

---

## Core Features

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
- Network timeout handling
- Retry logic
- Secure API-key management
- Environment variable configuration
- `.env.example` support
- Git-safe secret handling
- Professional Streamlit dashboard

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
