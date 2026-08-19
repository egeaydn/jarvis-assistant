"""
Phase 5 — Konuşma hafızası.

ConversationMemory:
    - Kullanıcı / asistan mesajlarını sırayla tutar (short-term memory).
    - Agent adımlarını (Thought / Action / Observation) da loglar.
    - get_context() → LLM'e bağlam olarak geçirilecek özet string döndürür.
"""

from dataclasses import dataclass, field
from typing import List, Literal


# ── Veri yapıları ─────────────────────────────────────────────────────────────

@dataclass
class Message:
    role: Literal["user", "assistant", "system"]
    content: str


@dataclass
class AgentStepRecord:
    thought: str
    action: str
    action_input: dict
    observation: str

    def to_text(self) -> str:
        args_str = ", ".join(f"{k}={v!r}" for k, v in self.action_input.items())
        return (
            f"Düşünce: {self.thought}\n"
            f"Eylem: {self.action}({args_str})\n"
            f"Gözlem: {self.observation}"
        )


# ── Ana sınıf ─────────────────────────────────────────────────────────────────

class ConversationMemory:
    """
    Kısa dönemli konuşma hafızası.

    Kullanım:
        mem = ConversationMemory(max_messages=20)
        mem.add_user("Chrome aç")
        mem.add_assistant("Chrome açılıyor...")
        ctx = mem.get_context()   # → son mesajları özetleyen string
    """

    def __init__(self, max_messages: int = 20) -> None:
        self._max = max_messages
        self._messages: List[Message] = []
        self._step_log: List[AgentStepRecord] = []

    # ── Mesaj ekleme ──────────────────────────────────────────────────────────

    def add_user(self, content: str) -> None:
        self._messages.append(Message(role="user", content=content))
        self._trim()

    def add_assistant(self, content: str) -> None:
        self._messages.append(Message(role="assistant", content=content))
        self._trim()

    def add_agent_step(self, step: AgentStepRecord) -> None:
        """Bir agent adımını step log'una ekler."""
        self._step_log.append(step)

    # ── Okuma ─────────────────────────────────────────────────────────────────

    def get_messages(self) -> List[Message]:
        """Ham mesaj listesini döndürür."""
        return list(self._messages)

    def get_context(self, last_n: int = 6) -> str:
        """
        Son N mesajı metin olarak döndürür.
        LLM'e ek bağlam olarak geçirilmek için kullanılır.
        """
        recent = self._messages[-last_n:]
        lines = []
        for msg in recent:
            prefix = "Kullanıcı" if msg.role == "user" else "Asistan"
            lines.append(f"{prefix}: {msg.content}")
        return "\n".join(lines)

    def get_step_log(self) -> List[AgentStepRecord]:
        """Tüm agent adımı geçmişini döndürür."""
        return list(self._step_log)

    def step_log_as_text(self) -> str:
        """Agent adımlarını okunabilir metin olarak döndürür."""
        if not self._step_log:
            return "(Henüz adım yok)"
        parts = []
        for i, step in enumerate(self._step_log, 1):
            parts.append(f"--- Adım {i} ---\n{step.to_text()}")
        return "\n\n".join(parts)

    # ── Yönetim ───────────────────────────────────────────────────────────────

    def clear(self) -> None:
        """Tüm hafızayı temizler."""
        self._messages.clear()
        self._step_log.clear()

    def clear_steps(self) -> None:
        """Sadece agent adımı logunu temizler (yeni görev başında çağrılır)."""
        self._step_log.clear()

    @property
    def message_count(self) -> int:
        return len(self._messages)

    # ── İç yardımcılar ────────────────────────────────────────────────────────

    def _trim(self) -> None:
        """Mesaj sayısı üst sınırı aştığında eski mesajları siler."""
        if len(self._messages) > self._max:
            # İlk mesaj system prompt olabilir, onu koru
            self._messages = self._messages[-self._max:]
