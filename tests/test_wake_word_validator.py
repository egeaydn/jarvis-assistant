"""Wake word doğrulayıcı birim testleri."""

from app.services.wake_word_validator import is_valid_wake_phrase, normalize_wake_text


def test_valid_phrases() -> None:
    assert is_valid_wake_phrase("Hey Jarvis")
    assert is_valid_wake_phrase("hey jarvis")
    assert is_valid_wake_phrase("heyjarvis")
    assert is_valid_wake_phrase("Hey, Jarvis!")
    assert is_valid_wake_phrase("  hey   jarvis  ")


def test_invalid_phrases() -> None:
    assert not is_valid_wake_phrase("jarvis")
    assert not is_valid_wake_phrase("hey")
    assert not is_valid_wake_phrase("hey jarvis gibi")
    assert not is_valid_wake_phrase("travis")
    assert not is_valid_wake_phrase("servis")
    assert not is_valid_wake_phrase("hey servis")
    assert not is_valid_wake_phrase("garvis")
    assert not is_valid_wake_phrase("hey jarvis open chrome")


def test_normalize() -> None:
    assert normalize_wake_text("Hey, Jarvis!") == "hey jarvis"
    assert normalize_wake_text("HEYJARVIS") == "heyjarvis"
