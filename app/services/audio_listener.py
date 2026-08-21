"""
Paylaşılan mikrofon dinleme yardımcıları.

Wake word ve komut dinleme modülleri tarafından kullanılır.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

import speech_recognition as sr


class MicrophoneListener:
    """
    ``speech_recognition`` tabanlı mikrofon erişim sarmalayıcısı.

    Ortam kalibrasyonu, arka plan dinleme ve hata toleransı sağlar.
    """

    def __init__(
        self,
        energy_threshold: int = 300,
        pause_threshold: float = 0.6,
        phrase_time_limit: float = 3.0,
    ) -> None:
        self._recognizer = sr.Recognizer()
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.energy_threshold = energy_threshold
        self._recognizer.pause_threshold = pause_threshold
        self._recognizer.non_speaking_duration = 0.3
        self._phrase_time_limit = phrase_time_limit

        self._microphone: Optional[sr.Microphone] = None
        self._stop_fn: Optional[Callable[[bool], None]] = None

    @property
    def recognizer(self) -> sr.Recognizer:
        """Dahili speech recognizer."""
        return self._recognizer

    def calibrate(self, duration: float = 0.5) -> bool:
        """
        Ortam gürültüsüne göre mikrofonu kalibre eder.

        Args:
            duration: Kalibrasyon süresi (saniye).

        Returns:
            True başarılı, False mikrofon erişilemedi.
        """
        try:
            self._microphone = sr.Microphone()
            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=duration)
            return True
        except OSError as exc:
            print(f"[AUDIO WN] Mikrofon kalibrasyonu basarisiz: {exc}")
            return False
        except Exception as exc:
            print(f"[AUDIO ERR] Kalibrasyon hatasi: {exc}")
            return False

    def start_background(
        self,
        handler: Callable[[sr.Recognizer, sr.AudioData], None],
    ) -> bool:
        """
        Arka planda sürekli dinlemeyi başlatır.

        Args:
            handler: Her ses parçası için çağrılacak geri bildirim.

        Returns:
            True dinleme başladı, False başlatılamadı.
        """
        if self._stop_fn is not None:
            return True

        max_retries = 5
        for attempt in range(max_retries):
            try:
                if self._microphone is None:
                    self._microphone = sr.Microphone()

                with self._microphone as source:
                    self._recognizer.adjust_for_ambient_noise(source, duration=0.4)

                self._stop_fn = self._recognizer.listen_in_background(
                    self._microphone,
                    handler,
                    phrase_time_limit=self._phrase_time_limit,
                )
                print("[AUDIO INF] Arka plan dinlemesi baslatildi.")
                return True
            except OSError as exc:
                if attempt >= max_retries - 1:
                    print(f"[AUDIO WN] Mikrofon erisilemedi: {exc}")
                    return False
                time.sleep(0.3)
            except Exception as exc:
                print(f"[AUDIO ERR] Dinleme baslatilamadi: {exc}")
                return False

        return False

    def stop_background(self, wait: bool = False) -> None:
        """Arka plan dinlemeyi durdurur."""
        if self._stop_fn is not None:
            try:
                self._stop_fn(wait_for_stop=wait)
            except Exception as exc:
                print(f"[AUDIO WN] Dinleme durdurulurken hata: {exc}")
            finally:
                self._stop_fn = None
                print("[AUDIO INF] Arka plan dinlemesi durduruldu.")

    @property
    def is_listening(self) -> bool:
        """Arka plan dinleme aktif mi."""
        return self._stop_fn is not None
