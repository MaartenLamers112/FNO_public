"""Provider-onafhankelijke e-mailservice voor FNO."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from flask import current_app


class MailService:
    """Verstuur eenvoudige e-mails via geconfigureerde SMTP."""

    def send_text(
        self,
        *,
        recipient: str,
        subject: str,
        body: str,
    ) -> None:
        """Verstuur een platte tekstmail."""

        if current_app.config["MAIL_SUPPRESS_SEND"]:
            return

        server = current_app.config["MAIL_SERVER"]
        sender = current_app.config["MAIL_FROM"]

        if not server or not sender:
            raise RuntimeError("SMTP is niet volledig geconfigureerd.")

        message = EmailMessage()
        message["From"] = sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        port = current_app.config["MAIL_PORT"]
        use_ssl = current_app.config["MAIL_USE_SSL"]
        use_tls = current_app.config["MAIL_USE_TLS"]
        username = current_app.config["MAIL_USERNAME"]
        password = current_app.config["MAIL_PASSWORD"]

        smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP

        with smtp_class(server, port, timeout=10) as smtp:
            if use_tls and not use_ssl:
                smtp.starttls()

            if username:
                smtp.login(username, password or "")

            smtp.send_message(message)
