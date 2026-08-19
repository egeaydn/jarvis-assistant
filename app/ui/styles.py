"""
Phase v1.0 — High-Tech Sci-Fi Jarvis Stylesheet (QSS).

Tony Stark JARVIS stili holografik mavi/cyan neon tema.
Yumuşak parlamalar, ince teknolojik sınırlar ve tamamen arındırılmış emojiler.
"""

QSS = """
/* ── Genel Pencere Ayarları ── */
QMainWindow {
    background-color: #030712;
}

QWidget {
    color: #e0f2fe;
    font-family: "Consolas", "Courier New", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ── Panel Tasarımları ── */
QFrame#sidePanel {
    background-color: #070e1b;
    border-right: 1px solid #1e293b;
    border-radius: 0px;
}

QFrame#mainArea {
    background-color: #030712;
}

/* ── Başlık Barı (Title Bar) ── */
QFrame#titleBar {
    background-color: #030712;
    border-bottom: 1px solid #0f172a;
}

QLabel#titleLabel {
    font-weight: bold;
    font-size: 13px;
    color: #38bdf8;
    letter-spacing: 1px;
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
    background-color: #0f172a;
    border-radius: 6px;
    border: 1px solid #1e293b;
    margin-left: 50px;
    margin-right: 10px;
}

QFrame#msgCard_assistant {
    background-color: #0b1329;
    border-radius: 6px;
    border: 1px solid #334155;
    margin-left: 10px;
    margin-right: 50px;
}

QFrame#msgCard_tool {
    background-color: #020617;
    border-radius: 4px;
    border: 1px dashed #0ea5e9;
    margin-left: 20px;
    margin-right: 20px;
}

QLabel#msgText {
    color: #f0f9ff;
    line-height: 1.5;
}

QLabel#senderLabel {
    font-weight: bold;
    font-size: 11px;
    letter-spacing: 1px;
}

QLabel#senderLabel_user {
    color: #38bdf8;
}

QLabel#senderLabel_assistant {
    color: #06b6d4;
}

QLabel#senderLabel_tool {
    color: #0ea5e9;
}

/* ── Sistem Dashboard (Side Panel) ── */
QLabel#sectionTitle {
    font-weight: bold;
    font-size: 12px;
    color: #38bdf8;
    text-transform: uppercase;
    letter-spacing: 2px;
}

QLabel#dbLabel {
    color: #94a3b8;
    font-size: 11px;
}

QLabel#dbValue {
    font-weight: bold;
    font-size: 13px;
    color: #00f0ff;
}

QProgressBar {
    border: 1px solid #1e293b;
    border-radius: 3px;
    background-color: #020617;
    text-align: center;
    color: transparent;
    height: 6px;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #00f0ff);
    border-radius: 2px;
}

/* ── Giriş Alanı (Input Bar) ── */
QFrame#inputContainer {
    background-color: #070e1b;
    border: 1px solid #1e293b;
    border-radius: 6px;
}

QFrame#inputContainer:focus-within {
    border: 1px solid #00f0ff;
}

QLineEdit#inputField {
    background-color: transparent;
    border: none;
    color: #f0f9ff;
    padding-left: 5px;
    font-size: 13px;
}

/* ── Butonlar ── */
QPushButton#actionButton {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 4px;
    width: 32px;
    height: 32px;
    color: #38bdf8;
    font-weight: bold;
}

QPushButton#actionButton:hover {
    background-color: #1e293b;
    border: 1px solid #38bdf8;
    color: #00f0ff;
}

QPushButton#actionButton:pressed {
    background-color: #334155;
}

QPushButton#micButton_active {
    background-color: #083344;
    border: 1px solid #06b6d4;
    border-radius: 4px;
    width: 32px;
    height: 32px;
    color: #22d3ee;
}

QPushButton#micButton_active:hover {
    background-color: #155e75;
}

QPushButton#winButton {
    background-color: transparent;
    border: none;
    border-radius: 2px;
    color: #64748b;
    font-size: 11px;
    font-weight: bold;
    width: 24px;
    height: 24px;
}

QPushButton#winButton:hover {
    background-color: #0f172a;
    color: #38bdf8;
}

QPushButton#winButton_close:hover {
    background-color: #7f1d1d;
    color: #fca5a5;
}

/* ── Scrollbar Özelleştirme ── */
QScrollBar:vertical {
    border: none;
    background: #020617;
    width: 6px;
}

QScrollBar::handle:vertical {
    background: #1e293b;
    min-height: 20px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #334155;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""
