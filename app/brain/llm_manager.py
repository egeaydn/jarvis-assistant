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
    "- Dosya silme, taşıma, klasör düzenleme veya terminal komutu çalıştırma işlemlerinde kullanıcıyı bilgilendir.\n"
    "- Kullanıcı 'ekrana bak', 'ne goruyorsun', 'hata ne' gibi sorular sorarsa analyze_screen tool'unu kullan.\n"
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
        "description": "Bir dosyayı kaynak yoldan hedef yola kopyalar.",
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
            description="Dosyayı kaynak yoldan hedef yola kopyalar.",
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