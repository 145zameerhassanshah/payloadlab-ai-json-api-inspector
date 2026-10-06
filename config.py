import os

from dotenv import load_dotenv


load_dotenv()


APP_NAME = "PayloadLab AI"
APP_TAGLINE = "Inspect. Validate. Understand AI API Data."


OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


DEFAULT_MODEL = os.getenv(
    "DEFAULT_MODEL",
    "openrouter/free"
)


APP_ENV = os.getenv(
    "APP_ENV",
    "development"
)


def validate_config():
    """
    Validate required application configuration.

    Returns:
        list: A list of configuration errors.
              An empty list means configuration is valid.
    """

    errors = []

    if not OPENROUTER_API_KEY:
        errors.append(
            "OPENROUTER_API_KEY is missing."
        )

    if not DEFAULT_MODEL:
        errors.append(
            "DEFAULT_MODEL is missing."
        )

    return errors