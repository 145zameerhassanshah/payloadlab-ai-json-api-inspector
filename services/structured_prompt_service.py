import json
import re

from typing import Dict, Any

from pydantic import ValidationError

from config import DEFAULT_MODEL

from payload_builder import build_chat_payload

from services.llm_service import send_llm_request

from utils.output_schemas import ClinicalStructuredOutput


# --------------------------------------------------
# ROLE-SPECIFIC INSTRUCTIONS
# --------------------------------------------------

ROLE_INSTRUCTIONS = {

    "Patient": (
        "Use simple patient-friendly language. "
        "Explain unavoidable medical terms clearly. "
        "Do not assume medical knowledge."
    ),

    "Physician": (
        "Use concise clinical terminology. "
        "Highlight clinically relevant findings, "
        "measurements, and uncertainty."
    ),

    "Nurse": (
        "Use clear clinical language. "
        "Emphasize observations, measurements, "
        "and documented care-related information."
    ),

    "Researcher": (
        "Use structured analytical language. "
        "Preserve measurable findings, uncertainty, "
        "and clinically relevant variables."
    ),

    "Healthcare Administrator": (
        "Use concise operational language. "
        "Focus on documented information without "
        "adding unsupported clinical interpretation."
    ),
}


# --------------------------------------------------
# NOTE-SPECIFIC INSTRUCTIONS
# --------------------------------------------------

NOTE_TYPE_INSTRUCTIONS = {

    "Progress Note": (
        "Focus on symptoms, observations, progress, "
        "and documented assessment details."
    ),

    "Discharge Summary": (
        "Focus on admission reason, hospital course, "
        "important findings, and documented "
        "discharge information."
    ),

    "Radiology Report": (
        "Focus on imaging findings, measurements, "
        "impression, and uncertainty."
    ),

    "Lab Report": (
        "Focus on test names, measured values, units, "
        "and explicitly stated interpretation."
    ),

    "Consultation Note": (
        "Focus on consultation reason, major findings, "
        "documented impressions, and recommendations "
        "already present in the note."
    ),

    "Emergency Note": (
        "Focus on presenting concern, key observations, "
        "measurements, and documented urgent findings."
    ),
}


# --------------------------------------------------
# OUTPUT STYLE INSTRUCTIONS
# --------------------------------------------------

OUTPUT_STYLE_INSTRUCTIONS = {

    "Patient-Friendly JSON": (
        "Use plain language while preserving "
        "the original clinical meaning."
    ),

    "Clinical JSON": (
        "Use concise clinical language suitable "
        "for healthcare professionals."
    ),

    "Research JSON": (
        "Use structured factual language suitable "
        "for analysis and research."
    ),
}


# --------------------------------------------------
# EXPECTED SCHEMA
# --------------------------------------------------

def get_expected_schema() -> Dict[str, Any]:

    return ClinicalStructuredOutput.model_json_schema()


# --------------------------------------------------
# BUILD DYNAMIC SYSTEM PROMPT
# --------------------------------------------------

def build_dynamic_system_prompt(
    user_role: str,
    patient_context: str,
    note_type: str,
    output_style: str,
) -> str:

    role_instruction = ROLE_INSTRUCTIONS.get(
        user_role,
        "Use clear and accurate language.",
    )

    note_instruction = NOTE_TYPE_INSTRUCTIONS.get(
        note_type,
        "Extract the most important information.",
    )

    output_instruction = OUTPUT_STYLE_INSTRUCTIONS.get(
        output_style,
        "Return concise structured JSON.",
    )

    schema = get_expected_schema()

    return f"""
You are a clinical information structuring assistant.

USER ROLE
{user_role}

ROLE-SPECIFIC INSTRUCTIONS
{role_instruction}

PATIENT CONTEXT
{patient_context}

NOTE TYPE
{note_type}

NOTE-SPECIFIC INSTRUCTIONS
{note_instruction}

OUTPUT STYLE
{output_style}

OUTPUT INSTRUCTIONS
{output_instruction}

SAFETY RULES
- Do not invent facts.
- Do not invent diagnoses.
- Do not recommend treatments.
- Preserve uncertainty.
- Preserve important measurements.
- Use only information supported by the supplied note.

STRICT JSON RULES
- Return exactly ONE JSON object.
- Return JSON only.
- Do not include markdown.
- Do not use ```json code fences.
- Do not write explanations before or after the JSON.
- Include ALL required fields.
- If a list has no information, return an empty list [].
- Never omit a required field.

REQUIRED OUTPUT SHAPE

{{
  "summary": "string",
  "key_findings": [],
  "measurements": [
    {{
      "name": "string",
      "value": "string"
    }}
  ],
  "uncertainties": [],
  "important_terms": [
    {{
      "term": "string",
      "explanation": "string"
    }}
  ],
  "safety_note": "string"
}}

FULL JSON SCHEMA
{json.dumps(schema, indent=2)}
""".strip()


# --------------------------------------------------
# BUILD USER PROMPT
# --------------------------------------------------

def build_dynamic_user_prompt(
    clinical_note: str,
) -> str:

    return f"""
Analyze the clinical note below.

Use only the information contained in the note.

Return exactly one JSON object using the required schema.

CLINICAL NOTE

{clinical_note}
""".strip()


# --------------------------------------------------
# CLEAN MODEL OUTPUT
# --------------------------------------------------

def clean_json_output(
    response_text: str,
) -> str:

    if not response_text:
        raise ValueError(
            "The model returned an empty response."
        )

    cleaned = response_text.strip()

    # Remove Markdown JSON fences.
    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    cleaned = cleaned.strip()

    # If the model added prose before/after JSON,
    # keep only the outermost JSON object.
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")

    if (
        first_brace != -1
        and last_brace != -1
        and last_brace > first_brace
    ):
        cleaned = cleaned[
            first_brace:last_brace + 1
        ]

    return cleaned


# --------------------------------------------------
# PARSE JSON
# --------------------------------------------------

def parse_json_output(
    response_text: str,
) -> Dict[str, Any]:

    cleaned = clean_json_output(
        response_text
    )

    try:
        parsed = json.loads(
            cleaned
        )

    except json.JSONDecodeError as error:
        raise ValueError(
            "Model output could not be parsed "
            f"as valid JSON: {error}"
        ) from error

    if not isinstance(
        parsed,
        dict,
    ):
        raise ValueError(
            "Expected a JSON object but "
            f"received {type(parsed).__name__}."
        )

    return parsed


# --------------------------------------------------
# VALIDATE SCHEMA
# --------------------------------------------------

def validate_structured_output(
    data: Dict[str, Any],
) -> ClinicalStructuredOutput:

    try:
        return ClinicalStructuredOutput.model_validate(
            data
        )

    except ValidationError as error:
        raise ValueError(
            "JSON was parsed successfully, "
            "but it did not match the "
            f"expected schema:\n{error}"
        ) from error


# --------------------------------------------------
# JSON REPAIR PROMPT
# --------------------------------------------------

def build_json_repair_payload(
    invalid_output: str,
) -> Dict[str, Any]:
    """
    Ask the LLM to repair malformed JSON once.

    This is used only after the first model response
    cannot be parsed as valid JSON.
    """

    schema = get_expected_schema()

    repair_system_prompt = """
You are a strict JSON repair assistant.

Your task is to convert malformed model output into exactly ONE valid JSON object.

RULES
- Return JSON only.
- Do not use markdown.
- Do not use code fences.
- Do not add explanations.
- Preserve the meaning of the original output.
- Do not invent clinical facts.
- Include every required field.
- Use empty lists [] where list data is unavailable.
""".strip()

    repair_user_prompt = f"""
Repair the following malformed output so it matches this JSON schema.

EXPECTED SCHEMA
{json.dumps(schema, indent=2)}

MALFORMED OUTPUT
{invalid_output}

Return exactly one valid JSON object.
""".strip()

    return build_chat_payload(
        model=DEFAULT_MODEL,
        system_prompt=repair_system_prompt,
        user_prompt=repair_user_prompt,
        temperature=0.0,
        max_tokens=1200,
    )


def repair_json_once(
    invalid_output: str,
) -> Dict[str, Any]:
    """
    Make one controlled repair request.
    """

    repair_payload = build_json_repair_payload(
        invalid_output
    )

    repair_result = send_llm_request(
        payload=repair_payload,
    )

    if not repair_result["success"]:
        return {
            "success": False,
            "errors": repair_result["errors"],
            "raw_output": None,
        }

    return {
        "success": True,
        "errors": [],
        "raw_output": repair_result[
            "parsed_content"
        ],
    }


# --------------------------------------------------
# MAIN REQUEST WORKFLOW
# --------------------------------------------------

def send_dynamic_structured_request(
    user_role: str,
    patient_context: str,
    note_type: str,
    output_style: str,
    clinical_note: str,
) -> Dict[str, Any]:

    system_prompt = build_dynamic_system_prompt(
        user_role=user_role,
        patient_context=patient_context,
        note_type=note_type,
        output_style=output_style,
    )

    user_prompt = build_dynamic_user_prompt(
        clinical_note=clinical_note
    )

    payload = build_chat_payload(
        model=DEFAULT_MODEL,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
        max_tokens=1200,
    )

    api_result = send_llm_request(
        payload=payload,
    )

    if not api_result["success"]:
        return {
            "success": False,
            "stage": api_result["stage"],
            "errors": api_result["errors"],
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "raw_output": None,
            "parsed_json": None,
            "validated_output": None,
            "repair_attempted": False,
            "repair_output": None,
        }

    raw_output = api_result[
        "parsed_content"
    ]

    repair_attempted = False
    repair_output = None

    # ----------------------------------------------
    # JSON PARSING
    # ----------------------------------------------

    try:
        parsed_json = parse_json_output(
            raw_output
        )

    except ValueError as first_error:

        # One automatic repair attempt for malformed JSON.
        repair_attempted = True

        repair_result = repair_json_once(
            raw_output
        )

        if not repair_result["success"]:
            return {
                "success": False,
                "stage": "json_repair_request",
                "errors": [
                    str(first_error),
                    *repair_result["errors"],
                ],
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "raw_output": raw_output,
                "parsed_json": None,
                "validated_output": None,
                "repair_attempted": True,
                "repair_output": None,
            }

        repair_output = repair_result[
            "raw_output"
        ]

        try:
            parsed_json = parse_json_output(
                repair_output
            )

        except ValueError as second_error:
            return {
                "success": False,
                "stage": "json_parsing_after_repair",
                "errors": [
                    str(first_error),
                    str(second_error),
                ],
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "raw_output": raw_output,
                "parsed_json": None,
                "validated_output": None,
                "repair_attempted": True,
                "repair_output": repair_output,
            }

    # ----------------------------------------------
    # SCHEMA VALIDATION
    # ----------------------------------------------

    try:
        validated = validate_structured_output(
            parsed_json
        )

    except ValueError as error:
        return {
            "success": False,
            "stage": "schema_validation",
            "errors": [
                str(error)
            ],
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "raw_output": raw_output,
            "parsed_json": parsed_json,
            "validated_output": None,
            "repair_attempted": repair_attempted,
            "repair_output": repair_output,
        }

    # ----------------------------------------------
    # SUCCESS
    # ----------------------------------------------

    return {
        "success": True,
        "stage": "complete",
        "errors": [],
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "raw_output": raw_output,
        "parsed_json": parsed_json,
        "validated_output": validated.model_dump(),
        "repair_attempted": repair_attempted,
        "repair_output": repair_output,
    }
