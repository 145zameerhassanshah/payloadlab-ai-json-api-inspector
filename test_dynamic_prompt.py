import json

from services.structured_prompt_service import (
    build_dynamic_system_prompt,
    get_expected_schema,
    validate_structured_output,
)


patient_context = (
    "Adult outpatient with a history "
    "of hypertension."
)


system_prompt = build_dynamic_system_prompt(
    user_role="Patient",
    patient_context=patient_context,
    note_type="Radiology Report",
    output_style="Patient-Friendly JSON",
)


print(
    "\nDYNAMIC SYSTEM PROMPT\n"
)

print(
    system_prompt
)


print(
    "\nEXPECTED SCHEMA\n"
)

print(
    json.dumps(
        get_expected_schema(),
        indent=2,
    )
)


test_output = {
    "summary": (
        "The chest X-ray shows an abnormal area "
        "in the lower right lung."
    ),

    "key_findings": [
        "Right lower lung infiltrate"
    ],

    "measurements": [
        {
            "name": "Blood Pressure",
            "value": "150/95 mmHg",
        }
    ],

    "uncertainties": [
        "Possible lower respiratory tract infection"
    ],

    "important_terms": [
        {
            "term": "Infiltrate",
            "explanation": (
                "An area on the X-ray that appears "
                "different from normal lung tissue."
            ),
        }
    ],

    "safety_note": (
        "This explanation does not replace "
        "professional medical advice."
    ),
}


validated = validate_structured_output(
    test_output
)


print(
    "\nSCHEMA VALIDATION SUCCESSFUL\n"
)

print(
    validated.model_dump()
)