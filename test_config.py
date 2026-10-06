from config import (
    APP_NAME,
    DEFAULT_MODEL,
    APP_ENV,
    OPENROUTER_API_KEY,
    validate_config,
)


print("\nAPP NAME:")
print(APP_NAME)


print("\nDEFAULT MODEL:")
print(DEFAULT_MODEL)


print("\nAPP ENV:")
print(APP_ENV)


print("\nAPI KEY LOADED:")
print(bool(OPENROUTER_API_KEY))


print("\nCONFIG ERRORS:")
print(validate_config())