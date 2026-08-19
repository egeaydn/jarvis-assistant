"""
Phase v1.0 — Jarvis Final Boss Masaüstü Arayüz Kodları.

PySide6 tabanlı arayüz tasarımı.
- QSystemTrayIcon ile sistem tepsisine küçülme.
- Background WakeWordEngine ("Hey Jarvis") ile arka planda dinleme ve otomatik uyanma.
- Windows başlangıcında otomatik çalışma seçeneği (winreg).
- Kilitlenmeyen multithreaded arka plan işçileri.
- Holografik Cyan / Blue Neon temalı, dönen dijital Arc Reactor animasyonlu HUD arayüzü.
- Tamamen kaldırılmış emojiler, sade ve profesyonel teknik tasarım.
- Kısa yanıtları seslendiren, uzun yanıtları Tony Stark tarzı özet geçen akıllı TTS sistemi.
"""

import sys
import os
import random
import math
from pathlib import Path
from typing import Optional, Any

from PySide6.QtCore import (
    Qt, QThread, Signal, QTimer, QMutex, QWaitCondition, Slot, QRectF, QPointF
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QTextEdit, QLineEdit, QPushButton, QLabel,
    QProgressBar, QFrame, QMessageBox, QGraphicsDropShadowEffect,
    QSystemTrayIcon, QMenu, QCheckBox
)
from PySide6.QtGui import QColor, QIcon, QFont, QAction, QPainter, QPen, QBrush

import psutil

from app.brain.agent import Agent, AgentResult
from app.brain.memory import AgentStepRecord
from app.services.stt import SpeechToText
from app.services.tts import TextToSpeech
from app.services.wake_word import WakeWordEngine
from app.config.startup import set_autostart, is_autostart_enabled
from app.ui.styles import QSS

# ── İngilizce Jarvis Karşılama İfadeleri ─────────────────────────────────────
WAKE_RESPONSES = [
    "Yes, sir?",
    "At your service, sir.",
    "Jarvis online. What do you require, sir?",
    "Online and ready, sir.",
    "I am here, sir."
]


# ── Arc Reactor Widget (Dijital Dönen Animasyonlu Gösterge) ───────────────────

class ArcReactorWidget(QWidget):
    """
    Tony Stark'ın Arc Reactor'ünden esinlenen,
    dönen ve merkezinde hafifçe nabız gibi atan holografik widget.
    """
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(110, 110)
        self.setMaximumSize(110, 110)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_angle)
        self.timer.start(30)  # ~33 FPS pürüzsüz animasyon

    def update_angle(self) -> None:
        self.angle = (self.angle + 2) % 360
        self.update()  # paintEvent'i tetikler

    def paintEvent(self, event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        side = min(width, height)
        rect = QRectF(10, 10, side - 20, side - 20)
        center = rect.center()
        radius = (side - 20) / 2

        # 1. Dış İnce Çember (Koyu Mavi/Gri)
        pen = QPen(QColor("#1e293b"), 1.5)
        painter.setPen(pen)
        painter.drawEllipse(center, radius, radius)

        # Matris işlemlerini kolaylaştırmak için merkezi 0,0 yapalım
        painter.translate(center)

        # 2. Dönen Kesikli Çizgili Neon Cyan Çember
        painter.rotate(self.angle)
        pen_neon = QPen(QColor("#00f0ff"), 2, Qt.DashLine)
        painter.setPen(pen_neon)
        painter.drawEllipse(QPointF(0, 0), radius - 8, radius - 8)

        # 3. Zıt Yöne Dönen İç Çember
        painter.rotate(-self.angle * 1.8)
        pen_inner = QPen(QColor("#38bdf8"), 1.2, Qt.SolidLine)
        painter.setPen(pen_inner)
        painter.drawEllipse(QPointF(0, 0), radius - 16, radius - 16)

        # 4. Merkezde Pulsing (Nabız) Atan Hologram Çekirdek
        pulse = 2.5 * math.sin(self.angle * 0.1)
        core_radius = max(6.0, radius - 26.0 + pulse)

        # Dış parıldama katmanı
        glow_color = QColor(0, 240, 255, 75)
        painter.setBrush(QBrush(glow_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(0, 0), core_radius + 4.0, core_radius + 4.0)

        # Ana parlak merkez
        painter.setBrush(QBrush(QColor("#00f0ff")))
        painter.drawEllipse(QPointF(0, 0), core_radius, core_radius)


# ── Thread Worker'ları ────────────────────────────────────────────────────────

class TTSWorker(QThread):
    """Sesi arka planda çalarak arayüzün donmasını engeller."""
    def __init__(self, tts: TextToSpeech, text: str) -> None:
        super().__init__()
        self.tts = tts
        self.text = text

    def run(self) -> None:
        try:
            self.tts.speak(self.text)
        except Exception:
            pass


class VoiceWorker(QThread):
    """Mikrofonu arka planda dinler ve sesi yazıya çevirir (STT)."""
    finished = Signal(str)  # Çözülen metin
    status_changed = Signal(str)  # Durum mesajı

    def __init__(self, stt: SpeechToText) -> None:
        super().__init__()
        self.stt = stt

    def run(self) -> None:
        self.status_changed.emit("Listening...")
        try:
            text = self.stt.listen_once()
            self.finished.emit(text if text else "")
        except Exception as exc:
            self.status_changed.emit(f"Error: {exc}")
            self.finished.emit("")


class AgentWorker(QThread):
    """Agent ReAct döngüsünü arka planda çalıştırır."""
    finished = Signal(object)  # AgentResult
    confirm_requested = Signal(str, str)  # tool_name, description -> ana pencereye onay sorusu

    def __init__(self, agent: Agent, user_input: str) -> None:
        super().__init__()
        self.agent = agent
        self.user_input = user_input

        # Cross-thread senkronizasyon için mutex ve condition variable
        self.mutex = QMutex()
        self.cond = QWaitCondition()
        self.confirm_approved = False

    def run(self) -> None:
        self.agent._confirm = self._confirm_bridge
        result = self.agent.run(self.user_input)
        self.finished.emit(result)

    def _confirm_bridge(self, tool_name: str, description: str, args: dict) -> bool:
        self.mutex.lock()
        self.confirm_requested.emit(tool_name, description)
        self.cond.wait(self.mutex)
        approved = self.confirm_approved
        self.mutex.unlock()
        return approved

    def set_confirm_result(self, approved: bool) -> None:
        self.mutex.lock()
        self.confirm_approved = approved
        self.cond.wakeAll()
        self.mutex.unlock()


# ── Arayüz Bileşenleri ─────────────────────────────────────────────────────────

class MessageBubble(QFrame):
    """Sohbet ekranındaki konuşma balonları."""
    def __init__(
        self,
        sender: str,
        text: str,
        role: str = "assistant",
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName(f"msgCard_{role}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        sender_label = QLabel(sender, self)
        sender_label.setObjectName(f"senderLabel_{role}")
        layout.addWidget(sender_label)

        msg_label = QLabel(text, self)
        msg_label.setObjectName("msgText")
        msg_label.setWordWrap(True)
        msg_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(msg_label)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)


# ── Ana Pencere ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    # Wake word arka plan thread'inden tetiklenecek Qt Sinyali
    wake_word_signal = Signal()

    def __init__(self, agent: Agent, stt: SpeechToText, tts: TextToSpeech) -> None:
        super().__init__()
        self.agent = agent
        self.stt = stt
        self.tts = tts

        # Durumlar
        self.voice_active = False
        self._drag_pos = None
        self._is_closing = False

        # İşçiler
        self.agent_worker: Optional[AgentWorker] = None
        self.voice_worker: Optional[VoiceWorker] = None
        self.tts_worker: Optional[TTSWorker] = None

        # Pencere Özellikleri
        self.setWindowTitle("JARVIS")
        self.resize(780, 620)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint)
        self.setStyleSheet(QSS)

        self._setup_ui()
        self._setup_system_tray()

        # Wake Word Motorunu Başlat
        self.wake_word_signal.connect(self._on_wake_word_detected)
        self.wake_word_engine = WakeWordEngine(lambda: self.wake_word_signal.emit())
        self.wake_word_engine.start()

        # Sistem Göstergesi Timer'ı
        self.sys_timer = QTimer(self)
        self.sys_timer.timeout.connect(self._update_system_stats)
        self.sys_timer.start(1000)
        self._update_system_stats()

    def _setup_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. SOL PANEL: Dashboard
        side_panel = QFrame(self)
        side_panel.setObjectName("sidePanel")
        side_panel.setFixedWidth(240)
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(20, 20, 20, 20)
        side_layout.setSpacing(15)

        # Arc Reactor Animasyonlu Logo
        reactor_layout = QHBoxLayout()
        self.arc_reactor = ArcReactorWidget(self)
        reactor_layout.addWidget(self.arc_reactor)
        side_layout.addLayout(reactor_layout)

        # Başlık Etiketi (Holografik Mavi)
        logo_label = QLabel("JARVIS // HUD", self)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #38bdf8; letter-spacing: 2px;")
        side_layout.addWidget(logo_label)

        # İnce Bölücü Çizgi
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #1e293b;")
        side_layout.addWidget(line)

        # CPU/RAM/Disk HUD
        side_layout.addWidget(self._create_section_title("SYSTEM STATUS"))
        self.cpu_progress, self.cpu_val = self._create_stat_widget("CPU Usage")
        side_layout.addLayout(self.cpu_progress)
        self.ram_progress, self.ram_val = self._create_stat_widget("RAM Usage")
        side_layout.addLayout(self.ram_progress)
        self.disk_progress, self.disk_val = self._create_stat_widget("Disk Usage")
        side_layout.addLayout(self.disk_progress)

        self.process_label = QLabel("Active Processes: -", self)
        self.process_label.setObjectName("dbLabel")
        side_layout.addWidget(self.process_label)

        side_layout.addStretch()

        # Otomatik Başlatma Checkbox'ı (Startup)
        self.startup_check = QCheckBox("Run at Startup", self)
        self.startup_check.setChecked(is_autostart_enabled())
        self.startup_check.setStyleSheet("""
            QCheckBox { color: #94a3b8; font-size: 11px; spacing: 8px; }
            QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid #334155; border-radius: 2px; background: #020617; }
            QCheckBox::indicator:checked { background: #38bdf8; border: 1px solid #38bdf8; }
        """)
        self.startup_check.stateChanged.connect(self._toggle_autostart)
        side_layout.addWidget(self.startup_check)

        # Görüşmeyi Sıfırla
        reset_btn = QPushButton("Reset Memory", self)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f172a;
                color: #ef4444;
                border: 1px solid #7f1d1d;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
                font-size: 11px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #7f1d1d;
                color: #fca5a5;
            }
        """)
        reset_btn.clicked.connect(self._reset_chat)
        side_layout.addWidget(reset_btn)

        main_layout.addWidget(side_panel)

        # 2. SAĞ PANEL: Chat UI
        right_panel = QFrame(self)
        right_panel.setObjectName("mainArea")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Title Bar
        title_bar = QFrame(self)
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(45)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)

        title_label = QLabel("JARVIS // INTERACTIVE PROTOCOL v1.0", self)
        title_label.setObjectName("titleLabel")
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        # Pencere kontrol butonları
        min_btn = QPushButton("—", self)
        min_btn.setObjectName("winButton")
        min_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(min_btn)

        close_btn = QPushButton("✕", self)
        close_btn.setObjectName("winButton_close")
        close_btn.setStyleSheet("QPushButton#winButton_close { background: transparent; border: none; font-weight: bold; width: 24px; height: 24px; color: #64748b; } QPushButton#winButton_close:hover { background-color: #7f1d1d; color: #fca5a5; }")
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(close_btn)

        right_layout.addWidget(title_bar)

        # Sohbet Alanı (Scroll Area)
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName("scrollContents")
        self.chat_layout = QVBoxLayout(self.scroll_widget)
        self.chat_layout.setContentsMargins(15, 15, 15, 15)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch()

        self.scroll.setWidget(self.scroll_widget)
        right_layout.addWidget(self.scroll)

        # Alt Giriş Paneli
        bottom_bar = QFrame(self)
        bottom_bar.setFixedHeight(75)
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 10, 20, 15)

        input_container = QFrame(self)
        input_container.setObjectName("inputContainer")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(8, 4, 8, 4)

        self.input_field = QLineEdit(self)
        self.input_field.setObjectName("inputField")
        self.input_field.setPlaceholderText("Write a command or speak 'Hey Jarvis'...")
        self.input_field.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.input_field)

        self.mic_btn = QPushButton(self)
        self.mic_btn.setObjectName("actionButton")
        self.mic_btn.setText("VOICE")
        self.mic_btn.setStyleSheet("font-size: 11px;")
        self.mic_btn.clicked.connect(self._toggle_voice)
        input_layout.addWidget(self.mic_btn)

        self.send_btn = QPushButton(self)
        self.send_btn.setObjectName("actionButton")
        self.send_btn.setText("SEND")
        self.send_btn.setStyleSheet("font-size: 11px;")
        self.send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_btn)

        bottom_layout.addWidget(input_container)
        right_layout.addWidget(bottom_bar)

        main_layout.addWidget(right_panel)

        # İlk karşılama
        self.add_message("Jarvis", "System online and fully operational, sir.", "assistant")

    # ── Sistem Tepsisi (System Tray) ──

    def _setup_system_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self)
        
        # Basit mavi kare ikon çizimi (Tema bağımlılığını kaldırmak için)
        from PySide6.QtGui import QPixmap, QPainter
        pix = QPixmap(16, 16)
        pix.fill(QColor("#00f0ff"))
        icon = QIcon(pix)
            
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("Jarvis System UI")

        # Sağ tık menüsü
        menu = QMenu()
        show_action = QAction("Open Interface", self)
        show_action.triggered.connect(self._restore_window)
        menu.addAction(show_action)

        reset_action = QAction("Reset Memory", self)
        reset_action.triggered.connect(self._reset_chat)
        menu.addAction(reset_action)

        menu.addSeparator()

        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self._quit_application)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_icon_activated)
        self.tray_icon.show()

    def _on_tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self._restore_window()

    def _restore_window(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event: Any) -> None:
        """Pencere kapatıldığında uygulamayı kapatmak yerine tepsiye gizler."""
        if self._is_closing:
            self.wake_word_engine.stop()
            event.accept()
        else:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Jarvis",
                "Operating in background mode, sir. Speak 'Hey Jarvis' to wake me.",
                QSystemTrayIcon.Information,
                2000
            )

    def _quit_application(self) -> None:
        self._is_closing = True
        self.close()
        QApplication.quit()

    # ── Wake Word Tetiklenmesi ──

    @Slot()
    def _on_wake_word_detected(self) -> None:
        """Wake word uyanma sesi tetiklendiğinde çalışır."""
        self._restore_window()

        # Rastgele İngilizce Jarvis karşılama cümlesi seç
        response = random.choice(WAKE_RESPONSES)

        # Karşılama sesi çal
        self.tts_worker = TTSWorker(self.tts, response)
        self.tts_worker.start()

        # Otomatik dinlemeyi başlat (karşılama sesinin bitmesi için 1.4 saniye bekle)
        QTimer.singleShot(1400, self._toggle_voice)

    # ── Otomatik Başlatma ──

    @Slot(int)
    def _toggle_autostart(self, state: int) -> None:
        enabled = (state == Qt.Checked.value)
        success, message = set_autostart(enabled)
        if not success:
            QMessageBox.warning(self, "System Settings", message)
        else:
            self.add_message("System log", message, "tool")

    # ── Sürükleme Mantığı ──

    def mousePressEvent(self, event: Any) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: Any) -> None:
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: Any) -> None:
        self._drag_pos = None

    # ── Arayüz Yardımcıları ──

    def _create_section_title(self, text: str) -> QLabel:
        lbl = QLabel(text, self)
        lbl.setObjectName("sectionTitle")
        return lbl

    def _create_stat_widget(self, name: str) -> tuple[QVBoxLayout, QLabel]:
        layout = QVBoxLayout()
        layout.setSpacing(4)

        header = QHBoxLayout()
        name_lbl = QLabel(name, self)
        name_lbl.setObjectName("dbLabel")
        header.addWidget(name_lbl)

        val_lbl = QLabel("-%", self)
        val_lbl.setObjectName("dbValue")
        header.addWidget(val_lbl, 0, Qt.AlignRight)

        layout.addLayout(header)

        progress = QProgressBar(self)
        progress.setValue(0)
        layout.addWidget(progress)

        return layout, val_lbl

    # ── Sohbet İşlemleri ──

    def add_message(self, sender: str, text: str, role: str = "assistant") -> None:
        bubble = MessageBubble(sender, text, role, self)
        count = self.chat_layout.count()
        self.chat_layout.insertWidget(count - 1, bubble)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    @Slot()
    def _send_message(self) -> None:
        user_text = self.input_field.text().strip()
        if not user_text:
            return

        self.input_field.clear()
        self.add_message("You", user_text, "user")

        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.mic_btn.setEnabled(False)

        # Wake word'ü geçici olarak kapat
        self.wake_word_engine.stop()

        self.agent_worker = AgentWorker(self.agent, user_text)
        self.agent_worker.finished.connect(self._on_agent_finished)
        self.agent_worker.confirm_requested.connect(self._on_confirm_requested)
        self.agent_worker.start()

    @Slot(object)
    def _on_agent_finished(self, result: AgentResult) -> None:
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.mic_btn.setEnabled(True)
        self.input_field.setFocus()

        # Emojisiz eylem kayıtları
        for step in result.steps:
            args_str = ", ".join(f"{k}={v!r}" for k, v in step.action_input.items())
            self.add_message("System Action", f"[EXEC] {step.action}({args_str})\nObservation: {step.observation}", "tool")

        # Asistan yanıtını ekle
        self.add_message("Jarvis", result.final_answer, "assistant")

        self.wake_word_engine.start()

        # ── Akıllı Konuşma Sınırlayıcı (Smart TTS Summarizer) ───────────────────
        speak_text = result.final_answer
        
        # Eğer asistan yanıtı uzunsa, sesli olarak sadece kısa bir özet söyler
        if len(speak_text) > 140:
            tools_called = [step.action for step in result.steps]
            if "run_terminal_command" in tools_called:
                speak_text = "Terminal command executed, sir. Output is displayed on the screen."
            elif "organize_folder" in tools_called:
                speak_text = "I have organized the folders according to your rules, sir."
            elif "analyze_screen" in tools_called:
                speak_text = "Screen analysis complete, sir. Here is the detailed breakdown."
            elif "open_application" in tools_called:
                speak_text = "Opening the requested application, sir."
            else:
                # Varsayılan fallback: İlk cümleyi oku
                first_sentence = speak_text.split('.')[0]
                if len(first_sentence) < 90:
                    speak_text = first_sentence + ", sir."
                else:
                    speak_text = "I have displayed the requested information on your screen, sir."

        self.tts_worker = TTSWorker(self.tts, speak_text)
        self.tts_worker.start()

    @Slot(str, str)
    def _on_confirm_requested(self, tool_name: str, description: str) -> None:
        # Emojisiz güvenlik onayı
        reply = QMessageBox.question(
            self,
            "Security Approval Required",
            f"Jarvis requests permission for critical operation:\n\n"
            f"Operation: {tool_name}\n"
            f"Details: {description}\n\n"
            f"Do you approve, sir?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        approved = (reply == QMessageBox.Yes)
        if self.agent_worker:
            self.agent_worker.set_confirm_result(approved)

    @Slot()
    def _toggle_voice(self) -> None:
        if self.voice_active:
            return

        self.voice_active = True
        self.mic_btn.setObjectName("micButton_active")
        self.mic_btn.setText("REC")
        self.mic_btn.setStyle(self.mic_btn.style())

        self.wake_word_engine.stop()

        self.voice_worker = VoiceWorker(self.stt)
        self.voice_worker.finished.connect(self._on_voice_finished)
        self.voice_worker.status_changed.connect(lambda s: self.input_field.setPlaceholderText(s))
        self.voice_worker.start()

    @Slot(str)
    def _on_voice_finished(self, text: str) -> None:
        self.voice_active = False
        self.mic_btn.setObjectName("actionButton")
        self.mic_btn.setText("VOICE")
        self.mic_btn.setStyle(self.mic_btn.style())
        self.input_field.setPlaceholderText("Write a command or speak 'Hey Jarvis'...")

        self.wake_word_engine.start()

        if text.strip():
            self.input_field.setText(text)
            self._send_message()

    @Slot()
    def _reset_chat(self) -> None:
        self.agent.reset()
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.add_message("Jarvis", "Memory reset completed, sir.", "assistant")

    def _update_system_stats(self) -> None:
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent
            proc_count = len(psutil.pids())

            self.cpu_val.setText(f"{cpu:.0f}%")
            self.ram_val.setText(f"{ram:.0f}%")
            self.disk_val.setText(f"{disk:.0f}%")

            self.cpu_progress.itemAt(1).widget().setValue(int(cpu))
            self.ram_progress.itemAt(1).widget().setValue(int(ram))
            self.disk_progress.itemAt(1).widget().setValue(int(disk))

            self.process_label.setText(f"Active Processes: {proc_count}")
        except Exception:
            pass


# ── Çalıştırma ──
def start_ui(agent: Agent, stt: SpeechToText, tts: TextToSpeech) -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow(agent, stt, tts)
    
    if "--minimized" not in sys.argv:
        window.show()
        
    sys.exit(app.exec())
