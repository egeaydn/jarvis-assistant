"""Wake word doğrulayıcı birim testleri."""

from app.services.wake_word_validator import is_valid_wake_phrase, normalize_wake_text


def test_valid_phrases() -> None:
    assert is_valid_wake_phrase("Hey Jarvis")
    assert is_valid_wake_phrase("hey jarvis")
    assert is_valid_wake_phrase("heyjarvis")
    assert is_valid_wake_phrase("Hey, Jarvis!")
    assert is_valid_wake_phrase("  hey   jarvis  ")
    assert is_valid_wake_phrase("Merhaba")
    assert is_valid_wake_phrase("Merhaba Ege")
    assert is_valid_wake_phrase("merhabaege")


def test_invalid_phrases() -> None:
    assert not is_valid_wake_phrase("jarvis")
    assert not is_valid_wake_phrase("hey")
    assert not is_valid_wake_phrase("hey jarvis gibi")
    assert not is_valid_wake_phrase("travis")
    assert not is_valid_wake_phrase("servis")
    assert not is_valid_wake_phrase("hey servis")
    assert not is_valid_wake_phrase("garvis")
    assert not is_valid_wake_phrase("hey jarvis open chrome")


def test_configured_aliases_require_an_exact_match() -> None:
    """Yapılandırılan alternatiflerin yalnızca tam hâlinin kabul edildiğini doğrular."""
    aliases = {"hey yarvis", "hair dryers"}

    assert is_valid_wake_phrase("Hey Yarvis", aliases)
    assert is_valid_wake_phrase("hair dryers", aliases)
    assert not is_valid_wake_phrase("hair dryer", aliases)
    assert not is_valid_wake_phrase("hey", aliases)


def test_normalize() -> None:
    assert normalize_wake_text("Hey, Jarvis!") == "hey jarvis"
    assert normalize_wake_text("HEYJARVIS") == "heyjarvis"
