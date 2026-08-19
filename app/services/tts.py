"""
Phase 6 — Text-to-Speech servisi.

pyttsx3 ile Windows SAPI5 üzerinden sesli konuşma.
Tamamen offline çalışır, internet gerektirmez.

Kullanım:
    tts = TextToSpeech()
    tts.speak("Chrome açılıyor.")
"""

import pyttsx3


class TextToSpeech:
    """
    Windows SAPI5 üzerinden metni sesli okur (offline).

    Parametreler:
        rate   : Konuşma hızı, kelime/dakika (default: 175)
        volume : Ses seviyesi 0.0–1.0 (default: 1.0)
    """

    def __init__(self, rate: int = 175, volume: float = 1.0) -> None:
        self._engine = pyttsx3.init()
        self.set_rate(rate)
        self.set_volume(volume)
        self._try_set_turkish_voice()

    # ── Konuşma ───────────────────────────────────────────────────────────────

    def speak(self, text: str) -> None:
        """
        Metni sesli okur (bloklayan çağrı — bitmeden devam etmez).
        """
        if not text or not text.strip():
            return
        try:
            self._engine.say(text)
            self._engine.runAndWait()
        except RuntimeError:
            # Bazı durumlarda engine'i yeniden başlatmak gerekebilir
            self._engine = pyttsx3.init()
            self._engine.say(text)
            self._engine.runAndWait()

    # ── Ayarlar ───────────────────────────────────────────────────────────────

    def set_rate(self, wpm: int) -> None:
        """Konuşma hızını ayarlar (kelime/dakika)."""
        self._engine.setProperty("rate", wpm)

    def set_volume(self, level: float) -> None:
        """Ses seviyesini ayarlar (0.0 – 1.0)."""
        self._engine.setProperty("volume", max(0.0, min(1.0, level)))

    def list_voices(self) -> list[str]:
        """Sistemde kurulu seslerin isimlerini döndürür."""
        voices = self._engine.getProperty("voices")
        return [v.name for v in voices] if voices else []

    # ── İç yardımcılar ────────────────────────────────────────────────────────

    def _try_set_turkish_voice(self) -> None:
        """
        Sistemde Türkçe ses varsa onu seçer.
        Yoksa varsayılan sesi kullanır (hata vermez).
        """
        voices = self._engine.getProperty("voices")
        if not voices:
            return

        # "tr" veya "Turkish" içeren ses ara
        for voice in voices:
            name_lower = voice.name.lower()
            lang_ids = getattr(voice, "languages", [])
            lang_str = " ".join(str(l) for l in lang_ids).lower()

            if "tr" in lang_str or "turkish" in name_lower or "türkçe" in name_lower:
                self._engine.setProperty("voice", voice.id)
                return

        # Türkçe ses bulunamadı — varsayılan kullanılır, sorun yok
