"""PDF ve Döküman okuma/özetleme araçları."""

import os
from pathlib import Path
from app.config.logger import get_logger

log = get_logger(__name__)


def read_and_summarize_pdf(filepath: str, custom_prompt: str = None) -> str:
    """
    Diskteki bir PDF dosyasının içeriğini okur. 
    Eğer metin 4000 karakterden uzunsa, Gemini kullanarak otomatik özetler.
    Kısa ise metnin tamamını döndürür.
    
    Args:
        filepath: Okunacak PDF dosyasının mutlak yolu
        custom_prompt: Özetleme için LLM'e verilecek özel yönerge (opsiyonel)
    """
    path = Path(filepath)
    if not path.is_absolute():
        path = Path.home() / filepath

    if not path.exists() or not path.is_file():
        return f"Hata: Belirtilen PDF dosyası bulunamadı ({path})"

    try:
        from PyPDF2 import PdfReader
        
        reader = PdfReader(str(path))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
                
        full_text = "\n".join(text_parts).strip()
        
        if not full_text:
            return "PDF dosyası okundu ancak metin bulunamadı. (Sadece resimlerden oluşuyor olabilir)."
            
        char_length = len(full_text)
        log.info("PDF okundu. Uzunluk: %d karakter.", char_length)
        
        # Eğer metin kısa ise doğrudan döndür (LLM maliyeti/gecikmesi yaratma)
        if char_length < 4000:
            return (
                f"PDF İçeriği (Tam Metin):\n"
                f"{'-'*40}\n"
                f"{full_text}\n"
                f"{'-'*40}"
            )
            
        # Uzun metinler için Gemini ile özetleme
        log.info("PDF uzun. Gemini ile ozetleniyor...")
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return f"Uyarı: PDF {char_length} karakter uzunluğunda. Özetlemek için GEMINI_API_KEY eksik. Metnin ilk 2000 karakteri:\n{full_text[:2000]}..."
            
        from google import genai
        from google.genai import types as gt
        
        client = genai.Client(api_key=api_key)
        
        # Token limitini aşmamak için en fazla 60.000 karakteri (yaklaşık 15k token) özetlemeye gönderelim.
        # Kitap gibi devasa PDF'lerde tamamını atmak hata verdirebilir.
        safe_text = full_text[:60000]
        
        instruction = custom_prompt if custom_prompt else "Lütfen aşağıdaki belgenin detaylı bir özetini çıkar, önemli noktaları ve ana fikri belirt."
        prompt = f"{instruction}\n\nBelge İçeriği:\n{safe_text}"
        
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
        )
        
        return (
            f"PDF başarıyla özetlendi ({char_length} karakter).\n\n"
            f"ÖZET:\n{response.text}"
        )

    except ImportError:
        return "Hata: PyPDF2 kütüphanesi eksik. Lütfen 'pip install PyPDF2' komutunu çalıştırın."
    except Exception as exc:
        log.error("PDF okuma hatasi: %s", exc)
        return f"PDF okunurken/özetlenirken bir hata oluştu: {exc}"
