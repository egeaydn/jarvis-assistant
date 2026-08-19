"""
Phase 4 — Çift-sağlayıcı LLM + Tool Calling.

Varsayılan: Groq (llama-3.3-70b-versatile) — OpenAI formatı, ücretsiz kota.
Yedek   : Gemini (gemini-2.0-flash)          — Google genai SDK.

Sağlayıcı seçimi: LLM_PROVIDER=groq | gemini  (.env veya ortam değişkeni)
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
    "Sen Ege Assistant'sın — Türkçe konuşan, yardımcı bir AI masaüstü asistanısın.\n"
    "Kullanıcının Windows bilgisayarını araçlar (tools) aracılığıyla kontrol edebilirsin.\n"
    "Kurallar:\n"
    "- Kullanıcının isteğini analiz et; gerekirse uygun tool'u çağır.\n"
    "- Tool sonucunu kısa ve doğal Türkçe ile özetle.\n"
    "- Tool gerekmiyorsa direkt yanıtla.\n"
    "- Gereksiz uzun açıklamalar yapma.\n"
)

# ── Groq / OpenAI formatı tool tanımları ─────────────────────────────────────
GROQ_TOOLS: List[dict] = [
    {"type": "function", "function": {
        "name": "open_application",
        "description": "Bir Windows masaüstü uygulamasını açar.",
        "parameters": {"type": "object",
            "properties": {"app_name": {"type": "string",
                "description": "Açılacak uygulama adı: chrome, edge, discord, spotify, notepad, notepad++, vscode, steam, explorer, calculator, paint, wordpad"}},
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
            model="gemini-2.0-flash",
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