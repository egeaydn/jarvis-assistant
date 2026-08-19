"""
Phase 7 — Screen Vision servisi.

ScreenCapture  : mss ile hizli ekran yakalama.
VisionAnalyzer : Gemini 2.0 Flash ile goruntu analizi.

Kullanim:
    cap  = ScreenCapture()
    analyzer = VisionAnalyzer()

    # Tek satirda ekrani analiz et
    result = analyzer.analyze_screen("Ekranda ne var?")
    print(result)
"""

import os
import io
from datetime import datetime
from pathlib import Path
from typing import Optional

import mss
import mss.tools
from dotenv import load_dotenv
from PIL import Image

load_dotenv()



# ── ScreenCapture ─────────────────────────────────────────────────────────────

class ScreenCapture:
    """
    mss kullanarak hizli ekran yakalama.

    mss, PyAutoGUI'den yaklasik 3x daha hizlidir ve
    ek bagimliliklardan bagimsiz calisir.
    """

    def capture(self, monitor: int = 1) -> bytes:
        """
        Ekranin PNG bytes ciktisini dondurur.

        monitor: 1 = birinci ekran, 0 = tum ekranlar birlesik
        """
        with mss.mss() as sct:
            mon = sct.monitors[monitor]
            screenshot = sct.grab(mon)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            return buf.getvalue()

    def capture_to_file(
        self,
        save_path: Optional[str] = None,
        monitor: int = 1,
    ) -> str:
        """
        Ekran goruntusunu dosyaya kaydeder ve tam yolu dondurur.
        save_path verilmezse Masaustu'ne zaman damgali isimle kaydeder.
        """
        if save_path:
            path = Path(save_path)
        else:
            desktop = Path.home() / "Desktop"
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = desktop / f"screenshot_{ts}.png"

        path.parent.mkdir(parents=True, exist_ok=True)

        png_bytes = self.capture(monitor=monitor)
        path.write_bytes(png_bytes)
        return str(path)

    def capture_region(
        self,
        x: int, y: int,
        width: int, height: int,
    ) -> bytes:
        """
        Ekranin belirli bir bolgesini PNG bytes olarak dondurur.
        """
        with mss.mss() as sct:
            region = {"left": x, "top": y, "width": width, "height": height}
            screenshot = sct.grab(region)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            return buf.getvalue()


# ── Varsayilan promptlar ───────────────────────────────────────────────────────

_PROMPT_GENEL = (
    "Bu ekran goruntusunde ne var? "
    "Hangi uygulamalar acik, ne yapiliyor? "
    "Kisa ve net Turkce acikla."
)

_PROMPT_HATA = (
    "Bu ekranda hata mesaji, uyari, exception veya sorun var mi? "
    "Varsa aynen yaz ve ne anlama geldigini Turkce acikla. "
    "Yoksa 'Hata gorunmuyor.' de."
)

_PROMPT_UI = (
    "Ekranda hangi uygulama veya web sayfasi acik? "
    "Kullanici ne yapabilir? Kisa ozet ver."
)


# ── VisionAnalyzer ────────────────────────────────────────────────────────────

class VisionAnalyzer:
    """
    Gemini 2.0 Flash kullanarak goruntu analizi yapar.

    Groq goruntu desteklemiyor, bu yuzden provider ne olursa olsun
    vision islemi her zaman Gemini uzerinden gider.
    """

    def __init__(self) -> None:
        from google import genai
        from google.genai import types as gt
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY bulunamadi. .env dosyasini kontrol edin."
            )
        self._client = genai.Client(api_key=api_key)
        self._model = "gemini-3.6-flash"
        self._capture = ScreenCapture()

    def analyze(self, image_bytes: bytes, prompt: str) -> str:
        """
        Verilen goruntu bytes ve prompt ile Gemini'den analiz ister.
        """
        from google.genai import types as gt

        image_part = gt.Part.from_bytes(data=image_bytes, mime_type="image/png")
        text_part  = gt.Part.from_text(text=prompt)

        response = self._client.models.generate_content(
            model=self._model,
            contents=[image_part, text_part],
        )
        return response.text.strip() if response.text else "(Yanit alinamadi)"

    def analyze_screen(self, prompt: Optional[str] = None, monitor: int = 1) -> str:
        """
        Ekranin screenshot'ini alir ve Gemini ile analiz eder.

        prompt verilmezse genel analiz yapilir.
        """
        if not prompt:
            prompt = _PROMPT_GENEL
        elif "hata" in prompt.lower() or "error" in prompt.lower():
            prompt = _PROMPT_HATA + f"\n\nEk talimat: {prompt}"
        elif "ui" in prompt.lower() or "sayfa" in prompt.lower():
            prompt = _PROMPT_UI + f"\n\nEk talimat: {prompt}"
        else:
            prompt = f"Bu ekran goruntusunu incele. {prompt} Turkce yanit ver."

        image_bytes = self._capture.capture(monitor=monitor)
        return self.analyze(image_bytes, prompt)
