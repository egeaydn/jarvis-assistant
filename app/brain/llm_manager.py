"""
Phase 5 — AI Agent + Çift-sağlayıcı LLM + Tool Calling.

Varsayılan: Groq  — OpenAI formatı, ücretsiz kota.
Yedek     : Gemini — Google genai SDK.

Sağlayıcı seçimi: LLM_PROVIDER=groq | gemini  (.env veya ortam değişkeni)

Phase 5 eklemeleri:
    - Agent-aware system prompt (çok adımlı görev farkındalığı)
    - Yeni file manager tool'ları: list_directory, create_folder,
      get_common_path, move_file, copy_file, delete_file,
      get_file_info, filter_files_by_extension
"""

import json
import os
from enum import Enum
from typing import Any, Callable, List

from dotenv import load_dotenv

load_dotenv()


class Provider(str, Enum):
    GROQ = "groq"
    GEMINI = "gemini"


SYSTEM_PROMPT = (
    "Sen Jarvis'sin — Türkçe konuşan, yardımcı ve otonom bir AI masaüstü asistanısın.\n"
    "Kullanıcının Windows bilgisayarını araçlar (tools) aracılığıyla kontrol edebilirsin.\n"
    "\n"
    "Kurallar:\n"
    "- Kullanıcının isteğini analiz et; gerekirse uygun tool'u çağır.\n"
    "- Karmaşık veya belirsiz görevlerde (örneğin düzenleme kuralları net olmayan klasör düzenleme isteklerinde) işe başlamadan önce kullanıcıya soru sorup netleştir.\n"
    "- Karmaşık görevleri adımlara böl: önce bilgi topla (listele/bul/oku), sonra işlem yap.\n"
    "- Bir projeyi çalıştırma veya hata çözme görevi verildiğinde:\n"
    "  1. Önce dizindeki dosyaları (package.json, requirements.txt vb.) listeleyip dili ve bağımlılıkları tespit et.\n"
    "  2. run_terminal_command ile çalıştırmayı veya yüklemeyi dene.\n"
    "  3. Hata alırsan hatanın çıktısını oku, analiz et ve çözmek için uygun komutları (örn. pip install) çalıştır.\n"
    "- Tool sonuçlarını değerlendir; eksik bilgi varsa bir sonraki tool'u çağır.\n"
    "- Tool sonucunu kısa ve doğal Türkçe ile özetle.\n"
    "- Tool gerekmiyorsa direkt yanıtla.\n"
    "- Gereksiz uzun açıklamalar yapma.\n"
    "- Dosya silme, taşıma, kopyalama, klasör düzenleme veya terminal komutu çalıştırma işlemlerinde kullanıcıyı bilgilendir.\n"
    "- Kullanıcı 'ekrana bak', 'ne goruyorsun', 'hata ne' gibi sorular sorarsa analyze_screen tool'unu kullan.\n"
    "- Kullanıcı bir ürün satın almak / bulmak istediğini belirtirse ('... almak istiyorum', "
    "'... arıyorum', '... satın alacağım' gibi ifadeler) search_products tool'unu çağır.\n"
    "- search_products çağırırken 'query' parametresine kullanıcının tüm cümlesini DEĞİL, "
    "sadece ürünü tanımlayan kısa anahtar kelimeleri gönder: ürün adı + varsa ölçü/renk/marka gibi "
    "ayırt edici özellikler. Gereksiz sebep/bağlam kelimelerini (kimin için, neden istendiği vb.) at.\n"
    "  Örnek: 'kardeşimin fotoğrafını asmak için 15x20 bir çerçeve arıyorum bulabilir misin' → "
    "query='15x20 çerçeve'.\n"
    "  Örnek: 'siyah renk 15x20 çerçeve arıyorum' → query='siyah 15x20 çerçeve'.\n"
    "- Kullanıcı 'günaydın' derse veya günlük özet isterse get_daily_briefing tool'unu kullan.\n"
    "- set_reminder çağırırken 'when' parametresine kullanıcının doğal dil zaman ifadesini "
    "olduğu gibi gönder (örn: 'yarın 15:00', '10 dakika sonra').\n"
    "- send_email, shutdown_system, restart_system, sleep_system, bulk_delete, "
    "set_registry_value, delete_registry_key, block_app_network gibi riskli araçları çağırmadan "
    "önce kullanıcıya ne yapacağını kısaca özetle; onay sistemi zaten devreye girecektir.\n"
)

# ── Groq / OpenAI formatı tool tanımları ─────────────────────────────────────
GROQ_TOOLS: List[dict] = [
    {"type": "function", "function": {
        "name": "open_application",
        "description": "Bir Windows masaüstü uygulamasını açar.",
        "parameters": {"type": "object",
            "properties": {"app_name": {"type": "string",
                "description": "Açılacak uygulama adı: chrome, edge, firefox, discord, spotify, steam, epic, xbox, notion, zoom, whatsapp, word, excel, powerpoint, outlook, vscode, visualstudio, cursor, androidstudio, notepad, notepad++, ssms, dbeaver, postman, github, xampp, explorer, calculator, paint, lghub, geforce, settings"}},
            "required": ["app_name"]}}},
    {"type": "function", "function": {
        "name": "close_application",
        "description": "Çalışmakta olan bir uygulamayı kapatır.",
        "parameters": {"type": "object",
            "properties": {"app_name": {"type": "string", "description": "Kapatılacak uygulamanın adı"}},
            "required": ["app_name"]}}},
    {"type": "function", "function": {
        "name": "get_system_info",
        "description": "CPU, RAM, disk kullanım yüzdeleri ve çalışan process sayısını döndürür.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "get_running_apps",
        "description": "Sistemde şu anda çalışan uygulamaların listesini döndürür.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "open_website",
        "description": "Bir web sitesini varsayılan tarayıcıda açar.",
        "parameters": {"type": "object",
            "properties": {"url": {"type": "string", "description": "Açılacak URL, örn: https://youtube.com"}},
            "required": ["url"]}}},
    {"type": "function", "function": {
        "name": "search_web",
        "description": "Google'da web araması başlatır ve tarayıcıda açar.",
        "parameters": {"type": "object",
            "properties": {"query": {"type": "string", "description": "Aranacak sorgu metni"}},
            "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "find_file",
        "description": "Bilgisayarda belirtilen adla dosya arar; bulunan dosyaların yollarını döndürür.",
        "parameters": {"type": "object",
            "properties": {"filename": {"type": "string", "description": "Aranacak dosya adı veya kısmi ad"}},
            "required": ["filename"]}}},
    {"type": "function", "function": {
        "name": "search_products",
        "description": "Kullanicinin almak istedigi bir urunu Turkiye alisveris sitelerinde (Trendyol, Hepsiburada, Amazon, N11) arar; her sitenin arama sonucunu Chrome'da ayri sekme olarak acar.",
        "parameters": {"type": "object",
            "properties": {
                "query": {"type": "string", "description": "SADECE urun adi + olcu/renk/marka gibi ayirt edici ozellikler (kisa anahtar kelimeler). Kullanicinin tum cumlesini gonderme. Orn: 'kardesimin fotografini asmak icin 15x20 bir cerceve ariyorum' -> '15x20 cerceve'"},
                "sites": {"type": "array", "items": {"type": "string"}, "description": "Opsiyonel: sadece belirli siteler (trendyol, hepsiburada, amazon, n11)"}},
            "required": ["query"]}}},
    # ── Phase 5 — Dosya / Klasör Yönetimi ────────────────────────────────────
    {"type": "function", "function": {
        "name": "list_directory",
        "description": "Bir klasördeki dosya ve alt klasörleri listeler. 'indirilenler', 'masaüstü', 'belgeler' gibi kısa isimler veya tam yol kabul eder.",
        "parameters": {"type": "object",
            "properties": {"path": {"type": "string", "description": "Listelenecek klasör yolu veya kısa ismi (örn: indirilenler, masaüstü)"}},
            "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "get_common_path",
        "description": "Desktop, Downloads, Documents gibi yaygın klasörlerin tam Windows yolunu döndürür.",
        "parameters": {"type": "object",
            "properties": {"location": {"type": "string", "description": "Konum adı: desktop, masaüstü, downloads, indirilenler, documents, belgeler, pictures, music, videos"}},
            "required": ["location"]}}},
    {"type": "function", "function": {
        "name": "create_folder",
        "description": "Yeni bir klasör oluşturur. parent_path verilmezse Masaüstü'nde oluşturur.",
        "parameters": {"type": "object",
            "properties": {
                "folder_name": {"type": "string", "description": "Oluşturulacak klasörün adı"},
                "parent_path": {"type": "string", "description": "Ana klasör yolu veya kısa ismi (isteğe bağlı)"}},
            "required": ["folder_name"]}}},
    {"type": "function", "function": {
        "name": "filter_files_by_extension",
        "description": "Bir klasördeki dosyaları uzantıya göre filtreler. Örneğin PDF, MP3, JPG dosyalarını bulmak için kullanılır.",
        "parameters": {"type": "object",
            "properties": {
                "path": {"type": "string", "description": "Klasör yolu veya kısa ismi (indirilenler, masaüstü...)"},
                "extension": {"type": "string", "description": "Uzantı: pdf, mp3, jpg, txt, docx vb. (nokta olmadan da olur)"}},
            "required": ["path", "extension"]}}},
    {"type": "function", "function": {
        "name": "get_file_info",
        "description": "Bir dosya veya klasör hakkında meta bilgi döndürür (boyut, tarih, uzantı, tam yol).",
        "parameters": {"type": "object",
            "properties": {"filepath": {"type": "string", "description": "Bilgi alınacak dosya veya klasörün tam yolu"}},
            "required": ["filepath"]}}},
    {"type": "function", "function": {
        "name": "move_file",
        "description": "Bir dosyayı kaynak yoldan hedef yola taşır. GÜVENLİK ONAYI GEREKTİRİR.",
        "parameters": {"type": "object",
            "properties": {
                "src": {"type": "string", "description": "Kaynak dosya yolu"},
                "dst": {"type": "string", "description": "Hedef klasör veya dosya yolu"}},
            "required": ["src", "dst"]}}},
    {"type": "function", "function": {
        "name": "copy_file",
        "description": "Bir dosyayı kaynak yoldan hedef yola kopyalar. Güvenlik onayı gerektirir ve mevcut dosyanın üzerine yazmaz.",
        "parameters": {"type": "object",
            "properties": {
                "src": {"type": "string", "description": "Kaynak dosya yolu"},
                "dst": {"type": "string", "description": "Hedef klasör veya dosya yolu"}},
            "required": ["src", "dst"]}}},
    {"type": "function", "function": {
        "name": "delete_file",
        "description": "Belirtilen dosyayı kalıcı olarak siler. GÜVENLİK ONAYI GEREKTİRİR.",
        "parameters": {"type": "object",
            "properties": {"filepath": {"type": "string", "description": "Silinecek dosyanın tam yolu"}},
            "required": ["filepath"]}}},
    # ── Phase 7 — Screen Vision ───────────────────────────────────────────────
    {"type": "function", "function": {
        "name": "analyze_screen",
        "description": "Ekranın anlık görüntüsünü alır ve Gemini Vision ile analiz eder. 'Ekrana bak', 'ne görüyorsun', 'bu hata ne', 'hangi uygulama açık' gibi sorularda kullan.",
        "parameters": {"type": "object",
            "properties": {"prompt": {"type": "string", "description": "Analize yönlendirici soru (isteğe bağlı): 'hata mesajı var mı?', 'ne görüyorsun?', 'hangi uygulama açık?'"}},
            "required": []}}},
    {"type": "function", "function": {
        "name": "capture_screenshot",
        "description": "Ekranın anlık görüntüsünü PNG dosyası olarak kaydeder.",
        "parameters": {"type": "object",
            "properties": {"save_path": {"type": "string", "description": "Kayıt yolu (boş bırakılırsa Masaüstü'ne zaman damgalı kaydeder)"}},
            "required": []}}},
    # ── Phase 9 — Autonomous Assistant ────────────────────────────────────────
    {"type": "function", "function": {
        "name": "run_terminal_command",
        "description": "Belirtilen dizinde bir Windows terminal komutu (PowerShell) çalıştırır ve çıktısını döndürür. Projeleri çalıştırmak, bağımlılık kurmak veya test etmek için kullan. GÜVENLİK ONAYI GEREKTİRİR.",
        "parameters": {"type": "object",
            "properties": {
                "command": {"type": "string", "description": "Çalıştırılacak terminal komutu (örn: 'python main.py', 'pip install requests', 'npm start')"},
                "cwd": {"type": "string", "description": "Komutun çalıştırılacağı dizin yolu veya kısa ismi (belgeler, masaüstü vb. - isteğe bağlı)"}},
            "required": ["command"]}}},
    {"type": "function", "function": {
        "name": "organize_folder",
        "description": "Belirtilen klasördeki dosyaları türlerine (Belgeler, Resimler, Arşivler vb.) göre analiz edip alt klasörlere taşır. GÜVENLİK ONAYI GEREKTİRİR.",
        "parameters": {"type": "object",
            "properties": {
                "folder_path": {"type": "string", "description": "Düzenlenecek klasörün yolu veya kısa ismi (örn: indirilenler, masaüstü)"},
                "rule": {"type": "string", "description": "Düzenleme kuralı: 'tür' (default) veya 'uzantı'"}},
            "required": ["folder_path"]}}},
    # ── Phase 10 — Pano (Clipboard) Yönetimi ─────────────────────────────────
    {"type": "function", "function": {
        "name": "copy_to_clipboard",
        "description": "Verilen metni sistem panosuna kopyalar.",
        "parameters": {"type": "object",
            "properties": {"text": {"type": "string", "description": "Panoya kopyalanacak metin"}},
            "required": ["text"]}}},
    {"type": "function", "function": {
        "name": "read_clipboard",
        "description": "Panodaki güncel metni okur.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "get_clipboard_history",
        "description": "Arka planda izlenen pano geçmişinden son N kaydı döndürür.",
        "parameters": {"type": "object",
            "properties": {"limit": {"type": "integer", "description": "Döndürülecek kayıt sayısı (varsayılan 5)"}},
            "required": []}}},
    # ── Phase 10 — Pencere Yönetimi ──────────────────────────────────────────
    {"type": "function", "function": {
        "name": "maximize_window",
        "description": "Belirtilen uygulamanın açık penceresini tam ekran yapar.",
        "parameters": {"type": "object",
            "properties": {"app_name": {"type": "string", "description": "Uygulama adı (örn: chrome, discord)"}},
            "required": ["app_name"]}}},
    {"type": "function", "function": {
        "name": "minimize_window",
        "description": "Belirtilen uygulamanın açık penceresini küçültür.",
        "parameters": {"type": "object",
            "properties": {"app_name": {"type": "string", "description": "Uygulama adı"}},
            "required": ["app_name"]}}},
    {"type": "function", "function": {
        "name": "close_window",
        "description": "Belirtilen uygulamanın penceresini kapatır (uygulamayı sonlandırmaz).",
        "parameters": {"type": "object",
            "properties": {"app_name": {"type": "string", "description": "Uygulama adı"}},
            "required": ["app_name"]}}},
    {"type": "function", "function": {
        "name": "focus_window",
        "description": "Belirtilen uygulamanın penceresini öne getirir ve odaklar.",
        "parameters": {"type": "object",
            "properties": {"app_name": {"type": "string", "description": "Uygulama adı"}},
            "required": ["app_name"]}}},
    {"type": "function", "function": {
        "name": "list_open_windows",
        "description": "Açık pencerelerin başlıklarını listeler.",
        "parameters": {"type": "object", "properties": {}}}},
    # ── Phase 10 — Ses Seviyesi Kontrolü ─────────────────────────────────────
    {"type": "function", "function": {
        "name": "set_volume",
        "description": "Sistem ses seviyesini yüzde (0-100) olarak ayarlar.",
        "parameters": {"type": "object",
            "properties": {"percent": {"type": "integer", "description": "Ses seviyesi yüzdesi (0-100)"}},
            "required": ["percent"]}}},
    {"type": "function", "function": {
        "name": "mute_volume",
        "description": "Sistem sesini sessize alır veya açar.",
        "parameters": {"type": "object",
            "properties": {"mute": {"type": "boolean", "description": "True: sessize al, False: sesi aç"}},
            "required": []}}},
    {"type": "function", "function": {
        "name": "get_volume",
        "description": "Mevcut ses seviyesini (%) ve sessiz durumunu döndürür.",
        "parameters": {"type": "object", "properties": {}}}},
    # ── Phase 10 — Hızlı Not Alma ─────────────────────────────────────────────
    {"type": "function", "function": {
        "name": "add_note",
        "description": "Zaman damgalı bir not ekler.",
        "parameters": {"type": "object",
            "properties": {
                "content": {"type": "string", "description": "Not içeriği"},
                "tag": {"type": "string", "description": "Opsiyonel etiket"}},
            "required": ["content"]}}},
    {"type": "function", "function": {
        "name": "list_notes",
        "description": "Kayıtlı notları en yeniden eskiye doğru listeler.",
        "parameters": {"type": "object",
            "properties": {
                "tag": {"type": "string", "description": "Sadece bu etiketli notları getir (opsiyonel)"},
                "limit": {"type": "integer", "description": "Maksimum kayıt sayısı (varsayılan 10)"}},
            "required": []}}},
    {"type": "function", "function": {
        "name": "search_notes",
        "description": "Not içeriğinde metin araması yapar.",
        "parameters": {"type": "object",
            "properties": {"query": {"type": "string", "description": "Aranacak metin"}},
            "required": ["query"]}}},
    # ── Phase 10 — Hatırlatıcı & Alarm ────────────────────────────────────────
    {"type": "function", "function": {
        "name": "set_reminder",
        "description": "Doğal dil zaman ifadesiyle ('yarın 15:00', '10 dakika sonra') hatırlatıcı kurar.",
        "parameters": {"type": "object",
            "properties": {
                "message": {"type": "string", "description": "Hatırlatıcı mesajı"},
                "when": {"type": "string", "description": "Doğal dil zaman ifadesi: 'yarın 15:00', '10 dakika sonra', 'bugün 20:30'"}},
            "required": ["message", "when"]}}},
    {"type": "function", "function": {
        "name": "list_reminders",
        "description": "Bekleyen (henüz tetiklenmemiş) tüm hatırlatıcıları listeler.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "cancel_reminder",
        "description": "Belirtilen ID'ye sahip hatırlatıcıyı iptal eder.",
        "parameters": {"type": "object",
            "properties": {"reminder_id": {"type": "string", "description": "İptal edilecek hatırlatıcının ID'si"}},
            "required": ["reminder_id"]}}},
    # ── Phase 10 — Dosya Güvenliği (Recycle Bin) ─────────────────────────────
    {"type": "function", "function": {
        "name": "move_to_recycle_bin",
        "description": "Bir dosyayı kalıcı silmek yerine Geri Dönüşüm Kutusu'na taşır (geri alınabilir). GÜVENLİK ONAYI GEREKTİRİR.",
        "parameters": {"type": "object",
            "properties": {"filepath": {"type": "string", "description": "Taşınacak dosyanın tam yolu"}},
            "required": ["filepath"]}}},
    {"type": "function", "function": {
        "name": "bulk_delete",
        "description": "Bir klasörde verilen glob desenine (örn. '*.tmp') uyan tüm dosyaları Geri Dönüşüm Kutusu'na taşır. GÜVENLİK ONAYI GEREKTİRİR.",
        "parameters": {"type": "object",
            "properties": {
                "folder_path": {"type": "string", "description": "Klasör yolu veya kısa ismi"},
                "pattern": {"type": "string", "description": "Glob deseni, örn: '*.tmp', '*.log'"}},
            "required": ["folder_path", "pattern"]}}},
    # ── Phase 10 — E-posta Gönderme ───────────────────────────────────────────
    {"type": "function", "function": {
        "name": "send_email",
        "description": "SMTP üzerinden e-posta gönderir. GÜVENLİK ONAYI GEREKTİRİR.",
        "parameters": {"type": "object",
            "properties": {
                "to": {"type": "string", "description": "Alıcı e-posta adresi"},
                "subject": {"type": "string", "description": "E-posta konusu"},
                "body": {"type": "string", "description": "E-posta gövdesi"},
                "attachments": {"type": "array", "items": {"type": "string"}, "description": "Opsiyonel ek dosya yolları"}},
            "required": ["to", "subject", "body"]}}},
    # ── Phase 10 — Sabah Brifingi ─────────────────────────────────────────────
    {"type": "function", "function": {
        "name": "get_daily_briefing",
        "description": "Hava durumu, sistem durumu (CPU/RAM/Disk) ve bugüne ait bekleyen hatırlatıcıları tek bir özet olarak döndürür. 'günaydın' gibi selamlamalarda kullan.",
        "parameters": {"type": "object",
            "properties": {"city": {"type": "string", "description": "Hava durumu için şehir adı (opsiyonel, varsayılan .env'den okunur)"}},
            "required": []}}},
    # ── Phase 10 — Sistem Güç Yönetimi ────────────────────────────────────────
    {"type": "function", "function": {
        "name": "shutdown_system",
        "description": "Bilgisayarı belirtilen bekleme süresinden sonra kapatır. GÜVENLİK ONAYI GEREKTİRİR.",
        "parameters": {"type": "object",
            "properties": {"delay_seconds": {"type": "integer", "description": "Kapatmadan önce bekleme süresi, saniye (varsayılan 30)"}},
            "required": []}}},
    {"type": "function", "function": {
        "name": "restart_system",
        "description": "Bilgisayarı belirtilen bekleme süresinden sonra yeniden başlatır. GÜVENLİK ONAYI GEREKTİRİR.",
        "parameters": {"type": "object",
            "properties": {"delay_seconds": {"type": "integer", "description": "Yeniden başlatmadan önce bekleme süresi, saniye (varsayılan 30)"}},
            "required": []}}},
    {"type": "function", "function": {
        "name": "sleep_system",
        "description": "Bilgisayarı uyku moduna alır. GÜVENLİK ONAYI GEREKTİRİR.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "cancel_shutdown",
        "description": "Zamanlanmış kapatma/yeniden başlatma işlemini iptal eder. Onay gerektirmez.",
        "parameters": {"type": "object", "properties": {}}}},
    # ── Phase 10 — Ağ/Firewall Kontrolü ──────────────────────────────────────
    {"type": "function", "function": {
        "name": "toggle_wifi",
        "description": "Belirtilen ağ arayüzünü açar veya kapatır. Kapatma (enable=false) GÜVENLİK ONAYI GEREKTİRİR.",
        "parameters": {"type": "object",
            "properties": {
                "enable": {"type": "boolean", "description": "True: aç, False: kapat"},
                "interface_name": {"type": "string", "description": "Ağ arayüzü adı (varsayılan 'Wi-Fi')"}},
            "required": ["enable"]}}},
    {"type": "function", "function": {
        "name": "block_app_network",
        "description": "Belirtilen uygulamanın internet erişimini Windows Firewall ile engeller. GÜVENLİK ONAYI GEREKTİRİR.",
        "parameters": {"type": "object",
            "properties": {"app_path": {"type": "string", "description": "Engellenecek uygulamanın tam .exe yolu"}},
            "required": ["app_path"]}}},
    # ── Phase 10 — Kayıt Defteri (yalnızca HKCU) ─────────────────────────────
    {"type": "function", "function": {
        "name": "set_registry_value",
        "description": "HKEY_CURRENT_USER (HKCU) altında bir registry değeri oluşturur/günceller. Başka hive desteklenmez. GÜVENLİK ONAYI GEREKTİRİR.",
        "parameters": {"type": "object",
            "properties": {
                "hive": {"type": "string", "description": "Yalnızca 'HKEY_CURRENT_USER' veya 'HKCU' kabul edilir"},
                "key_path": {"type": "string", "description": "Registry anahtar yolu, örn: 'Software\\\\MyApp'"},
                "value_name": {"type": "string", "description": "Değer adı"},
                "value_data": {"type": "string", "description": "Yazılacak veri"},
                "value_type": {"type": "string", "description": "REG_SZ, REG_DWORD, REG_EXPAND_SZ veya REG_MULTI_SZ (varsayılan REG_SZ)"}},
            "required": ["hive", "key_path", "value_name", "value_data"]}}},
    {"type": "function", "function": {
        "name": "delete_registry_key",
        "description": "HKEY_CURRENT_USER (HKCU) altında bir registry anahtarını siler. Başka hive desteklenmez. GÜVENLİK ONAYI GEREKTİRİR.",
        "parameters": {"type": "object",
            "properties": {
                "hive": {"type": "string", "description": "Yalnızca 'HKEY_CURRENT_USER' veya 'HKCU' kabul edilir"},
                "key_path": {"type": "string", "description": "Silinecek registry anahtar yolu"}},
            "required": ["hive", "key_path"]}}},
    # ── Phase 10 — Konuşma / Agent Geçmişinde Arama ──────────────────────────
    {"type": "function", "function": {
        "name": "search_agent_history",
        "description": "Kalıcı agent adımı geçmişinde tarih ve anahtar kelimeye göre arama yapar. 'geçen hafta ne yapmıştık' gibi sorularda kullan.",
        "parameters": {"type": "object",
            "properties": {
                "query": {"type": "string", "description": "Aranacak anahtar kelime (opsiyonel)"},
                "days_back": {"type": "integer", "description": "Kaç gün geriye bakılacağı (varsayılan 7)"}},
            "required": []}}},
]




# ── Gemini formatı tool tanımları (lazy import) ───────────────────────────────
def _build_gemini_tools():
    from google.genai import types as gt
    decls = [
        gt.FunctionDeclaration(name="open_application",
            description="Chrome, Discord, Spotify, Notepad veya VS Code gibi masaüstü uygulamasını açar.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "app_name": gt.Schema(type=gt.Type.STRING,
                    description="Açılacak uygulamanın adı: chrome, discord, spotify, notepad, vscode, steam")},
                required=["app_name"])),
        gt.FunctionDeclaration(name="close_application",
            description="Çalışmakta olan bir uygulamayı kapatır.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "app_name": gt.Schema(type=gt.Type.STRING, description="Kapatılacak uygulamanın adı")},
                required=["app_name"])),
        gt.FunctionDeclaration(name="get_system_info",
            description="CPU, RAM, disk kullanım yüzdeleri ve çalışan process sayısını döndürür.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={})),
        gt.FunctionDeclaration(name="get_running_apps",
            description="Sistemde şu anda çalışan uygulamaların listesini döndürür.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={})),
        gt.FunctionDeclaration(name="open_website",
            description="Bir web sitesini varsayılan tarayıcıda açar.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "url": gt.Schema(type=gt.Type.STRING, description="Açılacak URL")},
                required=["url"])),
        gt.FunctionDeclaration(name="search_web",
            description="Google'da web araması başlatır.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "query": gt.Schema(type=gt.Type.STRING, description="Aranacak sorgu metni")},
                required=["query"])),
        gt.FunctionDeclaration(name="find_file",
            description="Bilgisayarda belirtilen adla dosya arar.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "filename": gt.Schema(type=gt.Type.STRING, description="Aranacak dosya adı")},
                required=["filename"])),
        gt.FunctionDeclaration(name="search_products",
            description="Kullanıcının almak istediği bir ürünü Türkiye alışveriş sitelerinde (Trendyol, Hepsiburada, Amazon, N11) arar; sonuçları Chrome'da ayrı sekme olarak açar.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "query": gt.Schema(type=gt.Type.STRING, description="SADECE ürün adı + ölçü/renk/marka gibi ayırt edici özellikler (kısa anahtar kelimeler). Kullanıcının tüm cümlesini gönderme. Örn: 'kardeşimin fotoğrafını asmak için 15x20 bir çerçeve arıyorum' -> '15x20 çerçeve'"),
                "sites": gt.Schema(type=gt.Type.ARRAY, items=gt.Schema(type=gt.Type.STRING), description="Opsiyonel: sadece belirli siteler (trendyol, hepsiburada, amazon, n11)")},
                required=["query"])),
        # ── Phase 5 ───────────────────────────────────────────────────────────
        gt.FunctionDeclaration(name="list_directory",
            description="Bir klasördeki dosya ve alt klasörleri listeler.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "path": gt.Schema(type=gt.Type.STRING, description="Klasör yolu veya kısa ismi: indirilenler, masaüstü, belgeler")},
                required=["path"])),
        gt.FunctionDeclaration(name="get_common_path",
            description="Desktop, Downloads gibi yaygın klasörlerin tam yolunu döndürür.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "location": gt.Schema(type=gt.Type.STRING, description="Konum adı: desktop, downloads, documents, pictures, music, videos")},
                required=["location"])),
        gt.FunctionDeclaration(name="create_folder",
            description="Yeni bir klasör oluşturur.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "folder_name": gt.Schema(type=gt.Type.STRING, description="Oluşturulacak klasörün adı"),
                "parent_path": gt.Schema(type=gt.Type.STRING, description="Ana klasör yolu (isteğe bağlı)")},
                required=["folder_name"])),
        gt.FunctionDeclaration(name="filter_files_by_extension",
            description="Bir klasördeki dosyaları uzantıya göre filtreler (pdf, mp3, jpg vb.).",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "path": gt.Schema(type=gt.Type.STRING, description="Klasör yolu veya kısa ismi"),
                "extension": gt.Schema(type=gt.Type.STRING, description="Uzantı: pdf, mp3, jpg, txt vb.")},
                required=["path", "extension"])),
        gt.FunctionDeclaration(name="get_file_info",
            description="Bir dosya veya klasör hakkında meta bilgi döndürür.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "filepath": gt.Schema(type=gt.Type.STRING, description="Dosya veya klasör tam yolu")},
                required=["filepath"])),
        gt.FunctionDeclaration(name="move_file",
            description="Dosyayı kaynak yoldan hedef yola taşır. Güvenlik onayı gerektirir.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "src": gt.Schema(type=gt.Type.STRING, description="Kaynak dosya yolu"),
                "dst": gt.Schema(type=gt.Type.STRING, description="Hedef yol")},
                required=["src", "dst"])),
        gt.FunctionDeclaration(name="copy_file",
            description="Dosyayı kaynak yoldan hedef yola kopyalar. Güvenlik onayı gerektirir ve mevcut dosyanın üzerine yazmaz.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "src": gt.Schema(type=gt.Type.STRING, description="Kaynak dosya yolu"),
                "dst": gt.Schema(type=gt.Type.STRING, description="Hedef yol")},
                required=["src", "dst"])),
        gt.FunctionDeclaration(name="delete_file",
            description="Dosyayı kalıcı olarak siler. Güvenlik onayı gerektirir.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "filepath": gt.Schema(type=gt.Type.STRING, description="Silinecek dosyanın tam yolu")},
                required=["filepath"])),
        # ── Phase 7 ─────────────────────────────────────────────────────────
        gt.FunctionDeclaration(name="analyze_screen",
            description="Ekranın anlık görüntüsünü alır ve Gemini Vision ile analiz eder. Ekrana bak, hata ne, ne görüyorsun gibi sorularda kullan.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "prompt": gt.Schema(type=gt.Type.STRING, description="Analize yönlendirici soru (isteğe bağlı)")},
                required=[])),
        gt.FunctionDeclaration(name="capture_screenshot",
            description="Ekranın anlık görüntüsünü PNG dosyası olarak kaydeder.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "save_path": gt.Schema(type=gt.Type.STRING, description="Kayıt yolu (boş birakilirsa Masaüstü'ne kaydeder)")},
                required=[])),
        # ── Phase 9 ─────────────────────────────────────────────────────────
        gt.FunctionDeclaration(name="run_terminal_command",
            description="Belirtilen dizinde terminal komutu çalıştırır. Güvenlik onayı gerektirir.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "command": gt.Schema(type=gt.Type.STRING, description="Çalıştırılacak komut (python main.py vb.)"),
                "cwd": gt.Schema(type=gt.Type.STRING, description="Çalışma dizini (isteğe bağlı)")},
                required=["command"])),
        gt.FunctionDeclaration(name="organize_folder",
            description="Klasördeki dosyaları türlerine göre alt klasörlere taşıyarak düzenler. Güvenlik onayı gerektirir.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "folder_path": gt.Schema(type=gt.Type.STRING, description="Düzenlenecek klasör yolu"),
                "rule": gt.Schema(type=gt.Type.STRING, description="Kural: 'tür' veya 'uzantı'")},
                required=["folder_path"])),
        # ── Phase 10 — Pano (Clipboard) ────────────────────────────────────────
        gt.FunctionDeclaration(name="copy_to_clipboard",
            description="Verilen metni sistem panosuna kopyalar.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "text": gt.Schema(type=gt.Type.STRING, description="Panoya kopyalanacak metin")},
                required=["text"])),
        gt.FunctionDeclaration(name="read_clipboard",
            description="Panodaki güncel metni okur.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={})),
        gt.FunctionDeclaration(name="get_clipboard_history",
            description="Pano geçmişinden son N kaydı döndürür.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "limit": gt.Schema(type=gt.Type.INTEGER, description="Kayıt sayısı (varsayılan 5)")},
                required=[])),
        # ── Phase 10 — Pencere Yönetimi ─────────────────────────────────────────
        gt.FunctionDeclaration(name="maximize_window",
            description="Uygulamanın penceresini tam ekran yapar.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "app_name": gt.Schema(type=gt.Type.STRING, description="Uygulama adı")},
                required=["app_name"])),
        gt.FunctionDeclaration(name="minimize_window",
            description="Uygulamanın penceresini küçültür.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "app_name": gt.Schema(type=gt.Type.STRING, description="Uygulama adı")},
                required=["app_name"])),
        gt.FunctionDeclaration(name="close_window",
            description="Uygulamanın penceresini kapatır.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "app_name": gt.Schema(type=gt.Type.STRING, description="Uygulama adı")},
                required=["app_name"])),
        gt.FunctionDeclaration(name="focus_window",
            description="Uygulamanın penceresine odaklanır.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "app_name": gt.Schema(type=gt.Type.STRING, description="Uygulama adı")},
                required=["app_name"])),
        gt.FunctionDeclaration(name="list_open_windows",
            description="Açık pencerelerin başlıklarını listeler.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={})),
        # ── Phase 10 — Ses Seviyesi Kontrolü ────────────────────────────────────
        gt.FunctionDeclaration(name="set_volume",
            description="Sistem ses seviyesini yüzde (0-100) olarak ayarlar.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "percent": gt.Schema(type=gt.Type.INTEGER, description="Ses seviyesi yüzdesi")},
                required=["percent"])),
        gt.FunctionDeclaration(name="mute_volume",
            description="Sistem sesini sessize alır veya açar.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "mute": gt.Schema(type=gt.Type.BOOLEAN, description="True: sessize al, False: aç")},
                required=[])),
        gt.FunctionDeclaration(name="get_volume",
            description="Mevcut ses seviyesini ve sessiz durumunu döndürür.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={})),
        # ── Phase 10 — Hızlı Not Alma ────────────────────────────────────────────
        gt.FunctionDeclaration(name="add_note",
            description="Zaman damgalı bir not ekler.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "content": gt.Schema(type=gt.Type.STRING, description="Not içeriği"),
                "tag": gt.Schema(type=gt.Type.STRING, description="Opsiyonel etiket")},
                required=["content"])),
        gt.FunctionDeclaration(name="list_notes",
            description="Kayıtlı notları listeler.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "tag": gt.Schema(type=gt.Type.STRING, description="Etiket filtresi (opsiyonel)"),
                "limit": gt.Schema(type=gt.Type.INTEGER, description="Maksimum kayıt sayısı")},
                required=[])),
        gt.FunctionDeclaration(name="search_notes",
            description="Not içeriğinde metin araması yapar.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "query": gt.Schema(type=gt.Type.STRING, description="Aranacak metin")},
                required=["query"])),
        # ── Phase 10 — Hatırlatıcı & Alarm ───────────────────────────────────────
        gt.FunctionDeclaration(name="set_reminder",
            description="Doğal dil zaman ifadesiyle hatırlatıcı kurar.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "message": gt.Schema(type=gt.Type.STRING, description="Hatırlatıcı mesajı"),
                "when": gt.Schema(type=gt.Type.STRING, description="Doğal dil zaman ifadesi: 'yarın 15:00', '10 dakika sonra'")},
                required=["message", "when"])),
        gt.FunctionDeclaration(name="list_reminders",
            description="Bekleyen hatırlatıcıları listeler.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={})),
        gt.FunctionDeclaration(name="cancel_reminder",
            description="Bir hatırlatıcıyı iptal eder.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "reminder_id": gt.Schema(type=gt.Type.STRING, description="Hatırlatıcı ID'si")},
                required=["reminder_id"])),
        # ── Phase 10 — Dosya Güvenliği (Recycle Bin) ─────────────────────────────
        gt.FunctionDeclaration(name="move_to_recycle_bin",
            description="Dosyayı Geri Dönüşüm Kutusu'na taşır (geri alınabilir). Güvenlik onayı gerektirir.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "filepath": gt.Schema(type=gt.Type.STRING, description="Taşınacak dosyanın tam yolu")},
                required=["filepath"])),
        gt.FunctionDeclaration(name="bulk_delete",
            description="Klasörde desene uyan tüm dosyaları Geri Dönüşüm Kutusu'na taşır. Güvenlik onayı gerektirir.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "folder_path": gt.Schema(type=gt.Type.STRING, description="Klasör yolu"),
                "pattern": gt.Schema(type=gt.Type.STRING, description="Glob deseni, örn: '*.tmp'")},
                required=["folder_path", "pattern"])),
        # ── Phase 10 — E-posta Gönderme ──────────────────────────────────────────
        gt.FunctionDeclaration(name="send_email",
            description="SMTP üzerinden e-posta gönderir. Güvenlik onayı gerektirir.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "to": gt.Schema(type=gt.Type.STRING, description="Alıcı e-posta adresi"),
                "subject": gt.Schema(type=gt.Type.STRING, description="Konu"),
                "body": gt.Schema(type=gt.Type.STRING, description="Gövde"),
                "attachments": gt.Schema(type=gt.Type.ARRAY, items=gt.Schema(type=gt.Type.STRING), description="Ek dosya yolları (opsiyonel)")},
                required=["to", "subject", "body"])),
        # ── Phase 10 — Sabah Brifingi ─────────────────────────────────────────────
        gt.FunctionDeclaration(name="get_daily_briefing",
            description="Hava durumu, sistem durumu ve bekleyen hatırlatıcıları özetler.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "city": gt.Schema(type=gt.Type.STRING, description="Şehir adı (opsiyonel)")},
                required=[])),
        # ── Phase 10 — Sistem Güç Yönetimi ───────────────────────────────────────
        gt.FunctionDeclaration(name="shutdown_system",
            description="Bilgisayarı kapatır. Güvenlik onayı gerektirir.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "delay_seconds": gt.Schema(type=gt.Type.INTEGER, description="Bekleme süresi, saniye")},
                required=[])),
        gt.FunctionDeclaration(name="restart_system",
            description="Bilgisayarı yeniden başlatır. Güvenlik onayı gerektirir.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "delay_seconds": gt.Schema(type=gt.Type.INTEGER, description="Bekleme süresi, saniye")},
                required=[])),
        gt.FunctionDeclaration(name="sleep_system",
            description="Bilgisayarı uyku moduna alır. Güvenlik onayı gerektirir.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={})),
        gt.FunctionDeclaration(name="cancel_shutdown",
            description="Zamanlanmış kapatma/yeniden başlatmayı iptal eder. Onay gerektirmez.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={})),
        # ── Phase 10 — Ağ/Firewall Kontrolü ──────────────────────────────────────
        gt.FunctionDeclaration(name="toggle_wifi",
            description="Ağ arayüzünü açar/kapatır. Kapatma güvenlik onayı gerektirir.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "enable": gt.Schema(type=gt.Type.BOOLEAN, description="True: aç, False: kapat"),
                "interface_name": gt.Schema(type=gt.Type.STRING, description="Arayüz adı (varsayılan 'Wi-Fi')")},
                required=["enable"])),
        gt.FunctionDeclaration(name="block_app_network",
            description="Uygulamanın internet erişimini engeller. Güvenlik onayı gerektirir.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "app_path": gt.Schema(type=gt.Type.STRING, description="Uygulamanın tam .exe yolu")},
                required=["app_path"])),
        # ── Phase 10 — Kayıt Defteri (yalnızca HKCU) ─────────────────────────────
        gt.FunctionDeclaration(name="set_registry_value",
            description="HKCU altında registry değeri yazar. Güvenlik onayı gerektirir.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "hive": gt.Schema(type=gt.Type.STRING, description="Yalnızca 'HKEY_CURRENT_USER' veya 'HKCU'"),
                "key_path": gt.Schema(type=gt.Type.STRING, description="Registry anahtar yolu"),
                "value_name": gt.Schema(type=gt.Type.STRING, description="Değer adı"),
                "value_data": gt.Schema(type=gt.Type.STRING, description="Yazılacak veri"),
                "value_type": gt.Schema(type=gt.Type.STRING, description="REG_SZ, REG_DWORD, REG_EXPAND_SZ, REG_MULTI_SZ")},
                required=["hive", "key_path", "value_name", "value_data"])),
        gt.FunctionDeclaration(name="delete_registry_key",
            description="HKCU altında registry anahtarı siler. Güvenlik onayı gerektirir.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "hive": gt.Schema(type=gt.Type.STRING, description="Yalnızca 'HKEY_CURRENT_USER' veya 'HKCU'"),
                "key_path": gt.Schema(type=gt.Type.STRING, description="Silinecek anahtar yolu")},
                required=["hive", "key_path"])),
        # ── Phase 10 — Konuşma / Agent Geçmişinde Arama ──────────────────────────
        gt.FunctionDeclaration(name="search_agent_history",
            description="Geçmiş agent adımlarında tarih ve anahtar kelimeye göre arama yapar.",
            parameters=gt.Schema(type=gt.Type.OBJECT, properties={
                "query": gt.Schema(type=gt.Type.STRING, description="Aranacak anahtar kelime (opsiyonel)"),
                "days_back": gt.Schema(type=gt.Type.INTEGER, description="Kaç gün geriye bakılacağı")},
                required=[])),
    ]
    return [gt.Tool(function_declarations=decls)]



# ── Ortak yardımcı ────────────────────────────────────────────────────────────
def _format_result(result: Any) -> str:
    if isinstance(result, bool):
        return "Başarılı." if result else "Başarısız."
    if isinstance(result, dict):
        return "\n".join(f"{k}: {v}" for k, v in result.items())
    if isinstance(result, list):
        if not result:
            return "Sonuç bulunamadı."
        lines = [str(x) for x in result[:30]]
        if len(result) > 30:
            lines.append(f"... ve {len(result) - 30} sonuç daha")
        return "\n".join(lines)
    return str(result)


# ── LLMManager ────────────────────────────────────────────────────────────────
class LLMManager:
    """
    Groq veya Gemini üzerinden çok turlu konuşma + tool calling.

    Kullanım:
        llm = LLMManager(tool_executor=lambda n, a: tm.execute(n, **a))
        llm = LLMManager(tool_executor=..., provider="gemini")
    """

    MAX_TOOL_ROUNDS = 5

    def __init__(
        self,
        tool_executor: Callable[[str, dict], Any],
        provider: str = None,
    ) -> None:
        self._executor = tool_executor
        raw = provider or os.getenv("LLM_PROVIDER", Provider.GROQ)
        self._provider = Provider(raw.lower())

        if self._provider == Provider.GROQ:
            self._init_groq()
        else:
            self._init_gemini()

    # ── Groq ──────────────────────────────────────────────────────────────────
    def _init_groq(self) -> None:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY .env dosyasında bulunamadı.")
        self._groq = Groq(api_key=api_key)
        self._messages: List[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _chat_groq(self, user_input: str) -> str:
        self._messages.append({"role": "user", "content": user_input})

        for _ in range(self.MAX_TOOL_ROUNDS):
            resp = self._groq.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=self._messages,
                tools=GROQ_TOOLS,
                tool_choice="auto",
            )
            msg = resp.choices[0].message

            if not msg.tool_calls:
                reply = msg.content or "(Yanıt alınamadı)"
                self._messages.append({"role": "assistant", "content": reply})
                return reply

            # Asistan mesajını geçmişe ekle
            self._messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name,
                                  "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })

            # Tool'ları çalıştır ve sonuçları geçmişe ekle
            for tc in msg.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                print(f"  🔧 {name}({args})")
                raw = self._run_tool(name, args)
                self._messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": name,
                    "content": _format_result(raw),
                })

        return "(Maksimum tool turuna ulaşıldı)"

    # ── Gemini ────────────────────────────────────────────────────────────────
    def _init_gemini(self) -> None:
        from google import genai
        from google.genai import types as gt
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY .env dosyasında bulunamadı.")
        client = genai.Client(api_key=api_key)
        self._gemini_chat = client.chats.create(
            model="gemini-3.6-flash",
            config=gt.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=_build_gemini_tools(),
            ),
        )

    def _chat_gemini(self, user_input: str) -> str:
        from google.genai import types as gt
        response = self._gemini_chat.send_message(user_input)

        for _ in range(self.MAX_TOOL_ROUNDS):
            calls = [
                p for p in response.candidates[0].content.parts
                if p.function_call is not None
            ]
            if not calls:
                break
            result_parts = []
            for part in calls:
                fc = part.function_call
                print(f"  🔧 {fc.name}({dict(fc.args)})")
                raw = self._run_tool(fc.name, dict(fc.args))
                result_parts.append(
                    gt.Part.from_function_response(
                        name=fc.name,
                        response={"result": _format_result(raw)},
                    )
                )
            response = self._gemini_chat.send_message(result_parts)

        try:
            text = response.text
            return text if text else "(Yanıt alınamadı)"
        except Exception:
            parts = [
                p.text for c in response.candidates
                for p in c.content.parts if hasattr(p, "text") and p.text
            ]
            return "\n".join(parts) or "(Yanıt alınamadı)"

    # ── Ortak arayüz ──────────────────────────────────────────────────────────
    def chat(self, user_input: str) -> str:
        if self._provider == Provider.GROQ:
            return self._chat_groq(user_input)
        return self._chat_gemini(user_input)

    def reset(self) -> None:
        if self._provider == Provider.GROQ:
            self._messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        else:
            self._init_gemini()

    def _run_tool(self, name: str, args: dict) -> Any:
        try:
            return self._executor(name, args)
        except Exception as exc:
            return {"hata": str(exc)}

    @property
    def provider_name(self) -> str:
        return self._provider.value
