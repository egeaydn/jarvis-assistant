"""
Deterministik ve yerel wake word doğrulama katmanı.

LLM/Groq çıktısına dayanmaz; yalnızca STT metnini sıkı kurallarla denetler.
Yanlış pozitifleri önlemek için fuzzy eşleşme kullanılmaz.
"""

from __future__ import annotations

import re
import unicodedata

# Kabul edilen tam ifadeler (normalize edilmiş hâl).
_ACCEPTED_EXACT: frozenset[str] = frozenset(
    {
        "hey jarvis",
        "heyjarvis",
    }
)

# Türkçe karakter → ASCII yakınlık haritası (yalnızca normalizasyon için).
_TURKISH_CHAR_MAP: dict[str, str] = {
    "ç": "c",
    "ğ": "g",
    "ı": "i",
    "ö": "o",
    "ş": "s",
    "ü": "u",
    "â": "a",
    "î": "i",
    "û": "u",
}


def normalize_wake_text(text: str) -> str:
    """
    Wake word karşılaştırması için metni normalize eder.

    Küçük harfe çevirir, noktalama temizler, Türkçe karakter toleransı
    uygular ve fazla boşlukları birleştirir.

    Args:
        text: Ham STT çıktısı.

    Returns:
        Normalize edilmiş metin.
    """
    if not text:
        return ""

    lowered = text.lower().strip()
    normalized = unicodedata.normalize("NFKD", lowered)

    for tr_char, ascii_char in _TURKISH_CHAR_MAP.items():
        normalized = normalized.replace(tr_char, ascii_char)

    # Noktalama ve özel karakterleri boşluğa çevir.
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # Birleşik yazım varyasyonu: "hey jarvis" → "heyjarvis" kontrolü için
    # boşluksuz hâli ayrıca değerlendirilir; burada boşluklu standart form döner.
    return normalized


def is_valid_wake_phrase(text: str) -> bool:
    """
    Metnin yalnızca geçerli bir "Hey Jarvis" ifadesi olup olmadığını denetler.

    Kabul edilenler:
        - ``hey jarvis`` (tam ifade, ek kelime yok)
        - ``heyjarvis`` (bitişik yazım)

    Reddedilenler:
        - ``jarvis``, ``hey``, ``hey jarvis gibi`` tek başına veya benzer kelimeler
        - Fuzzy/benzerlik eşleşmeleri

    Args:
        text: STT çıktısı.

    Returns:
        True yalnızca tam eşleşme varsa.
    """
    normalized = normalize_wake_text(text)
    if not normalized:
        return False

    # Boşluksuz varyasyon.
    compact = normalized.replace(" ", "")

    if normalized in _ACCEPTED_EXACT:
        return True
    if compact == "heyjarvis":
        return True

    return False


def validation_confidence(text: str) -> float:
    """
    Yerel güven skoru — yalnızca tam eşleşmede 1.0 döner.

    Args:
        text: STT çıktısı.

    Returns:
        1.0 geçerli ifade, aksi halde 0.0.
    """
    return 1.0 if is_valid_wake_phrase(text) else 0.0
