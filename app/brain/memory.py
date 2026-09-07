"""
Phase 5 — Konuşma hafızası.

ConversationMemory:
    - Kullanıcı / asistan mesajlarını sırayla tutar (short-term memory).
    - Agent adımlarını (Thought / Action / Observation) da loglar.
    - get_context() → LLM'e bağlam olarak geçirilecek özet string döndürür.
"""

from dataclasses import dataclass, field
from typing import List, Literal

import json
from datetime import datetime
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_HISTORY_FILE = _DATA_DIR / "agent_history.jsonl"
_CHAT_HISTORY_FILE = _DATA_DIR / "chat_history.json"


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
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

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
    Kısa dönemli konuşma hafızası. Kalıcılık özelliğiyle (chat_history.json) desteklenir.
    """

    def __init__(self, max_messages: int = 10) -> None:
        self._max = max_messages
        self._messages: List[Message] = []
        self._step_log: List[AgentStepRecord] = []
        self._load_chat_history()

    def _load_chat_history(self) -> None:
        """Geçmiş sohbetleri dosyadan okur."""
        if not _CHAT_HISTORY_FILE.exists():
            return
        try:
            with _CHAT_HISTORY_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    self._messages.append(Message(role=item["role"], content=item["content"]))
            self._trim()
        except Exception:
            pass

    def _save_chat_history(self) -> None:
        """Mevcut sohbetleri diske yazar."""
        try:
            _DATA_DIR.mkdir(parents=True, exist_ok=True)
            data = [{"role": m.role, "content": m.content} for m in self._messages]
            with _CHAT_HISTORY_FILE.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    # ── Mesaj ekleme ──────────────────────────────────────────────────────────

    def add_user(self, content: str) -> None:
        self._messages.append(Message(role="user", content=content))
        self._trim()
        self._save_chat_history()

    def add_assistant(self, content: str) -> None:
        self._messages.append(Message(role="assistant", content=content))
        self._trim()
        self._save_chat_history()

    def add_agent_step(self, step: AgentStepRecord) -> None:
        """Bir agent adımını step log'una ekler ve kalıcı geçmişe yazar."""
        self._step_log.append(step)
        self._persist_step(step)

    def _persist_step(self, step: AgentStepRecord) -> None:
        """Agent adımını diske append eder; search_agent_history bu dosyayı okur."""
        try:
            _DATA_DIR.mkdir(parents=True, exist_ok=True)
            with _HISTORY_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "timestamp": step.timestamp,
                    "thought": step.thought,
                    "action": step.action,
                    "action_input": step.action_input,
                    "observation": step.observation,
                }, ensure_ascii=False) + "\n")
        except OSError:
            pass

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
        self._save_chat_history()

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

