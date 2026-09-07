"""
Phase 5 — AI Agent (ReAct Pattern).

ReAct döngüsü:
    Thought  → LLM ne düşünüyor?
    Action   → Hangi tool seçildi?
    Observation → Tool sonucu nedir?
    → Tekrar (gerekirse) → Final Answer

Agent, LLMManager'ı içine alır ve üzerine adım adım planlama katmanı kurar.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from app.brain.memory import AgentStepRecord, ConversationMemory
from app.config.logger import get_logger

log = get_logger(__name__)


# ── Sabitler ──────────────────────────────────────────────────────────────────

MAX_STEPS = 8          # Sonsuz döngü güvencesi
FINISH_TOKEN = "FINISH"  # LLM bu action'ı döndürdüğünde döngü biter

# Onay gerektiren riskli tool'lar (Security System)
CONFIRMATION_REQUIRED: set = {
    "delete_file",
    "move_file",
    "copy_file",
    "run_terminal_command",
    "organize_folder",
    # Phase 10 — Dosya / Ağ / Sistem / E-posta riskleri
    "move_to_recycle_bin",
    "bulk_delete",
    "send_email",
    "shutdown_system",
    "restart_system",
    "sleep_system",
    "set_registry_value",
    "delete_registry_key",
    "block_app_network",
}

# Parametreye bağlı olarak onay gerektiren tool'lar: fonksiyon args alır, True ise onay ister.
# Örn. toggle_wifi(enable=True) risksizdir ama toggle_wifi(enable=False) bağlantıyı keser.
CONDITIONAL_CONFIRMATION: dict = {
    "toggle_wifi": lambda args: not args.get("enable", True),
}


# ── Veri yapısı ───────────────────────────────────────────────────────────────

@dataclass
class AgentResult:
    """run() çağrısının dönüş değeri."""
    final_answer: str
    steps: List[AgentStepRecord] = field(default_factory=list)
    success: bool = True


# ── Agent ─────────────────────────────────────────────────────────────────────

class Agent:
    """
    ReAct pattern'e dayalı AI Agent.

    Kullanım:
        agent = Agent(llm_manager=llm, tool_executor=tm.execute, memory=mem)
        result = agent.run("İndirilenler klasörümü listele ve PDF'leri aç.")
        print(result.final_answer)
    """

    def __init__(
        self,
        llm_manager,                          # LLMManager örneği
        tool_executor: Callable[[str, dict], Any],
        memory: Optional[ConversationMemory] = None,
        confirm_fn: Optional[Callable[[str, str, dict], bool]] = None,
    ) -> None:
        self._llm = llm_manager
        self._executor = tool_executor
        self._memory = memory or ConversationMemory()
        # confirm_fn(tool_name, filepath, args) → True ise devam et
        self._confirm = confirm_fn or _default_confirm

    # ── Ana giriş noktası ─────────────────────────────────────────────────────

    def run(self, user_input: str) -> AgentResult:
        """
        Kullanıcı isteğini alır, ReAct döngüsünde işler ve sonucu döndürür.
        """
        self._memory.add_user(user_input)
        self._memory.clear_steps()

        steps: List[AgentStepRecord] = []

        # Agent döngüsü başlıyor — LLM'e kullanıcı isteğini iletiyoruz
        # LLMManager zaten tool calling döngüsünü yönetiyor.
        # Agent katmanı şunları ekliyor:
        #   1. Adım adım düşünce loglama (step log)
        #   2. Güvenlik onay sistemi
        #   3. Konuşma hafızası yönetimi

        try:
            final_answer = self._run_with_steps(user_input, steps)
        except Exception as exc:
            final_answer = f"⚠️ Agent hatası: {exc}"
            return AgentResult(final_answer=final_answer, steps=steps, success=False)

        self._memory.add_assistant(final_answer)
        return AgentResult(final_answer=final_answer, steps=steps, success=True)

    # ── İç çalışma mantığı ────────────────────────────────────────────────────

    def _run_with_steps(self, user_input: str, steps: List[AgentStepRecord]) -> str:
        """
        LLMManager'ın tool calling döngüsünü izler ve adımları loglar.
        Güvenlik gerektiren tool'ları yakalar ve onay ister.
        """
        # LLMManager'ı güvenlik wrapper'ı ile sardırıyoruz
        original_executor = self._llm._executor

        def safe_executor(name: str, args: dict) -> Any:
            # Güvenlik kontrolü
            needs_confirmation = name in CONFIRMATION_REQUIRED or (
                name in CONDITIONAL_CONFIRMATION and CONDITIONAL_CONFIRMATION[name](args)
            )
            if needs_confirmation:
                approved = self._confirm(name, _describe_action(name, args), args)
                if not approved:
                    return {"sonuç": "İşlem kullanıcı tarafından iptal edildi."}

            # Tool'u çalıştır
            result = original_executor(name, args)

            # Adımı logla
            step = AgentStepRecord(
                thought=f"'{name}' tool'u çağrıldı.",
                action=name,
                action_input=args,
                observation=_format_observation(result),
            )
            steps.append(step)
            self._memory.add_agent_step(step)

            return result

        # Geçici olarak executor'ı değiştir
        self._llm._executor = safe_executor
        try:
            reply = self._llm.chat(user_input)
        finally:
            # Her durumda orijinal executor'ı geri koy
            self._llm._executor = original_executor

        return reply

    # ── Hafıza erişimi ────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Konuşma geçmişini ve hafızayı temizler."""
        self._memory.clear()
        self._llm.reset()

    @property
    def memory(self) -> ConversationMemory:
        return self._memory


# ── Yardımcılar ───────────────────────────────────────────────────────────────

def _default_confirm(tool_name: str, description: str, args: dict) -> bool:
    """
    Terminal üzerinden kullanıcıdan onay ister (güvenlik sistemi).
    """
    log.warning("GUVENLIK ONAYI GEREKIYOR | Islem: %s | Detay: %s", tool_name, description)
    try:
        answer = input("  Onaylıyor musunuz? (e/h): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "h"
    return answer in ("e", "evet", "y", "yes")



def _describe_action(tool_name: str, args: dict) -> str:
    """Tool ve argümanları insan okunabilir formatta açıklar."""
    if tool_name == "delete_file":
        path = args.get("filepath", "?")
        return f"'{path}' dosyası SİLİNECEK"
    if tool_name == "move_file":
        src = args.get("src", "?")
        dst = args.get("dst", "?")
        return f"'{src}' → '{dst}' olarak TAŞINACAK"
    if tool_name == "copy_file":
        src = args.get("src", "?")
        dst = args.get("dst", "?")
        return f"'{src}' → '{dst}' konumuna KOPYALANACAK"
    if tool_name == "run_terminal_command":
        cmd = args.get("command", "?")
        cwd = args.get("cwd", "Mevcut dizin")
        return f"Dizin: {cwd} üzerinde şu terminal komutu ÇALIŞTIRILACAK:\n> {cmd}"
    if tool_name == "organize_folder":
        path = args.get("folder_path", "?")
        rule = args.get("rule", "tür")
        return f"'{path}' klasörü '{rule}' kuralına göre DÜZENLENECEK ve dosyalar alt klasörlere taşınacak."
    if tool_name == "move_to_recycle_bin":
        path = args.get("filepath", "?")
        return f"'{path}' GERİ DÖNÜŞÜM KUTUSU'na taşınacak."
    if tool_name == "bulk_delete":
        folder = args.get("folder_path", "?")
        pattern = args.get("pattern", "?")
        return f"'{folder}' klasöründe '{pattern}' desenine uyan TÜM dosyalar geri dönüşüm kutusuna taşınacak."
    if tool_name == "send_email":
        to = args.get("to", "?")
        subject = args.get("subject", "?")
        body = args.get("body", "?")
        return f"'{to}' adresine şu e-posta GÖNDERİLECEK:\nKonu: {subject}\nGövde: {body}"
    if tool_name in ("shutdown_system", "restart_system"):
        delay = args.get("delay_seconds", 30)
        action = "KAPATILACAK" if tool_name == "shutdown_system" else "YENİDEN BAŞLATILACAK"
        return f"Bilgisayar {delay} saniye içinde {action}."
    if tool_name == "sleep_system":
        return "Bilgisayar UYKU MODUNA alınacak."
    if tool_name == "set_registry_value":
        key_path = args.get("key_path", "?")
        value_name = args.get("value_name", "?")
        value_data = args.get("value_data", "?")
        return f"HKCU\\{key_path}\\{value_name} = {value_data!r} olarak YAZILACAK."
    if tool_name == "delete_registry_key":
        key_path = args.get("key_path", "?")
        return f"HKCU\\{key_path} registry anahtarı SİLİNECEK."
    if tool_name == "block_app_network":
        app_path = args.get("app_path", "?")
        return f"'{app_path}' uygulamasının İNTERNET ERİŞİMİ ENGELLENECEK."
    if tool_name == "toggle_wifi":
        return "Wi-Fi arayüzü KAPATILACAK (bağlantı kesilecek)."
    parts = ", ".join(f"{k}={v!r}" for k, v in args.items())
    return f"{tool_name}({parts})"


def _format_observation(result: Any) -> str:
    """Tool çıktısını okunabilir stringe çevirir."""
    if isinstance(result, bool):
        return "Başarılı." if result else "Başarısız."
    if isinstance(result, dict):
        return ", ".join(f"{k}: {v}" for k, v in result.items())
    if isinstance(result, list):
        if not result:
            return "Sonuç bulunamadı."
        preview = result[:5]
        suffix = f" ... ({len(result) - 5} daha)" if len(result) > 5 else ""
        return str(preview) + suffix
    return str(result)
