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

from app.config.logger import get_logger
from app.services.assistant_state import AssistantStateManager
from app.services.audio_listener import MicrophoneListener
from app.services.wake_word_validator import is_valid_wake_phrase, validation_confidence

load_dotenv()

log = get_logger(__name__)

_MIN_CONFIDENCE = 1.0
_DEBOUNCE_SECONDS = 4.0
_WAKE_STT_LANGUAGE = os.getenv("WAKE_STT_LANGUAGE", "tr-TR")
_WAKE_PAUSE_THRESHOLD = 0.9

GREETING_PHRASE = "Merhaba efendim"


class _PorcupineBackend:
    """Picovoice Porcupine tabanlı wake word algılayıcı."""

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
        if self._thread and self._thread.is_alive():
            return True
        try:
            import pvporcupine  # noqa: F401
            from pvrecorder import PvRecorder  # noqa: F401
        except ImportError:
            log.warning("pvporcupine/pvrecorder yuklu degil, STT moduna geciliyor.")
            return False
        if not Path(self._keyword_path).is_file():
            log.warning("Anahtar kelime dosyasi bulunamadi: %s", self._keyword_path)
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="PorcupineWake")
        self._thread.start()
        log.info("Porcupine wake word dinlemesi baslatildi.")
        return True

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None

    def _run_loop(self) -> None:
        porcupine = None
        recorder = None
        try:
            import pvporcupine
            from pvrecorder import PvRecorder
            porcupine = pvporcupine.create(access_key=self._access_key, keyword_paths=[self._keyword_path])
            recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
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
                        log.info("Porcupine: ozel wake word algilandi.")
                        self._on_detected()
        except Exception as exc:
            log.error("Porcupine hatasi: %s", exc)
        finally:
            try:
                if recorder is not None:
                    recorder.stop(); recorder.delete()
            except Exception as exc:
                log.warning("Recorder kapatma hatasi: %s", exc)
            try:
                if porcupine is not None:
                    porcupine.delete()
            except Exception as exc:
                log.warning("Porcupine kapatma hatasi: %s", exc)


class WakeWordEngine:
    """Arka planda mikrofonu dinleyerek yalnızca Hey Jarvis ifadesini yakalar."""

    def __init__(self, trigger_callback: Callable[[], None], state_manager: AssistantStateManager) -> None:
        self._callback = trigger_callback
        self._state = state_manager
        self._listener = MicrophoneListener(energy_threshold=350, pause_threshold=_WAKE_PAUSE_THRESHOLD, phrase_time_limit=3.0)
        self._accepted_aliases = _load_wake_aliases()
        self._enabled = True
        self._last_trigger = 0.0
        self._lock = threading.Lock()
        self._porcupine: Optional[_PorcupineBackend] = None
        self._using_porcupine = False
        self._init_porcupine_if_configured()

    def _init_porcupine_if_configured(self) -> None:
        access_key = os.getenv("PICOVOICE_ACCESS_KEY", "").strip()
        keyword_path = os.getenv("PORCUPINE_KEYWORD_PATH", "").strip()
        if not access_key or not keyword_path:
            return
        self._porcupine = _PorcupineBackend(
            access_key=access_key, keyword_path=keyword_path,
            on_detected=self._on_porcupine_detected,
            should_listen=self._state.can_listen_for_wake_word,
        )

    def _on_porcupine_detected(self) -> None:
        if not self._can_trigger():
            return
        with self._lock:
            self._last_trigger = time.monotonic()
        self._callback()

    def start(self) -> bool:
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
        if self._porcupine is not None:
            self._porcupine.stop()
        self._listener.stop_background(wait=False)

    def set_enabled(self, enabled: bool) -> None:
        """Mikrofon dinlemeyi aç/kapat."""
        self._enabled = enabled
        if enabled:
            self.start()
        else:
            self.stop()

    @property
    def is_active(self) -> bool:
        if self._using_porcupine and self._porcupine is not None:
            return True
        return self._listener.is_listening

    def _retry_start_later(self) -> bool:
        def _delayed_retry() -> None:
            time.sleep(1.5)
            if self._enabled and self._state.can_listen_for_wake_word():
                self.start()
        threading.Thread(target=_delayed_retry, daemon=True, name="WakeRetry").start()
        return False

    def _can_trigger(self) -> bool:
        if not self._enabled:
            return False
        if not self._state.can_listen_for_wake_word():
            return False
        if time.monotonic() - self._last_trigger < _DEBOUNCE_SECONDS:
            return False
        return True

    def _background_handler(self, recognizer: sr.Recognizer, audio: sr.AudioData) -> None:
        if not self._can_trigger():
            return
        try:
            text = recognizer.recognize_google(audio, language=_WAKE_STT_LANGUAGE)
            log.debug("STT: '%s'", text)
            if validation_confidence(text, self._accepted_aliases) < _MIN_CONFIDENCE:
                return
            if not is_valid_wake_phrase(text, self._accepted_aliases):
                return
            with self._lock:
                self._last_trigger = time.monotonic()
            log.info("Dogrulanmis wake word algilandi: '%s'", text)
            self._callback()
        except sr.UnknownValueError:
            pass
        except sr.RequestError as exc:
            log.warning("STT API hatasi: %s", exc)
        except Exception as exc:
            log.error("Tanima hatasi: %s", exc)


def _load_wake_aliases() -> frozenset[str]:
    raw_aliases = os.getenv("WAKE_WORD_ALIASES", "")
    aliases = frozenset(a.strip() for a in raw_aliases.split(",") if a.strip())
    if aliases:
        log.info("Ek eslesmeli ifadeler yuklendi: %s", sorted(aliases))
    return aliases
