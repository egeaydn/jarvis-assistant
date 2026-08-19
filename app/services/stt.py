"""
Phase 6 — Speech-to-Text servisi.

Google Speech API üzerinden mikrofon sesini Türkçe metne çevirir.
İnternet bağlantısı gerektirir (API key gerekmez, ücretsiz).

Kullanım:
    stt = SpeechToText()
    stt.calibrate()           # İlk başta bir kere çağır
    text = stt.listen_once()  # Konuşmayı al
    if text:
        print(text)
"""

import speech_recognition as sr


class SpeechToText:
    """
    Mikrofonu dinler ve Google Speech API ile metne çevirir.

    Parametreler:
        language        : Tanıma dili (default: "tr-TR")
        timeout         : Konuşma başlamazsa kaç saniye bekle (default: 5)
        phrase_time_limit: Konuşma başladıktan sonra max kaç saniye al (default: 10)
        energy_threshold: Mikrofon hassasiyeti (default: dynamic)
    """

    def __init__(
        self,
        language: str = "tr-TR",
        timeout: int = 5,
        phrase_time_limit: int = 10,
    ) -> None:
        self._language = language
        self._timeout = timeout
        self._phrase_limit = phrase_time_limit
        self._recognizer = sr.Recognizer()
        # Dinamik enerji eşiği — ortama göre otomatik ayarlanır
        self._recognizer.dynamic_energy_threshold = True

    def calibrate(self, duration: float = 1.0) -> None:
        """
        Ortam gürültüsüne göre mikrofonu kalibre eder.
        Program başında bir kere çağrılmalı.
        """
        try:
            with sr.Microphone() as source:
                print("  🔇 Ortam gürültüsü ölçülüyor, lütfen bekleyin...")
                self._recognizer.adjust_for_ambient_noise(source, duration=duration)
                print(f"  ✅ Kalibrasyon tamamlandı. (eşik: {self._recognizer.energy_threshold:.0f})")
        except OSError as exc:
            raise RuntimeError(
                f"Mikrofon bulunamadı veya erişim reddedildi: {exc}"
            ) from exc

    def listen_once(self) -> str | None:
        """
        Mikrofonu açar, bir cümle dinler ve metne çevirir.

        Dönüş:
            str  — tanınan metin
            None — anlaşılamadı veya timeout
        """
        import time
        max_retries = 5
        audio = None
        
        for attempt in range(max_retries):
            try:
                with sr.Microphone() as source:
                    audio = self._recognizer.listen(
                        source,
                        timeout=self._timeout,
                        phrase_time_limit=self._phrase_limit,
                    )
                break
            except OSError as exc:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Mikrofon meşgul veya erişilemiyor: {exc}") from exc
                time.sleep(0.2)  # Arka plan motorunun mikrofonu serbest bırakmasını bekle
            except sr.WaitTimeoutError:
                return None  # Konuşma başlamadı


        try:
            text = self._recognizer.recognize_google(
                audio,
                language=self._language,
            )
            return text.strip()
        except sr.UnknownValueError:
            return None  # Ses anlaşılamadı
        except sr.RequestError as exc:
            raise RuntimeError(
                f"Google Speech API'ye ulaşılamadı: {exc}\n"
                "İnternet bağlantınızı kontrol edin."
            ) from exc

    @property
    def language(self) -> str:
        return self._language
