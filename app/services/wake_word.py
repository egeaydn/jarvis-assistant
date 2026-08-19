"""
Phase v1.0 — Wake Word (Hey Jarvis) Arka Plan Dinleme Servisi.

SpeechRecognition listen_in_background API'sini kullanarak
arka planda sürekli "Jarvis" tetikleme kelimesini arar.
İngilizce ve Türkçe paralel tanıma ve düşük gecikmeli parametreler ile optimize edilmiştir.
"""

import speech_recognition as sr
from typing import Callable, Optional


class WakeWordEngine:
    """
    Arka planda mikrofonu dinleyerek 'Jarvis' anahtar kelimesini yakalar.
    """

    def __init__(self, trigger_callback: Callable[[], None]) -> None:
        self._callback = trigger_callback
        self._recognizer = sr.Recognizer()
        
        # ── Düşük Gecikmeli Ses Algılama Ayarları ──────────────────────────────
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.pause_threshold = 0.35          # Cümle sonunu hızlı algıla (default: 0.8)
        self._recognizer.non_speaking_duration = 0.15     # Kırpma payını azalt (default: 0.5)
        
        self._microphone: Optional[sr.Microphone] = None
        self._stop_fn: Optional[Callable[[bool], None]] = None

    def start(self) -> bool:
        """Dinleme motorunu arka plan thread'inde başlatır."""
        if self._stop_fn:
            return True  # Zaten çalışıyor

        import time
        max_retries = 5
        
        for attempt in range(max_retries):
            try:
                self._microphone = sr.Microphone()
                with self._microphone as source:
                    self._recognizer.adjust_for_ambient_noise(source, duration=0.4)
                
                # Arka plan dinleme thread'ini başlat
                self._stop_fn = self._recognizer.listen_in_background(
                    self._microphone,
                    self._background_handler,
                    phrase_time_limit=3
                )
                return True
            except OSError as exc:
                if attempt == max_retries - 1:
                    print(f"[WAKE WORD WN] Dinleme başlatılamadı (mikrofon meşgul): {exc}")
                    return False
                time.sleep(0.2)
            except Exception as exc:
                print(f"[WAKE WORD WN] Hata oluştu: {exc}")
                return False


    def stop(self) -> None:
        """Dinleme motorunu kapatır."""
        if self._stop_fn:
            self._stop_fn(wait_for_stop=False)
            self._stop_fn = None
            print("[WAKE WORD INF] Dinleme durduruldu.")

    def _background_handler(self, recognizer: sr.Recognizer, audio: sr.AudioData) -> None:
        """Her ses algılandığında arka plan thread'inde çalışır."""
        # 1. Aşama: İngilizce Model ile Tanıma (Jarvis kelimesine en duyarlı mod)
        try:
            text_en = recognizer.recognize_google(audio, language="en-US").lower()
            print(f"[WAKE WORD DBG] Heard (en): '{text_en}'")
            if any(k in text_en for k in ("jarvis", "travis", "travis", "charvis", "jarves", "jarve")):
                print(f"[WAKE WORD DETECTED] Tetikleme algılandı (en): '{text_en}'")
                self._callback()
                return
        except Exception:
            pass

        # 2. Aşama: Türkçe Model ile Tanıma (Phonetic Fallback)
        try:
            text_tr = recognizer.recognize_google(audio, language="tr-TR").lower()
            print(f"[WAKE WORD DBG] Heard (tr): '{text_tr}'")
            # Türkçe fonetik hatalara göre ("servis", "cervis" vb.) yakalama
            if any(k in text_tr for k in ("jarvis", "servis", "varis", "yaris", "cervis", "carvis", "yarvis")):
                print(f"[WAKE WORD DETECTED] Tetikleme algılandı (tr): '{text_tr}'")
                self._callback()
                return
        except Exception:
            pass
