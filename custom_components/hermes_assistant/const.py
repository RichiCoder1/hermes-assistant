"""Constants for Hermes Assistant."""

from typing import Final

DOMAIN: Final = "hermes_assistant"

CONF_BASE_URL: Final = "base_url"
CONF_API_KEY: Final = "api_key"
CONF_PROMPT: Final = "prompt"
CONF_TIMEOUT: Final = "timeout"
CONF_MAX_RESPONSE_CHARS: Final = "max_response_chars"
CONF_MEMORY_SCOPE: Final = "memory_scope"

DEFAULT_NAME: Final = "Hermes Assistant"
DEFAULT_PROMPT: Final = (
    "You are speaking through a Home Assistant voice device. Reply in the user's "
    "language using concise, natural speech. Avoid Markdown, tables, URLs, and emoji. "
    "Ask a short follow-up question only when more information is genuinely required."
)
DEFAULT_TIMEOUT: Final = 120
DEFAULT_MAX_RESPONSE_CHARS: Final = 1200
DEFAULT_MEMORY_SCOPE: Final = "conversation"
MEMORY_SCOPES: Final = ("conversation", "device", "user", "assistant")
