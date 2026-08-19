"""
Phase 8 — UI Stil Dosyası (QSS / Qt Stylesheet).

Modern, karanlık (Catppuccin Mocha esintili), degradeler ve yumuşak köşeler
içeren premium masaüstü asistanı tasarım teması.
"""

QSS = """
/* ── Genel Pencere Ayarları ── */
QMainWindow {
    background-color: #11111b;
}

QWidget {
    color: #cdd6f4;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 14px;
}

/* ── Panel Tasarımları ── */
QFrame#sidePanel {
    background-color: #181825;
    border-right: 1px solid #313244;
    border-radius: 0px;
}

QFrame#mainArea {
    background-color: #11111b;
}

/* ── Başlık Barı (Title Bar) ── */
QFrame#titleBar {
    background-color: #11111b;
    border-bottom: 1px solid #1e1e2e;
}

QLabel#titleLabel {
    font-weight: bold;
    font-size: 15px;
    color: #89b4fa;
}

/* ── Sohbet Alanı (Scroll Area) ── */
QScrollArea {
    border: none;
    background-color: transparent;
}

QWidget#scrollContents {
    background-color: transparent;
}

/* ── Konuşma Balonları ve Mesaj Kartları ── */
QFrame#msgCard_user {
    background-color: #313244;
    border-radius: 12px;
    border: 1px solid #45475a;
    margin-left: 40px;
    margin-right: 10px;
}

QFrame#msgCard_assistant {
    background-color: #1e1e2e;
    border-radius: 12px;
    border: 1px solid #313244;
    margin-left: 10px;
    margin-right: 40px;
}

QFrame#msgCard_tool {
    background-color: #181825;
    border-radius: 8px;
    border: 1px dashed #f38ba8;
    margin-left: 20px;
    margin-right: 20px;
}

QLabel#msgText {
    color: #cdd6f4;
    line-height: 1.4;
}

QLabel#senderLabel {
    font-weight: bold;
    font-size: 11px;
}

QLabel#senderLabel_user {
    color: #b4befe;
}

QLabel#senderLabel_assistant {
    color: #a6e3a1;
}

QLabel#senderLabel_tool {
    color: #f38ba8;
}

/* ── Sistem Dashboard (Side Panel) ── */
QLabel#sectionTitle {
    font-weight: bold;
    font-size: 13px;
    color: #cdd6f4;
    text-transform: uppercase;
    letter-spacing: 1px;
}

QLabel#dbLabel {
    color: #a6adc8;
    font-size: 12px;
}

QLabel#dbValue {
    font-weight: bold;
    font-size: 14px;
    color: #89b4fa;
}

QProgressBar {
    border: 1px solid #313244;
    border-radius: 6px;
    background-color: #11111b;
    text-align: center;
    color: transparent;
    height: 12px;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #89b4fa, stop:1 #b4befe);
    border-radius: 5px;
}

/* ── Giriş Alanı (Input Bar) ── */
QFrame#inputContainer {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 20px;
}

QLineEdit#inputField {
    background-color: transparent;
    border: none;
    color: #cdd6f4;
    padding-left: 10px;
    font-size: 14px;
}

/* ── Butonlar ── */
QPushButton#actionButton {
    background-color: #313244;
    border: none;
    border-radius: 16px;
    width: 32px;
    height: 32px;
}

QPushButton#actionButton:hover {
    background-color: #45475a;
}

QPushButton#actionButton:pressed {
    background-color: #585b70;
}

QPushButton#micButton_active {
    background-color: #f38ba8;
    border-radius: 16px;
    width: 32px;
    height: 32px;
}

QPushButton#micButton_active:hover {
    background-color: #eba0ac;
}

QPushButton#winButton {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    color: #a6adc8;
    font-size: 12px;
    font-weight: bold;
    width: 24px;
    height: 24px;
}

QPushButton#winButton:hover {
    background-color: #313244;
    color: #cdd6f4;
}

QPushButton#winButton_close:hover {
    background-color: #f38ba8;
    color: #11111b;
}

/* ── Scrollbar Özelleştirme ── */
QScrollBar:vertical {
    border: none;
    background: #11111b;
    width: 8px;
    margin: 0px 0 0px 0;
}

QScrollBar::handle:vertical {
    background: #313244;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #45475a;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""
