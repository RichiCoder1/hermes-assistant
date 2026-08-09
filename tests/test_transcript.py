"""Tests for transcript and TTS helpers."""

from types import SimpleNamespace

from custom_components.hermes_assistant.transcript import (
    memory_session_key,
    messages_from_chat_log,
    session_id_value,
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


def test_session_id_is_conversation_scoped_and_opaque() -> None:
    value = session_id_value("entry", "conversation-secret")
    assert value == session_id_value("entry", "conversation-secret")
    assert value != session_id_value("entry", "another-conversation")
    assert "conversation-secret" not in value


def test_conversation_memory_key_is_independent_from_session_id() -> None:
    key = memory_session_key(
        "entry", "conversation-secret", "conversation", device_id=None, user_id=None
    )
    assert key != session_id_value("entry", "conversation-secret")


def test_device_memory_scope_is_stable_across_conversations() -> None:
    first = memory_session_key(
        "entry", "conversation-a", "device", device_id="kitchen", user_id=None
    )
    second = memory_session_key(
        "entry", "conversation-b", "device", device_id="kitchen", user_id=None
    )
    assert first == second
    assert "kitchen" not in first


def test_user_memory_scope_is_stable_across_devices() -> None:
    first = memory_session_key(
        "entry", "conversation-a", "user", device_id="kitchen", user_id="person"
    )
    second = memory_session_key(
        "entry", "conversation-b", "user", device_id="office", user_id="person"
    )
    assert first == second
    assert "person" not in first


def test_assistant_memory_scope_is_stable_across_conversations_and_devices() -> None:
    first = memory_session_key(
        "entry", "conversation-a", "assistant", device_id="kitchen", user_id="one"
    )
    second = memory_session_key(
        "entry", "conversation-b", "assistant", device_id="office", user_id="two"
    )
    assert first == second
    assert first != memory_session_key(
        "another-entry",
        "conversation-b",
        "assistant",
        device_id="office",
        user_id="two",
    )


def test_user_memory_scope_falls_back_to_conversation() -> None:
    first = memory_session_key(
        "entry", "conversation-a", "user", device_id="kitchen", user_id=None
    )
    second = memory_session_key(
        "entry", "conversation-b", "user", device_id="kitchen", user_id=None
    )
    assert first != second
