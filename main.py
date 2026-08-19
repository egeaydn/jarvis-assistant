import sys
from typing import Any

from app.brain.agent import Agent
from app.brain.llm_manager import LLMManager
from app.brain.memory import ConversationMemory
from app.tools.app_tools import close_application, get_running_apps, open_application
from app.tools.browser_tools import open_website, search_web
from app.tools.file_manager_tools import (
    copy_file,
    create_folder,
    delete_file,
    filter_files_by_extension,
    get_common_path,
    get_file_info,
    list_directory,
    move_file,
)
from app.tools.file_tools import find_file, open_file
from app.tools.screen_tools import analyze_screen, capture_screenshot
from app.tools.system_tools import get_system_info
from app.tools.tool_manager import ToolManager
from app.services.stt import SpeechToText
from app.services.tts import TextToSpeech
from app.ui.window import start_ui


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

    # ── Phase 5 — Dosya / Klasör Yönetimi ────────────────────────────────────
    tm.register("list_directory",           "Klasor icerigini listeler",                  list_directory,           {"path": "str"})
    tm.register("get_common_path",          "Yaygin klasor yolunu dondurur",              get_common_path,          {"location": "str"})
    tm.register("create_folder",            "Yeni klasor olusturur",                      create_folder,            {"folder_name": "str", "parent_path": "str (opsiyonel)"})
    tm.register("filter_files_by_extension","Klasoru uzantiya gore filtreler",             filter_files_by_extension,{"path": "str", "extension": "str"})
    tm.register("get_file_info",            "Dosya meta bilgisini dondurur",              get_file_info,            {"filepath": "str"})
    tm.register("move_file",                "Dosya tasir (guvenlik onayi gerektirir)",    move_file,                {"src": "str", "dst": "str"})
    tm.register("copy_file",                "Dosya kopyalar",                             copy_file,                {"src": "str", "dst": "str"})
    tm.register("delete_file",              "Dosya siler (guvenlik onayi gerektirir)",   delete_file,              {"filepath": "str"})

    # ── Phase 7 — Screen Vision ───────────────────────────────────────────
    tm.register("analyze_screen",           "Ekrani Gemini Vision ile analiz eder",      analyze_screen,           {"prompt": "str (opsiyonel)"})
    tm.register("capture_screenshot",       "Ekran goruntusunu PNG olarak kaydeder",     capture_screenshot,       {"save_path": "str (opsiyonel)"})

    return tm


def _print_header(provider: str, voice_mode: bool) -> None:
    mode_str = "AI Agent + Sesli Mod" if voice_mode else "AI Agent + Vision"
    print("=" * 52)
    print(f"  Ege Assistant v0.7 — {mode_str}")
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


    try:
        llm = LLMManager(
            tool_executor=lambda name, args: tm.execute(name, **args)
        )
    except EnvironmentError as exc:
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
        stt = SpeechToText()
        tts = TextToSpeech()
        start_ui(agent, stt, tts)


if __name__ == "__main__":
    main()