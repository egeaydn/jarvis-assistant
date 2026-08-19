import sys
from typing import Any

from app.brain.llm_manager import LLMManager
from app.tools.app_tools import close_application, get_running_apps, open_application
from app.tools.browser_tools import open_website, search_web
from app.tools.file_tools import find_file, open_file
from app.tools.system_tools import get_system_info
from app.tools.tool_manager import ToolManager


def build_tool_manager() -> ToolManager:
    tm = ToolManager()
    tm.register("open_application",  "Masaustu uygulamasi acar",               open_application,  {"app_name": "str"})
    tm.register("close_application", "Calisan uygulamayi kapatir",             close_application, {"app_name": "str"})
    tm.register("get_running_apps",  "Calisan process listesini dondurur",     get_running_apps)
    tm.register("get_system_info",   "CPU/RAM/Disk bilgilerini dondurur",       get_system_info)
    tm.register("open_website",      "Web sitesini varsayilan tarayicide acar", open_website,      {"url": "str"})
    tm.register("search_web",        "Google'da arama yapar",                   search_web,        {"query": "str"})
    tm.register("find_file",         "Dosya adina gore ev dizininde arar",     find_file,         {"filename": "str"})
    tm.register("open_file",         "Dosyayi varsayilan uygulama ile acar",   open_file,         {"filepath": "str"})
    return tm


def main() -> None:
    tm = build_tool_manager()

    try:
        llm = LLMManager(
            tool_executor=lambda name, args: tm.execute(name, **args)
        )
    except EnvironmentError as exc:
        print(f"[HATA] {exc}")
        sys.exit(1)

    print("=" * 52)
    print("  Ege Assistant v0.4 — LLM + Tool Calling")
    print(f"  Sağlayıcı: {llm.provider_name.upper()}")
    print("=" * 52)
    print("Doğal Türkçe yaz — LLM anlayip tool seçer.")
    print("Komutlar: sıfırla · çıkış\n")

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