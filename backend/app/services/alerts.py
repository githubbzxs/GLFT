from __future__ import annotations

import smtplib
from email.message import EmailMessage

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import models


async def create_alert(session: AsyncSession, level: str, message: str) -> None:
    session.add(models.Alert(level=level, message=message))
    await session.commit()


def send_email_alert(subject: str, body: str) -> None:
    settings = get_settings()
    if not settings.smtp_host or not settings.alert_email_to:
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_user or "glft-alert"
    msg["To"] = settings.alert_email_to
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_tls:
            server.starttls()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
