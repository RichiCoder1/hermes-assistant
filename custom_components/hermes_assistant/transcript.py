"""Pure transcript and spoken-response helpers."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from typing import Protocol


class ChatContent(Protocol):
    """The public fields consumed from Home Assistant chat content."""

    @property
    def role(self) -> str:
        """Message role."""


_EMOJI_RE = re.compile(
    "[\U0001f000-\U0001faff\U00002600-\U000027bf\U0000fe0f\U0000200d]+"
)
_MARKDOWN_RE = re.compile(r"(?:```.*?```|`([^`]*)`|[*_#>]+)", re.DOTALL)
_SPACE_RE = re.compile(r"\s+")


def messages_from_chat_log(content: Iterable[ChatContent]) -> list[dict[str, str]]:
    """Convert Home Assistant chat content to OpenAI-compatible messages."""
    messages: list[dict[str, str]] = []
    for item in content:
        if item.role not in {"system", "user", "assistant"}:
            continue
        text = getattr(item, "content", None)
        if not isinstance(text, str) or not text.strip():
            continue
        messages.append({"role": item.role, "content": text.strip()})
    return messages


def spoken_text(value: str, max_chars: int) -> str:
    """Make a text response predictable for TTS and cap its length."""
    cleaned = _MARKDOWN_RE.sub(lambda match: match.group(1) or " ", value)
    cleaned = _EMOJI_RE.sub(" ", cleaned)
    cleaned = _SPACE_RE.sub(" ", cleaned).strip()
    if len(cleaned) <= max_chars:
        return cleaned

    candidate = cleaned[: max_chars + 1]
    boundary = max(candidate.rfind(". "), candidate.rfind("! "), candidate.rfind("? "))
    if boundary >= max_chars // 3:
        return candidate[: boundary + 1].strip()
    return cleaned[: max_chars - 1].rstrip() + "…"


def session_id_value(entry_id: str, conversation_id: str) -> str:
    """Create an opaque transcript session ID for one HA conversation."""
    return _opaque_session_value(entry_id, "session", conversation_id)


def memory_session_key(
    entry_id: str,
    conversation_id: str,
    scope: str,
    *,
    device_id: str | None,
    user_id: str | None,
) -> str:
    """Create an opaque long-term memory key at the configured scope."""
    source = conversation_id
    if scope == "device" and device_id:
        source = device_id
    elif scope == "user" and user_id:
        source = user_id
    elif scope == "assistant":
        source = "assistant"
    else:
        scope = "conversation"
    return _opaque_session_value(entry_id, f"memory:{scope}", source)


def _opaque_session_value(entry_id: str, namespace: str, source: str) -> str:
    """Hash an HA identifier into a bounded Hermes-safe namespace."""
    digest = hashlib.sha256(f"{entry_id}:{namespace}:{source}".encode()).hexdigest()[
        :32
    ]
    return f"ha:{namespace}:{digest}"
