from typing import List
from pydantic import BaseModel, Field


class Measurement(BaseModel):
    name: str = Field(
        description="Name of the measurement."
    )

    value: str = Field(
        description="Measurement value including unit when available."
    )


class ImportantTerm(BaseModel):
    term: str = Field(
        description="Medical or technical term."
    )

    explanation: str = Field(
        description="Clear explanation of the term."
    )


class ClinicalStructuredOutput(BaseModel):

    summary: str = Field(
        description="Concise and accurate summary of the clinical note."
    )

    key_findings: List[str] = Field(
        description=(
            "Important findings explicitly supported by the note. "
            "Return an empty list if none exist."
        )
    )

    measurements: List[Measurement] = Field(
        description=(
            "Measurements and values found in the note. "
            "Return an empty list if none exist."
        )
    )

    uncertainties: List[str] = Field(
        description=(
            "Statements showing uncertainty, possibility, or suspicion. "
            "Return an empty list if none exist."
        )
    )

    important_terms: List[ImportantTerm] = Field(
        description=(
            "Important medical terms with explanations. "
            "Return an empty list if none exist."
        )
    )

    safety_note: str = Field(
        description=(
            "Short statement explaining that the generated output "
            "does not replace professional medical evaluation."
        )
    )