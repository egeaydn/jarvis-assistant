"""
Phase 7 — Ekran analizi tool'lari.

LLM tarafindan cagirilabilecek iki tool:
    analyze_screen(prompt)       -- ekrani gorerek analiz eder
    capture_screenshot(save_path) -- ekranin fotografini kaydeder
"""

from typing import Optional

from app.services.vision import ScreenCapture, VisionAnalyzer

# Lazy init -- ilk cagirida olusturulur, sonraki cagrilarda yeniden kullanilir
_capture: Optional[ScreenCapture] = None
_analyzer: Optional[VisionAnalyzer] = None


def _get_capture() -> ScreenCapture:
    global _capture
    if _capture is None:
        _capture = ScreenCapture()
    return _capture


def _get_analyzer() -> VisionAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = VisionAnalyzer()
    return _analyzer


# ── Tool fonksiyonlari ────────────────────────────────────────────────────────

def analyze_screen(prompt: str = "") -> str:
    """
    Ekranin anlik goruntusunu alir ve Gemini Vision ile analiz eder.

    prompt: Analize yonlendirici soru veya talimat (bos birakilabilir).
    Ornek: "hata mesaji var mi?", "hangi uygulama acik?", "ne goruyorsun?"
    """
    try:
        analyzer = _get_analyzer()
        result = analyzer.analyze_screen(prompt or None)
        return result
    except EnvironmentError as exc:
        return f"Vision servisi kullanilamiyor: {exc}"
    except Exception as exc:
        return f"Ekran analizi basarisiz: {exc}"


def capture_screenshot(save_path: str = "") -> str:
    """
    Ekranin anlik goruntusunu PNG dosyasi olarak kaydeder.

    save_path: Kayit yolu (bos birakilirsa Masaustu'ne zaman damgali kaydeder).
    Donen deger: Kaydedilen dosyanin tam yolu.
    """
    try:
        cap = _get_capture()
        path = cap.capture_to_file(save_path if save_path else None)
        return f"Screenshot kaydedildi: {path}"
    except Exception as exc:
        return f"Screenshot alinamadi: {exc}"
