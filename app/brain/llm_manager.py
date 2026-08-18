"""
Phase 4 — Gemini 2.5 Flash + Tool Calling entegrasyonu.

Akış:
  Kullanıcı
    ↓
  Gemini 2.5 Flash  ← tool tanımları verilir
    ↓
  Tool Call kararı  (hangisini, hangi argümanlarla çağıracak?)
    ↓
  ToolManager.execute()
    ↓
  Sonuç → Gemini'ye iletilir
    ↓
  Doğal Türkçe yanıt
"""

import os
from typing import Any, Callable

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# ── Sistem promptu ──────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "Sen Ege Assistant'sın — Türkçe konuşan, yardımcı bir AI masaüstü asistanısın.\n"
    "Kullanıcının Windows bilgisayarını araçlar (tools) aracılığıyla kontrol edebilirsin.\n"
    "Kurallar:\n"
    "- Kullanıcının isteğini analiz et; gerekirse uygun tool'u çağır.\n"
    "- Tool sonucunu kısa ve doğal Türkçe ile özetle.\n"
    "- Tool gerekmiyorsa direkt yanıtla.\n"
    "- Gereksiz uzun açıklamalar yapma.\n"
)

# ── Gemini'a bildirilen tool tanımları ──────────────────────────────────────
_DECLARATIONS = [
    types.FunctionDeclaration(
        name="open_application",
        description="Chrome, Discord, Spotify, Notepad veya VS Code gibi masaüstü uygulamasını açar.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "app_name": types.Schema(
                    type=types.Type.STRING,
                    description=(
                        "Açılacak uygulamanın adı. "
                        "Desteklenenler: chrome, discord, spotify, notepad, vscode, steam"
                    ),
                )
            },
            required=["app_name"],
        ),
    ),
    types.FunctionDeclaration(
        name="close_application",
        description="Çalışmakta olan bir uygulamayı kapatır.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "app_name": types.Schema(
                    type=types.Type.STRING,
                    description="Kapatılacak uygulamanın adı",
                )
            },
            required=["app_name"],
        ),
    ),
    types.FunctionDeclaration(
        name="get_system_info",
        description="CPU, RAM, disk kullanım yüzdelerini ve çalışan process sayısını döndürür.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={},
        ),
    ),
    types.FunctionDeclaration(
        name="get_running_apps",
        description="Sistemde şu anda çalışan uygulamaların/process'lerin listesini döndürür.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={},
        ),
    ),
    types.FunctionDeclaration(
        name="open_website",
        description="Bir web sitesini varsayılan tarayıcıda açar.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "url": types.Schema(
                    type=types.Type.STRING,
                    description="Açılacak URL, örn: https://youtube.com",
                )
            },
            required=["url"],
        ),
    ),
    types.FunctionDeclaration(
        name="search_web",
        description="Google'da web araması başlatır ve tarayıcıda sonuçları açar.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "query": types.Schema(
                    type=types.Type.STRING,
                    description="Aranacak sorgu metni",
                )
            },
            required=["query"],
        ),
    ),
    types.FunctionDeclaration(
        name="find_file",
        description="Bilgisayarda belirtilen adla dosya arar; bulunan dosyaların yollarını döndürür.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "filename": types.Schema(
                    type=types.Type.STRING,
                    description="Aranacak dosya adı veya kısmi ad",
                )
            },
            required=["filename"],
        ),
    ),
]

_GEMINI_TOOLS = [types.Tool(function_declarations=_DECLARATIONS)]


# ── Yardımcı fonksiyon ───────────────────────────────────────────────────────
def _format_result(result: Any) -> str:
    """Tool çıktısını LLM'e göndermek için okunabilir stringe dönüştürür."""
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


# ── Ana sınıf ────────────────────────────────────────────────────────────────
class LLMManager:
    """
    Gemini 2.5 Flash ile çok turlu konuşma + tool calling akışını yönetir.

    Kullanım:
        llm = LLMManager(tool_executor=lambda name, args: tm.execute(name, **args))
        reply = llm.chat("Chrome'u aç")
    """

    MAX_TOOL_ROUNDS = 5  # sonsuz döngü koruması

    def __init__(self, tool_executor: Callable[[str, dict], Any]) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY bulunamadı. Lütfen .env dosyasını kontrol et."
            )
        self._client = genai.Client(api_key=api_key)
        self._executor = tool_executor
        self._chat = self._new_chat()

    def _new_chat(self):
        return self._client.chats.create(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=_GEMINI_TOOLS,
            ),
        )

    def _run_tool(self, name: str, args: dict) -> Any:
        try:
            return self._executor(name, args)
        except Exception as exc:
            return {"hata": str(exc)}

    def chat(self, user_input: str) -> str:
        """
        Kullanıcı mesajını işler: gerekirse tool çağırır, yanıtı döndürür.
        """
        response = self._chat.send_message(user_input)

        for _ in range(self.MAX_TOOL_ROUNDS):
            # Yanıtta tool call var mı?
            calls = [
                p for p in response.candidates[0].content.parts
                if p.function_call is not None
            ]
            if not calls:
                break

            # Tool'ları çalıştır, sonuçları topla
            result_parts = []
            for part in calls:
                fc = part.function_call
                print(f"  🔧 {fc.name}({dict(fc.args)})")
                raw = self._run_tool(fc.name, dict(fc.args))
                result_parts.append(
                    types.Part.from_function_response(
                        name=fc.name,
                        response={"result": _format_result(raw)},
                    )
                )

            # Sonuçları Gemini'ye ilet
            response = self._chat.send_message(result_parts)

        return _extract_text(response)

    def reset(self) -> None:
        """Konuşma geçmişini sıfırlar, yeni bir chat oturumu başlatır."""
        self._chat = self._new_chat()


def _extract_text(response) -> str:
    """Yanıttan metin kısmını güvenli şekilde çıkarır."""
    try:
        text = response.text
        if text:
            return text
    except Exception:
        pass
    # Fallback: tüm text part'ları birleştir
    parts = [
        p.text
        for c in response.candidates
        for p in c.content.parts
        if hasattr(p, "text") and p.text
    ]
    return "\n".join(parts) if parts else "(Yanıt alınamadı)"
