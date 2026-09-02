"""
Phase 10 — E-posta Gönderme.

send_email: SMTP üzerinden e-posta gönderir. .env dosyasından SMTP_HOST, SMTP_PORT,
SMTP_USER, SMTP_PASSWORD okunur (Gmail için "Uygulama Şifresi" kullanılmalı).

⚠️ Güvenlik onayı gerektiren işlem (agent.py tarafından kontrol edilir).
"""

import os
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

_MAX_ATTACHMENT_MB = 20


def send_email(to: str, subject: str, body: str, attachments: Optional[List[str]] = None) -> str:
    """
    SMTP üzerinden e-posta gönderir.

    Gerekli .env değişkenleri: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD.
    """
    if not to or "@" not in to:
        raise ValueError(f"Geçersiz alıcı adresi: '{to}'")
    if not subject or not subject.strip():
        raise ValueError("Konu boş olamaz.")
    if not body or not body.strip():
        raise ValueError("Gövde boş olamaz.")

    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")

    if not all([host, port, user, password]):
        raise EnvironmentError(
            "SMTP ayarları eksik. .env dosyasına SMTP_HOST, SMTP_PORT, SMTP_USER, "
            "SMTP_PASSWORD değerlerini ekleyin."
        )

    attachment_paths = _validate_attachments(attachments or [])

    message = MIMEMultipart()
    message["From"] = user
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain", "utf-8"))

    for path in attachment_paths:
        with path.open("rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{path.name}"')
        message.attach(part)

    try:
        with smtplib.SMTP(host, int(port), timeout=15) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, [to], message.as_string())
    except smtplib.SMTPException as exc:
        raise RuntimeError(f"E-posta gönderilemedi: {exc}") from exc
    except OSError as exc:
        raise RuntimeError(f"SMTP sunucusuna bağlanılamadı: {exc}") from exc

    return f"E-posta '{to}' adresine gönderildi: '{subject}'"


def _validate_attachments(attachments: List[str]) -> List[Path]:
    """Ek dosyaların var olduğunu ve boyutunun makul olduğunu doğrular."""
    validated: List[Path] = []
    for raw_path in attachments:
        path = Path(raw_path)
        if not path.exists():
            raise FileNotFoundError(f"Ek dosya bulunamadı: '{raw_path}'")
        if not path.is_file():
            raise ValueError(f"Ek olarak yalnızca dosya eklenebilir: '{raw_path}'")
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > _MAX_ATTACHMENT_MB:
            raise ValueError(f"'{raw_path}' çok büyük ({size_mb:.1f} MB). Maksimum {_MAX_ATTACHMENT_MB} MB.")
        validated.append(path)
    return validated
