"""Tests for transcript and TTS helpers."""

from types import SimpleNamespace

from custom_components.hermes_assistant.transcript import (
    messages_from_chat_log,
    scoped_session_value,
    spoken_text,
)


def test_messages_include_supported_roles() -> None:
    content = [
        SimpleNamespace(role="system", content=" Speak briefly "),
        SimpleNamespace(role="user", content="Hello"),
        SimpleNamespace(role="tool_result", content="private tool output"),
        SimpleNamespace(role="assistant", content="Hi there"),
        SimpleNamespace(role="assistant", content=None),
    ]
    assert messages_from_chat_log(content) == [
        {"role": "system", "content": "Speak briefly"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]


def test_spoken_text_removes_voice_noise_without_removing_non_latin_text() -> None:
    assert spoken_text("**你好** 👋  `朋友`", 100) == "你好 朋友"


def test_spoken_text_truncates_at_sentence_boundary() -> None:
    text = "First sentence. Second sentence is much too long for the configured limit."
    assert spoken_text(text, 30) == "First sentence."


def test_spoken_text_hard_truncates_when_no_boundary() -> None:
    assert spoken_text("abcdefghijk", 8) == "abcdefg…"


def test_session_scope_is_stable_and_opaque() -> None:
    value = scoped_session_value(
        "entry", "conversation-secret", "conversation", device_id=None, user_id=None
    )
    assert value == scoped_session_value(
        "entry", "conversation-secret", "conversation", device_id=None, user_id=None
    )
    assert "conversation-secret" not in value


def test_device_scope_uses_device_when_available() -> None:
    first = scoped_session_value(
        "entry", "conversation-a", "device", device_id="kitchen", user_id=None
    )
    second = scoped_session_value(
        "entry", "conversation-b", "device", device_id="kitchen", user_id=None
    )
    assert first == second


def test_user_scope_falls_back_to_conversation() -> None:
    first = scoped_session_value(
        "entry", "conversation-a", "user", device_id="kitchen", user_id=None
    )
    second = scoped_session_value(
        "entry", "conversation-b", "user", device_id="kitchen", user_id=None
    )
    assert first != second
