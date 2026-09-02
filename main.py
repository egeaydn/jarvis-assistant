import sys
from typing import Any

from app.brain.agent import Agent
from app.brain.llm_manager import LLMManager
from app.brain.memory import ConversationMemory
from app.tools.app_tools import close_application, get_running_apps, open_application
from app.tools.browser_tools import open_website, search_web
from app.tools.file_manager_tools import (
    bulk_delete,
    copy_file,
    create_folder,
    delete_file,
    filter_files_by_extension,
    get_common_path,
    get_file_info,
    list_directory,
    move_file,
    move_to_recycle_bin,
)
from app.tools.file_tools import find_file, open_file
from app.tools.screen_tools import analyze_screen, capture_screenshot
from app.tools.shopping_tools import search_products
from app.tools.system_tools import get_system_info
from app.tools.tool_manager import ToolManager
from app.services.stt import SpeechToText
from app.services.tts import TextToSpeech
from app.ui.window import start_ui
from app.tools.autonomous_tools import run_terminal_command, organize_folder

# ── Phase 10 — Prodüktivite / Güvenlik araçları ───────────────────────────────
from app.tools.clipboard_tools import copy_to_clipboard, get_clipboard_history, read_clipboard
from app.tools.window_tools import close_window, focus_window, list_open_windows, maximize_window, minimize_window
from app.tools.volume_tools import get_volume, mute_volume, set_volume
from app.tools.notes_tools import add_note, list_notes, search_notes
from app.tools.reminder_tools import cancel_reminder, list_reminders, set_reminder
from app.tools.email_tools import send_email
from app.tools.briefing_tools import get_daily_briefing
from app.tools.system_power_tools import cancel_shutdown, restart_system, shutdown_system, sleep_system
from app.tools.network_tools import block_app_network, toggle_wifi
from app.tools.registry_tools import delete_registry_key, set_registry_value
from app.tools.memory_search_tools import search_agent_history
from app.services.clipboard_listener import start_clipboard_listener
from app.services.reminder_service import start_reminder_service


def build_tool_manager() -> ToolManager:
    tm = ToolManager()

    # ── Phase 1-4 tool'ları ───────────────────────────────────────────────────
    tm.register("open_application",  "Masaustu uygulamasi acar",               open_application,  {"app_name": "str"})
    tm.register("close_application", "Calisan uygulamayi kapatir",             close_application, {"app_name": "str"})
    tm.register("get_running_apps",  "Calisan process listesini dondurur",     get_running_apps)
    tm.register("get_system_info",   "CPU/RAM/Disk bilgilerini dondurur",       get_system_info)
    tm.register("open_website",      "Web sitesini varsayilan tarayicide acar", open_website,      {"url": "str"})
    tm.register("search_web",        "Google'da arama yapar",                   search_web,        {"query": "str"})
    tm.register("find_file",         "Dosya adina gore ev dizininde arar",     find_file,         {"filename": "str"})
    tm.register("open_file",         "Dosyayi varsayilan uygulama ile acar",   open_file,         {"filepath": "str"})
    tm.register("search_products",   "Urunu alisveris sitelerinde arar ve Chrome'da sekme olarak acar", search_products, {"query": "str", "sites": "list[str] (opsiyonel)"})

    # ── Phase 5 — Dosya / Klasör Yönetimi ────────────────────────────────────
    tm.register("list_directory",           "Klasor icerigini listeler",                  list_directory,           {"path": "str"})
    tm.register("get_common_path",          "Yaygin klasor yolunu dondurur",              get_common_path,          {"location": "str"})
    tm.register("create_folder",            "Yeni klasor olusturur",                      create_folder,            {"folder_name": "str", "parent_path": "str (opsiyonel)"})
    tm.register("filter_files_by_extension","Klasoru uzantiya gore filtreler",             filter_files_by_extension,{"path": "str", "extension": "str"})
    tm.register("get_file_info",            "Dosya meta bilgisini dondurur",              get_file_info,            {"filepath": "str"})
    tm.register("move_file",                "Dosya tasir (guvenlik onayi gerektirir)",    move_file,                {"src": "str", "dst": "str"})
    tm.register("copy_file",                "Dosya kopyalar (guvenlik onayi gerektirir)", copy_file,                {"src": "str", "dst": "str"})
    tm.register("delete_file",              "Dosya siler (guvenlik onayi gerektirir)",   delete_file,              {"filepath": "str"})

    # ── Phase 7 — Screen Vision ───────────────────────────────────────────
    tm.register("analyze_screen",           "Ekrani Gemini Vision ile analiz eder",      analyze_screen,           {"prompt": "str (opsiyonel)"})
    tm.register("capture_screenshot",       "Ekran goruntusunu PNG olarak kaydeder",     capture_screenshot,       {"save_path": "str (opsiyonel)"})

    # ── Phase 9 — Autonomous Assistant ────────────────────────────────────────
    tm.register("run_terminal_command",     "Dizinde terminal komutu calistirir",        run_terminal_command,     {"command": "str", "cwd": "str (opsiyonel)"})
    tm.register("organize_folder",          "Klasordeki dosyalari otomatik duzenler",    organize_folder,          {"folder_path": "str", "rule": "str (opsiyonel)"})

    # ── Phase 10 — Pano (Clipboard) Yönetimi ─────────────────────────────────
    tm.register("copy_to_clipboard",        "Metni sistem panosuna kopyalar",            copy_to_clipboard,        {"text": "str"})
    tm.register("read_clipboard",           "Panodaki guncel metni okur",                read_clipboard)
    tm.register("get_clipboard_history",    "Pano gecmisinden son N kaydi dondurur",     get_clipboard_history,    {"limit": "int (opsiyonel)"})

    # ── Phase 10 — Pencere Yönetimi ───────────────────────────────────────────
    tm.register("maximize_window",          "Uygulama penceresini tam ekran yapar",      maximize_window,          {"app_name": "str"})
    tm.register("minimize_window",          "Uygulama penceresini kucultur",             minimize_window,          {"app_name": "str"})
    tm.register("close_window",             "Uygulama penceresini kapatir",              close_window,             {"app_name": "str"})
    tm.register("focus_window",             "Uygulama penceresine odaklanir",            focus_window,             {"app_name": "str"})
    tm.register("list_open_windows",        "Acik pencerelerin basliklarini listeler",   list_open_windows)

    # ── Phase 10 — Ses Seviyesi Kontrolü ──────────────────────────────────────
    tm.register("set_volume",               "Sistem ses seviyesini yuzde olarak ayarlar",set_volume,               {"percent": "int"})
    tm.register("mute_volume",              "Sistemi sessize alir veya acar",            mute_volume,              {"mute": "bool (opsiyonel)"})
    tm.register("get_volume",               "Mevcut ses seviyesini ve sessiz durumunu dondurur", get_volume)

    # ── Phase 10 — Hızlı Not Alma ──────────────────────────────────────────────
    tm.register("add_note",                 "Zaman damgali not ekler",                   add_note,                 {"content": "str", "tag": "str (opsiyonel)"})
    tm.register("list_notes",               "Kayitli notlari listeler",                  list_notes,               {"tag": "str (opsiyonel)", "limit": "int (opsiyonel)"})
    tm.register("search_notes",             "Notlar icinde metin aramasi yapar",         search_notes,             {"query": "str"})

    # ── Phase 10 — Hatırlatıcı & Alarm ────────────────────────────────────────
    tm.register("set_reminder",             "Dogal dil zaman ifadesiyle hatirlatici kurar", set_reminder,          {"message": "str", "when": "str"})
    tm.register("list_reminders",           "Bekleyen hatirlaticilari listeler",         list_reminders)
    tm.register("cancel_reminder",          "Bir hatirlaticiyi iptal eder",              cancel_reminder,          {"reminder_id": "str"})

    # ── Phase 10 — Dosya Güvenliği (Recycle Bin) ─────────────────────────────
    tm.register("move_to_recycle_bin",      "Dosyayi geri donusum kutusuna tasir (guvenlik onayi gerektirir)", move_to_recycle_bin, {"filepath": "str"})
    tm.register("bulk_delete",              "Desene uyan tum dosyalari geri donusum kutusuna tasir (guvenlik onayi gerektirir)", bulk_delete, {"folder_path": "str", "pattern": "str"})

    # ── Phase 10 — E-posta Gönderme ───────────────────────────────────────────
    tm.register("send_email",               "SMTP uzerinden e-posta gonderir (guvenlik onayi gerektirir)", send_email, {"to": "str", "subject": "str", "body": "str", "attachments": "list[str] (opsiyonel)"})

    # ── Phase 10 — Sabah Brifingi ──────────────────────────────────────────────
    tm.register("get_daily_briefing",       "Hava durumu, sistem ve hatirlaticilari ozetler", get_daily_briefing,   {"city": "str (opsiyonel)"})

    # ── Phase 10 — Sistem Güç Yönetimi ────────────────────────────────────────
    tm.register("shutdown_system",          "Bilgisayari kapatir (guvenlik onayi gerektirir)", shutdown_system,     {"delay_seconds": "int (opsiyonel)"})
    tm.register("restart_system",           "Bilgisayari yeniden baslatir (guvenlik onayi gerektirir)", restart_system, {"delay_seconds": "int (opsiyonel)"})
    tm.register("sleep_system",             "Bilgisayari uyku moduna alir (guvenlik onayi gerektirir)", sleep_system)
    tm.register("cancel_shutdown",          "Zamanlanmis kapatma/yeniden baslatmayi iptal eder", cancel_shutdown)

    # ── Phase 10 — Ağ/Firewall Kontrolü ───────────────────────────────────────
    tm.register("toggle_wifi",              "Wi-Fi arayuzunu acar/kapatir (kapatma guvenlik onayi gerektirir)", toggle_wifi, {"enable": "bool", "interface_name": "str (opsiyonel)"})
    tm.register("block_app_network",        "Uygulamanin internet erisimini engeller (guvenlik onayi gerektirir)", block_app_network, {"app_path": "str"})

    # ── Phase 10 — Kayıt Defteri (yalnızca HKCU) ─────────────────────────────
    tm.register("set_registry_value",       "HKCU altinda registry degeri yazar (guvenlik onayi gerektirir)", set_registry_value, {"hive": "str", "key_path": "str", "value_name": "str", "value_data": "any", "value_type": "str (opsiyonel)"})
    tm.register("delete_registry_key",      "HKCU altinda registry anahtari siler (guvenlik onayi gerektirir)", delete_registry_key, {"hive": "str", "key_path": "str"})

    # ── Phase 10 — Konuşma / Agent Geçmişinde Arama ──────────────────────────
    tm.register("search_agent_history",     "Gecmis agent adimlarinda tarih ve anahtar kelimeye gore arar", search_agent_history, {"query": "str (opsiyonel)", "days_back": "int (opsiyonel)"})

    return tm


def _print_header(provider: str, voice_mode: bool) -> None:
    mode_str = "AI Agent + Sesli Mod" if voice_mode else "Autonomous Assistant"
    print("=" * 52)
    print(f"  Ege Assistant v0.9 — {mode_str}")
    print(f"  Saglaiyci: {provider.upper()}")
    print("=" * 52)


# ── Text modu döngüsü ─────────────────────────────────────────────────────────

def run_text_mode(agent: Agent, llm_provider: str) -> None:
    _print_header(llm_provider, voice_mode=False)
    print("Dogal Turkce yaz — Agent cok adimli gorevler yapabilir.")
    print("Komutlar: sifirla . gecmis . cikis\n")

    while True:
        try:
            user_input = input("Sen: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGorusuruz!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("cikis", "exit", "quit", "çıkış"):
            print("Gorusuruz!")
            break
        if user_input.lower() in ("sifirla", "reset", "sıfırla"):
            agent.reset()
            print("Konusma gecmisi ve hafiza sifirlanedi.\n")
            continue
        if user_input.lower() in ("gecmis", "geçmiş", "history"):
            _show_history(agent)
            continue

        _run_agent(agent, user_input)


# ── Voice modu döngüsü ────────────────────────────────────────────────────────

def run_voice_mode(agent: Agent, llm_provider: str) -> None:
    from app.services.stt import SpeechToText
    from app.services.tts import TextToSpeech

    _print_header(llm_provider, voice_mode=True)
    print("Enter'a bas ve konus. Cikis icin 'q' yaz.\n")

    try:
        stt = SpeechToText(language="tr-TR", timeout=5, phrase_time_limit=10)
        tts = TextToSpeech(rate=170)
    except Exception as exc:
        print(f"[HATA] Ses servisi baslanamadi: {exc}")
        sys.exit(1)

    # Bir kere kalibre et
    try:
        stt.calibrate(duration=1.0)
    except RuntimeError as exc:
        print(f"[UYARI] Kalibrasyon hatasi: {exc}")
        print("Metin moduna geciliyor...\n")
        run_text_mode(agent, llm_provider)
        return

    print("\nHazir! Enter'a basinca dinlemeye basliyor.\n")

    while True:
        try:
            key = input("[ Enter = konus | q = cikis ]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nGorusuruz!")
            break

        if key == "q":
            print("Gorusuruz!")
            break
        if key == "sifirla":
            agent.reset()
            print("Sifirlandi.\n")
            continue
        if key == "gecmis":
            _show_history(agent)
            continue

        # Sesli giriş
        print("  Dinleniyor...")
        try:
            user_input = stt.listen_once()
        except RuntimeError as exc:
            print(f"  [HATA] {exc}\n")
            continue

        if not user_input:
            print("  (Ses anlasilamadi, tekrar deneyin)\n")
            continue

        print(f"Sen (ses): {user_input}")

        # Agent'ı çalıştır
        result = _run_agent(agent, user_input)

        # Cevabı seslendir
        if result:
            print("  Sesli cevap veriliyor...")
            try:
                tts.speak(result)
            except Exception as exc:
                print(f"  [TTS UYARI] {exc}")


# ── Ortak yardımcılar ─────────────────────────────────────────────────────────

def _run_agent(agent: Agent, user_input: str) -> str | None:
    try:
        result = agent.run(user_input)
        if result.steps:
            print(f"  {len(result.steps)} adim tamamlandi.")
        print(f"\nEge: {result.final_answer}\n")
        return result.final_answer
    except Exception as exc:
        print(f"Hata: {exc}\n")
        return None


def _show_history(agent: Agent) -> None:
    steps = agent.memory.get_step_log()
    if not steps:
        print("(Henuz agent adimi yok)\n")
    else:
        print("\nAgent Adim Gecmisi:")
        print(agent.memory.step_log_as_text())
        print()


# ── Giriş noktası ─────────────────────────────────────────────────────────────

def main() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    voice_mode = "--voice" in sys.argv

    tm = build_tool_manager()

    # Phase 10 — Arka plan servislerini baslat (pano gecmisi, hatirlaticilar)
    start_clipboard_listener()
    start_reminder_service()

    try:
        llm = LLMManager(
            tool_executor=lambda name, args: tm.execute(name, **args)
        )
    except (EnvironmentError, ImportError, ValueError) as exc:
        print(f"[HATA] {exc}")
        sys.exit(1)

    memory = ConversationMemory(max_messages=30)
    agent = Agent(
        llm_manager=llm,
        tool_executor=lambda name, args: tm.execute(name, **args),
        memory=memory,
    )

    if "--voice" in sys.argv:
        run_voice_mode(agent, llm.provider_name)
    elif "--text" in sys.argv:
        run_text_mode(agent, llm.provider_name)
    else:
        # Varsayılan olarak modern masaüstü arayüzünü (GUI) başlat
        _hide_console_window()
        try:
            stt = SpeechToText()
            tts = TextToSpeech()
            start_ui(agent, stt, tts)
        except Exception as exc:
            print(f"[HATA] Arayüz başlatılamadı: {exc}")
            sys.exit(1)


def _hide_console_window() -> None:
    """`python main.py` ile başlatılınca görev çubuğunda ayrı bir python.exe
    ikonu belirmemesi için konsol penceresini gizler (derlenmiş .exe zaten
    konsolsuz calistigi icin bu no-op olur)."""
    if sys.platform != "win32" or getattr(sys, "frozen", False):
        return
    try:
        import ctypes

        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
    except (AttributeError, OSError):
        pass


if __name__ == "__main__":
    main()
