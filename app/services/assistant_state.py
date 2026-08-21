"""
Asistan ses döngüsü için thread-safe durum makinesi.

Durumlar:
    IDLE_WAKE_LISTENING  — Arka planda yalnızca "Hey Jarvis" dinlenir.
    GREETING             — "Merhaba efendim" seslendirilir.
    COMMAND_LISTENING    — Kullanıcı komutu dinlenir.
    PROCESSING           — Agent komutu işler.
    SPEAKING             — Yanıt seslendirilir.
"""

from __future__ import annotations

import threading
from enum import Enum, auto
from typing import Callable, Optional


class AssistantState(Enum):
    """Asistanın ses/mikrofon yaşam döngüsü durumları."""

    IDLE_WAKE_LISTENING = auto()
    GREETING = auto()
    COMMAND_LISTENING = auto()
    PROCESSING = auto()
    SPEAKING = auto()


# Wake word dinlemesinin aktif olabileceği tek durum.
_WAKE_LISTENING_STATE = AssistantState.IDLE_WAKE_LISTENING


class AssistantStateManager:
    """
    Asistan durum geçişlerini thread-safe yönetir.

    Wake word motoru yalnızca ``IDLE_WAKE_LISTENING`` durumunda ve
    mikrofon açıkken dinleme yapmalıdır.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._state = AssistantState.IDLE_WAKE_LISTENING
        self._microphone_enabled = True
        self._listeners: list[Callable[[AssistantState], None]] = []

    @property
    def state(self) -> AssistantState:
        """Geçerli asistan durumu."""
        with self._lock:
            return self._state

    @property
    def microphone_enabled(self) -> bool:
        """Kullanıcı tray menüsünden mikrofonu kapattı mı."""
        with self._lock:
            return self._microphone_enabled

    def can_listen_for_wake_word(self) -> bool:
        """Wake word dinlemesi şu an güvenli mi."""
        with self._lock:
            return (
                self._microphone_enabled
                and self._state is _WAKE_LISTENING_STATE
            )

    def set_microphone_enabled(self, enabled: bool) -> None:
        """Tray menüsünden mikrofonu aç/kapat."""
        with self._lock:
            self._microphone_enabled = enabled

    def transition_to(self, new_state: AssistantState) -> None:
        """
        Yeni duruma geçer ve dinleyicileri bilgilendirir.

        Args:
            new_state: Hedef durum.
        """
        with self._lock:
            if self._state is new_state:
                return
            self._state = new_state

        for listener in self._listeners:
            try:
                listener(new_state)
            except Exception as exc:
                print(f"[STATE ERR] Dinleyici hatasi: {exc}")

    def on_state_changed(
        self,
        callback: Callable[[AssistantState], None],
    ) -> None:
        """Durum değişiminde çağrılacak geri bildirim ekler."""
        self._listeners.append(callback)

    def reset_to_idle(self) -> None:
        """Dinlemeye güvenli şekilde geri döner."""
        self.transition_to(AssistantState.IDLE_WAKE_LISTENING)
