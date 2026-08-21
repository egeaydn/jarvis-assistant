"""
Phase v2.0 — Güvenilir Wake Word (Hey Jarvis) Servisi.

Özellikler:
- Deterministik yerel doğrulama (LLM/Groq kullanılmaz)
- State machine ile entegrasyon — yalnızca IDLE_WAKE_LISTENING'de dinler
- Debounce/cooldown ile çift tetiklemeyi engeller
- İsteğe bağlı Porcupine motoru (özel .ppn anahtar kelimesi gerekir)
- Mikrofon hatalarında otomatik yeniden deneme
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import speech_recognition as sr
from dotenv import load_dotenv

from app.services.assistant_state import AssistantState, AssistantStateManager
from app.services.audio_listener import MicrophoneListener
from app.services.wake_word_validator import is_valid_wake_phrase, validation_confidence

load_dotenv()

# Minimum güven eşiği — yalnızca tam eşleşme kabul edilir (0.0 veya 1.0).
_MIN_CONFIDENCE = 1.0

# Aynı ses parçasında / kısa sürede tekrar tetiklemeyi engelle (saniye).
_DEBOUNCE_SECONDS = 4.0

# STT dili — "Hey Jarvis" İngilizce ifadesi için en-US.
_WAKE_STT_LANGUAGE = "en-US"

GREETING_PHRASE = "Merhaba efendim"


class _PorcupineBackend:
    """
    Picovoice Porcupine tabanlı wake word algılayıcı.

    Yalnızca özel ``.ppn`` dosyası ile etkinleştirilir; yerleşik ``jarvis``
    anahtar kelimesi tek başına tetikleme yapmaz (yanlış pozitif riski).
    """

    def __init__(
        self,
        access_key: str,
        keyword_path: str,
        on_detected: Callable[[], None],
        should_listen: Callable[[], bool],
    ) -> None:
        self._access_key = access_key
        self._keyword_path = keyword_path
        self._on_detected = on_detected
        self._should_listen = should_listen
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_trigger = 0.0

    def start(self) -> bool:
        """Porcupine dinleme thread'ini başlatır."""
        if self._thread and self._thread.is_alive():
            return True

        try:
            import pvporcupine  # noqa: F401
            from pvrecorder import PvRecorder  # noqa: F401
        except ImportError:
            print("[PORCUPINE WN] pvporcupine/pvrecorder yüklü değil, STT moduna geçiliyor.")
            return False

        if not Path(self._keyword_path).is_file():
            print(f"[PORCUPINE WN] Anahtar kelime dosyası bulunamadı: {self._keyword_path}")
            return False

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="PorcupineWake")
        self._thread.start()
        print("[PORCUPINE INF] Porcupine wake word dinlemesi başlatıldı.")
        return True

    def stop(self) -> None:
        """Porcupine thread'ini durdurur."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None

    def _run_loop(self) -> None:
        """Porcupine ana dinleme döngüsü."""
        porcupine = None
        recorder = None
        try:
            import pvporcupine
            from pvrecorder import PvRecorder

            porcupine = pvporcupine.create(
                access_key=self._access_key,
                keyword_paths=[self._keyword_path],
            )
            recorder = PvRecorder(
                device_index=-1,
                frame_length=porcupine.frame_length,
            )
            recorder.start()

            while not self._stop_event.is_set():
                if not self._should_listen():
                    time.sleep(0.05)
                    continue

                pcm = recorder.read()
                result = porcupine.process(pcm)
                if result >= 0:
                    now = time.monotonic()
                    if now - self._last_trigger >= _DEBOUNCE_SECONDS:
                        self._last_trigger = now
                        print("[PORCUPINE DETECTED] Özel wake word algılandı.")
                        self._on_detected()

        except Exception as exc:
            print(f"[PORCUPINE ERR] Porcupine hatası: {exc}")
        finally:
            try:
                if recorder is not None:
                    recorder.stop()
                    recorder.delete()
            except Exception as exc:
                print(f"[PORCUPINE WN] Recorder kapatma hatası: {exc}")
            try:
                if porcupine is not None:
                    porcupine.delete()
            except Exception as exc:
                print(f"[PORCUPINE WN] Porcupine kapatma hatası: {exc}")


class WakeWordEngine:
    """
    Arka planda mikrofonu dinleyerek yalnızca ``Hey Jarvis`` ifadesini yakalar.

    STT (Google) yalnızca ham metin üretir; tetikleme kararı yerel
    ``wake_word_validator`` katmanında verilir.
    """

    def __init__(
        self,
        trigger_callback: Callable[[], None],
        state_manager: AssistantStateManager,
    ) -> None:
        self._callback = trigger_callback
        self._state = state_manager
        self._listener = MicrophoneListener(
            energy_threshold=350,
            pause_threshold=0.55,
            phrase_time_limit=3.0,
        )
        self._enabled = True
        self._last_trigger = 0.0
        self._lock = threading.Lock()
        self._porcupine: Optional[_PorcupineBackend] = None
        self._using_porcupine = False

        self._init_porcupine_if_configured()

    def _init_porcupine_if_configured(self) -> None:
        """Ortam değişkenleri varsa Porcupine backend'ini hazırlar."""
        access_key = os.getenv("PICOVOICE_ACCESS_KEY", "").strip()
        keyword_path = os.getenv("PORCUPINE_KEYWORD_PATH", "").strip()

        if not access_key or not keyword_path:
            return

        self._porcupine = _PorcupineBackend(
            access_key=access_key,
            keyword_path=keyword_path,
            on_detected=self._on_porcupine_detected,
            should_listen=self._state.can_listen_for_wake_word,
        )

    def _on_porcupine_detected(self) -> None:
        """Porcupine algıladığında debounce ve state kontrolü uygular."""
        if not self._can_trigger():
            return
        with self._lock:
            self._last_trigger = time.monotonic()
        self._callback()

    def start(self) -> bool:
        """
        Wake word dinlemesini başlatır.

        Porcupine yapılandırılmışsa onu, aksi halde STT tabanlı dinlemeyi kullanır.

        Returns:
            True dinleme başladı veya zaten aktif.
        """
        if not self._enabled:
            return False

        if not self._state.can_listen_for_wake_word():
            return False

        if self._porcupine is not None:
            if self._porcupine.start():
                self._using_porcupine = True
                return True

        self._using_porcupine = False
        if not self._listener.calibrate(duration=0.4):
            return self._retry_start_later()

        if self._listener.start_background(self._background_handler):
            return True

        return self._retry_start_later()

    def stop(self) -> None:
        """Wake word dinlemesini durdurur."""
        if self._porcupine is not None:
            self._porcupine.stop()
        self._listener.stop_background(wait=False)

    def set_enabled(self, enabled: bool) -> None:
        """
        Mikrofon dinlemeyi aç/kapat (tray menüsü).

        Args:
            enabled: True dinlemeyi aç, False kapat.
        """
        self._enabled = enabled
        if enabled:
            self.start()
        else:
            self.stop()

    @property
    def is_active(self) -> bool:
        """Dinleme aktif mi."""
        if self._using_porcupine and self._porcupine is not None:
            return True
        return self._listener.is_listening

    def _retry_start_later(self) -> bool:
        """Mikrofon meşgul/hatalıysa kısa süre sonra yeniden dener."""
        def _delayed_retry() -> None:
            time.sleep(1.5)
            if self._enabled and self._state.can_listen_for_wake_word():
                self.start()

        threading.Thread(target=_delayed_retry, daemon=True, name="WakeRetry").start()
        return False

    def _can_trigger(self) -> bool:
        """Debounce, state ve mikrofon durumunu kontrol eder."""
        if not self._enabled:
            return False
        if not self._state.can_listen_for_wake_word():
            return False

        now = time.monotonic()
        if now - self._last_trigger < _DEBOUNCE_SECONDS:
            return False

        return True

    def _background_handler(
        self,
        recognizer: sr.Recognizer,
        audio: sr.AudioData,
    ) -> None:
        """
        Her ses parçası için arka plan thread'inde çalışır.

        STT metni yerel doğrulayıcıdan geçer; LLM kullanılmaz.
        """
        if not self._can_trigger():
            return

        try:
            text = recognizer.recognize_google(
                audio,
                language=_WAKE_STT_LANGUAGE,
            )
            print(f"[WAKE WORD DBG] STT: '{text}'")

            confidence = validation_confidence(text)
            if confidence < _MIN_CONFIDENCE:
                return

            if not is_valid_wake_phrase(text):
                return

            with self._lock:
                self._last_trigger = time.monotonic()

            print(f"[WAKE WORD DETECTED] Doğrulanmış wake word: '{text}'")
            self._callback()

        except sr.UnknownValueError:
            pass
        except sr.RequestError as exc:
            print(f"[WAKE WORD WN] STT API hatası: {exc}")
        except Exception as exc:
            print(f"[WAKE WORD ERR] Tanıma hatası: {exc}")
