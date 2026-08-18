import sys

from app.brain.llm_manager import LLMManager
from app.tools.app_tools import close_application, get_running_apps, open_application
from app.tools.browser_tools import open_website, search_web
from app.tools.file_tools import find_file, open_file
from app.tools.system_tools import get_system_info
from app.tools.tool_manager import ToolManager


def build_tool_manager() -> ToolManager:
    """
    Tüm araçları merkezi kayıt sistemine ekler.
    Yeni bir araç eklemek için buraya tek satır yeterli.
    """
    tm = ToolManager()
    tm.register("open_application",  "Masaüstü uygulaması açar",               open_application,  {"app_name": "str"})
    tm.register("close_application", "Çalışan uygulamayı kapatır",             close_application, {"app_name": "str"})
    tm.register("get_running_apps",  "Çalışan process listesini döndürür",     get_running_apps)
    tm.register("get_system_info",   "CPU/RAM/Disk bilgilerini döndürür",       get_system_info)
    tm.register("open_website",      "Web sitesini varsayılan tarayıcıda açar", open_website,      {"url": "str"})
    tm.register("search_web",        "Google'da arama yapar",                   search_web,        {"query": "str"})
    tm.register("find_file",         "Dosya adına göre ev dizininde arar",     find_file,         {"filename": "str"})
    tm.register("open_file",         "Dosyayı varsayılan uygulama ile açar",   open_file,         {"filepath": "str"})
    return tm


def main():
    print("=" * 52)
    print("🤖  Ege Assistant v0.4 — LLM + Tool Calling")
    print("=" * 52)
    print("Doğal Türkçe yaz — Gemini anlayıp tool seçer.")
    print("Özel komutlar: sıfırla · çıkış\n")

    tm = build_tool_manager()

    try:
        llm = LLMManager(
            tool_executor=lambda name, args: tm.execute(name, **args)
        )
    except EnvironmentError as exc:
        print(f"❌ {exc}")
        sys.exit(1)

    while True:
        try:
            user_input = input("Sen: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Görüşürüz!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("çıkış", "exit", "quit"):
            print("👋 Görüşürüz!")
            break

        if user_input.lower() in ("sıfırla", "reset"):
            llm.reset()
            print("✅ Konuşma geçmişi sıfırlandı.\n")
            continue

        try:
            reply = llm.chat(user_input)
            print(f"\nEge: {reply}\n")
        except Exception as exc:
            print(f"⚠️  LLM hatası: {exc}\n")


if __name__ == "__main__":
    main()


# ── Action → (tool_name, kwargs_factory) eşlemesi ───────────────────────────
ACTION_TOOL_MAP = {
    "open":        ("open_application",  lambda c: {"app_name": c["target"]}),
    "close":       ("close_application", lambda c: {"app_name": c["target"]}),
    "list_apps":   ("get_running_apps",  lambda c: {}),
    "system_info": ("get_system_info",   lambda c: {}),
    "open_web":    ("open_website",      lambda c: {"url": c["target"]}),
    "search_web":  ("search_web",        lambda c: {"query": c["query"] or c["raw"]}),
    "find_file":   ("find_file",         lambda c: {"filename": c["target"] or c["query"] or ""}),
}

HELP_TEXT = (
    "  chrome aç              → Chrome'u başlatır\n"
    "  discord'u kapat        → Discord'u kapatır\n"
    "  açık uygulamalar       → Çalışan process listesi\n"
    "  sistem bilgisi         → CPU / RAM / Disk durumu\n"
    "  youtube aç             → YouTube'u açar\n"
    "  python ara             → Web'de arama yapar\n"
    "  readme.md dosyasını bul → Dosya arar\n"
    "  araçları listele       → Kayıtlı tüm araçlar\n"
    "  çıkış                  → Uygulamadan çıkar"
)


def _display_result(action: str, result: Any, command: dict) -> None:
    """Tool sonucunu aksiyona göre ekrana yazar."""
    if action == "open":
        print(f"✅ {command['target'].title()} açılıyor...")
    elif action == "close":
        print(f"✅ {command['target'].title()} kapatıldı.")
    elif action == "open_web":
        print(f"✅ {command['target']} açılıyor...")
    elif action == "search_web":
        print(f"✅ '{command['query']}' için arama yapılıyor...")
    elif action == "find_file":
        files: List[str] = result
        if files:
            print(f"\n📁 Bulunan dosyalar ({len(files)} adet):")
            for f in files[:20]:
                print(f"   - {f}")
            if len(files) > 20:
                print(f"   ... ve {len(files) - 20} sonuç daha")
        else:
            print("   Dosya bulunamadı.")
    elif action == "list_apps":
        apps: List[str] = result
        print(f"\n📋 Çalışan uygulamalar ({len(apps)} adet):")
        for app in apps[:25]:
            print(f"   - {app}")
        if len(apps) > 25:
            print(f"   ... ve {len(apps) - 25} uygulama daha")
    elif action == "system_info":
        info = result
        print("\n📊 Sistem Bilgisi")
        print(f"   CPU    : {info['cpu_percent']}%")
        print(f"   RAM    : {info['ram_percent']}%")
        print(f"   Disk   : {info['disk_percent']}%")
        print(f"   Process: {info['running_processes']}")


def handle_command(tm: ToolManager, command: dict) -> None:
    action = command["action"]

    if action == "exit":
        print("👋 Ege Assistant kapatılıyor. Görüşürüz!")
        sys.exit(0)

    # Özel: kayıtlı araçları listele
    if command["raw"].strip().lower() in ("araçları listele", "araçlar", "tools"):
        print("\n🧰 Kayıtlı araçlar:")
        for name in tm.list_tools():
            print(f"   - {name}")
        return

    if action == "unknown":
        print(f'❓ Anlamadım: "{command["raw"]}"')
        print("   Dene:\n" + HELP_TEXT)
        return

    if action not in ACTION_TOOL_MAP:
        print(f'❓ Bilinmeyen aksiyon: "{action}"')
        return

    tool_name, kwargs_fn = ACTION_TOOL_MAP[action]
    try:
        result = tm.execute(tool_name, **kwargs_fn(command))
        _display_result(action, result, command)
    except (FileNotFoundError, RuntimeError, KeyError, ValueError) as exc:
        print(f"⚠️  {exc}")


def main():
    tm = build_tool_manager()

    print("=" * 48)
    print("🤖  Ege Assistant v0.3 — Tool System")
    print("=" * 48)
    print(HELP_TEXT)
    print()

    while True:
        try:
            user_input = input("Sen: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Görüşürüz!")
            break

        if not user_input:
            continue

        command = parse(user_input)
        handle_command(tm, command)
        print()


if __name__ == "__main__":
    main()