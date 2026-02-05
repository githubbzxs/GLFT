from __future__ import annotations

import smtplib
from email.message import EmailMessage

from sqlalchemy.ext.asyncio import AsyncSession

from dataclasses import dataclass

from app.core.config import get_settings
from app.db import models


@dataclass
class AlertConfig:
    alert_email_to: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_tls: bool


async def create_alert(session: AsyncSession, level: str, message: str) -> None:
    session.add(models.Alert(level=level, message=message))
    await session.commit()


def send_email_alert(subject: str, body: str, config: AlertConfig | None = None) -> None:
    settings = get_settings()
    if config:
        smtp_host = config.smtp_host
        email_to = config.alert_email_to
        smtp_port = config.smtp_port
        smtp_user = config.smtp_user
        smtp_password = config.smtp_password
        smtp_tls = config.smtp_tls
    else:
        smtp_host = settings.smtp_host
        email_to = settings.alert_email_to
        smtp_port = settings.smtp_port
        smtp_user = settings.smtp_user
        smtp_password = settings.smtp_password
        smtp_tls = settings.smtp_tls

    if not smtp_host or not email_to:
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_user or "glft-alert"
    msg["To"] = email_to
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if smtp_tls:
            server.starttls()
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
        server.send_message(msg)
