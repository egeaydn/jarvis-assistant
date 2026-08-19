"""
Phase 8 — Modern Desktop UI Arayüz Kodları.

PySide6 tabanlı arayüz tasarımı.
Background worker thread'leri ile kilitlenmeyen asistan deneyimi.
Canlı CPU/RAM/Disk kullanımı göstergeleri.
Grafiksel güvenlik onay penceresi entegrasyonu.
"""

import sys
import os
from pathlib import Path
from typing import Optional, Any

from PySide6.QtCore import (
    Qt, QThread, Signal, QTimer, QMutex, QWaitCondition, Slot
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QTextEdit, QLineEdit, QPushButton, QLabel,
    QProgressBar, QFrame, QMessageBox, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QColor, QIcon, QFont

import psutil

from app.brain.agent import Agent, AgentResult
from app.brain.memory import AgentStepRecord
from app.services.stt import SpeechToText
from app.services.tts import TextToSpeech
from app.ui.styles import QSS


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
        self.status_changed.emit("Dinleniyor...")
        try:
            text = self.stt.listen_once()
            self.finished.emit(text if text else "")
        except Exception as exc:
            self.status_changed.emit(f"Hata: {exc}")
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
        # Agent'ın onay fonksiyonunu bu thread'e yönlendiriyoruz
        self.agent._confirm = self._confirm_bridge

        result = self.agent.run(self.user_input)
        self.finished.emit(result)

    def _confirm_bridge(self, tool_name: str, description: str, args: dict) -> bool:
        """
        Agent'ın arka plandaki onay isteğini yakalar,
        ana pencereye (GUI thread) sinyal atar ve sonucu bekler.
        """
        self.mutex.lock()
        self.confirm_requested.emit(tool_name, description)
        # Ana thread'den yanıt gelene kadar bu thread'i blokla
        self.cond.wait(self.mutex)
        approved = self.confirm_approved
        self.mutex.unlock()
        return approved

    def set_confirm_result(self, approved: bool) -> None:
        """Ana pencereden gelen onay sonucunu set eder ve thread'i uyandırır."""
        self.mutex.lock()
        self.confirm_approved = approved
        self.cond.wakeAll()
        self.mutex.unlock()


# ── Arayüz Bileşenleri ─────────────────────────────────────────────────────────

class MessageBubble(QFrame):
    """
    Sohbet ekranındaki konuşma balonları.
    """
    def __init__(
        self,
        sender: str,
        text: str,
        role: str = "assistant",  # user | assistant | tool
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName(f"msgCard_{role}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Gönderici başlığı
        sender_label = QLabel(sender, self)
        sender_label.setObjectName(f"senderLabel_{role}")
        layout.addWidget(sender_label)

        # Mesaj içeriği
        msg_label = QLabel(text, self)
        msg_label.setObjectName("msgText")
        msg_label.setWordWrap(True)
        msg_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(msg_label)

        # Gölge efekti
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)


# ── Ana Pencere ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, agent: Agent, stt: SpeechToText, tts: TextToSpeech) -> None:
        super().__init__()
        self.agent = agent
        self.stt = stt
        self.tts = tts

        # Pencere durumları
        self.voice_active = False
        self._drag_pos = None

        # İşçiler (workers)
        self.agent_worker: Optional[AgentWorker] = None
        self.voice_worker: Optional[VoiceWorker] = None
        self.tts_worker: Optional[TTSWorker] = None

        # Temel pencere ayarları
        self.setWindowTitle("EGE ASSISTANT")
        self.resize(750, 600)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setStyleSheet(QSS)

        self._setup_ui()

        # Sistem İzleme Timer'ı (1 saniyede bir tetiklenir)
        self.sys_timer = QTimer(self)
        self.sys_timer.timeout.connect(self._update_system_stats)
        self.sys_timer.start(1000)
        self._update_system_stats()

    def _setup_ui(self) -> None:
        # Ana widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Ana layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. SOL PANEL: Dashboard (Sistem Bilgileri)
        side_panel = QFrame(self)
        side_panel.setObjectName("sidePanel")
        side_panel.setFixedWidth(230)
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(20, 20, 20, 20)
        side_layout.setSpacing(15)

        # Logo / Başlık
        logo_label = QLabel("🤖 EGE\nASSISTANT", self)
        logo_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #b4befe;")
        side_layout.addWidget(logo_label)

        # Çizgi ayırıcı
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #313244;")
        side_layout.addWidget(line)

        # CPU
        side_layout.addWidget(self._create_section_title("Sistem Durumu"))
        self.cpu_progress, self.cpu_val = self._create_stat_widget("CPU Kullanımı")
        side_layout.addLayout(self.cpu_progress)
        # RAM
        self.ram_progress, self.ram_val = self._create_stat_widget("RAM Kullanımı")
        side_layout.addLayout(self.ram_progress)
        # Disk
        self.disk_progress, self.disk_val = self._create_stat_widget("Disk Kullanımı")
        side_layout.addLayout(self.disk_progress)

        # Process / Bilgi
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)
        self.process_label = QLabel("Aktif Proses: -", self)
        self.process_label.setObjectName("dbLabel")
        info_layout.addWidget(self.process_label)
        side_layout.addLayout(info_layout)

        side_layout.addStretch()

        # Konuşma sıfırlama butonu
        reset_btn = QPushButton("Görüşmeyi Sıfırla", self)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #f38ba8;
                border: 1px solid #f38ba8;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f38ba8;
                color: #11111b;
            }
        """)
        reset_btn.clicked.connect(self._reset_chat)
        side_layout.addWidget(reset_btn)

        main_layout.addWidget(side_panel)

        # 2. SAĞ PANEL: Sohbet Arayüzü
        right_panel = QFrame(self)
        right_panel.setObjectName("mainArea")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Üst Başlık Çubuğu (Frameless Drag Area)
        title_bar = QFrame(self)
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(45)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)

        title_label = QLabel("Ege Assistant v0.7 — AI Agent + Vision", self)
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
        close_btn.setStyleSheet("QPushButton#winButton_close { background: transparent; border: none; font-weight: bold; width: 24px; height: 24px; color: #a6adc8; } QPushButton#winButton_close:hover { background-color: #f38ba8; color: #11111b; }")
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

        # Giriş Çubuğu Grubu
        input_container = QFrame(self)
        input_container.setObjectName("inputContainer")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(8, 4, 8, 4)

        self.input_field = QLineEdit(self)
        self.input_field.setObjectName("inputField")
        self.input_field.setPlaceholderText("Bir şey yazın veya mikrofona basın...")
        self.input_field.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.input_field)

        # Mikrofon Butonu
        self.mic_btn = QPushButton(self)
        self.mic_btn.setObjectName("actionButton")
        self.mic_btn.setIcon(QIcon.fromTheme("audio-input-microphone"))
        self.mic_btn.setText("🎙")
        self.mic_btn.setStyleSheet("font-size: 16px;")
        self.mic_btn.clicked.connect(self._toggle_voice)
        input_layout.addWidget(self.mic_btn)

        # Gönder Butonu
        self.send_btn = QPushButton(self)
        self.send_btn.setObjectName("actionButton")
        self.send_btn.setText("➤")
        self.send_btn.setStyleSheet("font-size: 16px;")
        self.send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_btn)

        bottom_layout.addWidget(input_container)
        right_layout.addWidget(bottom_bar)

        main_layout.addWidget(right_panel)

        # Karşılama mesajı ekle
        self.add_message("Asistan", "Merhaba! Ben Ege Assistant. Bugün size nasıl yardımcı olabilirim?", "assistant")

    # ── Pencere Sürükleme Mantığı ──
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

    # ── Yardımcı Arayüz Fonksiyonları ──
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

    # ── Sohbet Yönetimi ──
    def add_message(self, sender: str, text: str, role: str = "assistant") -> None:
        """Mesaj balonunu sohbet alanına ekler."""
        bubble = MessageBubble(sender, text, role, self)

        # Stretch'ten önce ekle
        count = self.chat_layout.count()
        self.chat_layout.insertWidget(count - 1, bubble)

        # En alta kaydır
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    # ── Eylemler / İş Mantığı ──
    @Slot()
    def _send_message(self) -> None:
        user_text = self.input_field.text().strip()
        if not user_text:
            return

        self.input_field.clear()
        self.add_message("Sen", user_text, "user")

        # Girişleri devre dışı bırak
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.mic_btn.setEnabled(False)

        # Agent Worker başlat
        self.agent_worker = AgentWorker(self.agent, user_text)
        self.agent_worker.finished.connect(self._on_agent_finished)
        self.agent_worker.confirm_requested.connect(self._on_confirm_requested)
        self.agent_worker.start()

    @Slot(object)
    def _on_agent_finished(self, result: AgentResult) -> None:
        # Arayüz girişlerini aç
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.mic_btn.setEnabled(True)
        self.input_field.setFocus()

        # Tool adımlarını ekle
        for step in result.steps:
            args_str = ", ".join(f"{k}={v!r}" for k, v in step.action_input.items())
            self.add_message("Sistem Eylemi", f"🔧 {step.action}({args_str})\nSonuç: {step.observation}", "tool")

        # Asistan yanıtını ekle
        self.add_message("Asistan", result.final_answer, "assistant")

        # Yanıtı seslendir (background thread)
        self.tts_worker = TTSWorker(self.tts, result.final_answer)
        self.tts_worker.start()

    @Slot(str, str)
    def _on_confirm_requested(self, tool_name: str, description: str) -> None:
        """
        Background thread güvenlik onayı istediğinde çalışır.
        Grafiksel QMessageBox ile onay kutusu gösterir.
        """
        reply = QMessageBox.question(
            self,
            "Güvenlik Onayı Gerekli",
            f"Asistan şu kritik işlemi yapmak istiyor:\n\n"
            f"İşlem: {tool_name}\n"
            f"Detay: {description}\n\n"
            f"Onaylıyor musunuz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        approved = (reply == QMessageBox.Yes)
        if self.agent_worker:
            self.agent_worker.set_confirm_result(approved)

    @Slot()
    def _toggle_voice(self) -> None:
        """Sesli dinlemeyi başlatır veya kapatır."""
        if self.voice_active:
            return  # Zaten aktifse bekle

        self.voice_active = True
        self.mic_btn.setObjectName("micButton_active")
        self.mic_btn.setStyle(self.mic_btn.style())  # Yeniden çiz
        self.input_field.setPlaceholderText("Dinleniyor... Lütfen konuşun.")

        self.voice_worker = VoiceWorker(self.stt)
        self.voice_worker.finished.connect(self._on_voice_finished)
        self.voice_worker.status_changed.connect(lambda s: self.input_field.setPlaceholderText(s))
        self.voice_worker.start()

    @Slot(str)
    def _on_voice_finished(self, text: str) -> None:
        self.voice_active = False
        self.mic_btn.setObjectName("actionButton")
        self.mic_btn.setStyle(self.mic_btn.style())
        self.input_field.setPlaceholderText("Bir şey yazın veya mikrofona basın...")

        if text.strip():
            self.input_field.setText(text)
            self._send_message()

    @Slot()
    def _reset_chat(self) -> None:
        self.agent.reset()
        # Sohbet alanını temizle
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.add_message("Asistan", "Görüşme geçmişi ve bellek sıfırlandı. Nasıl yardımcı olabilirim?", "assistant")

    # ── Dashboard Güncellemesi ──
    def _update_system_stats(self) -> None:
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent
            proc_count = len(psutil.pids())

            self.cpu_val.setText(f"{cpu:.0f}%")
            self.ram_val.setText(f"{ram:.0f}%")
            self.disk_val.setText(f"{disk:.0f}%")

            # Progress bar bul ve güncelle
            # layout'ların içindeki progressbar widgetlarını güncelliyoruz
            self.cpu_progress.itemAt(1).widget().setValue(int(cpu))
            self.ram_progress.itemAt(1).widget().setValue(int(ram))
            self.disk_progress.itemAt(1).widget().setValue(int(disk))

            self.process_label.setText(f"Aktif Proses: {proc_count}")
        except Exception:
            pass


# ── Çalıştırma Fonksiyonu ──
def start_ui(agent: Agent, stt: SpeechToText, tts: TextToSpeech) -> None:
    app = QApplication(sys.argv)
    window = MainWindow(agent, stt, tts)
    window.show()
    sys.exit(app.exec())
