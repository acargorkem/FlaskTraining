"""
libs.mailgun

Uses requests.post() to send mail with mailgun.
MAILGUN_API_KEY and MAILGUN_DOMAIN called from `.env`` file.
To use your MAILGUN_API_KEY and MAILGUN_DOMAIN please check `.env example` file.
"""

import os
from typing import List
from requests import Response, post
from libs.strings import get_text


class Mailgun:
    MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY")
    MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN")
    FROM_TITLE = "Stores REST API"
    FROM_EMAIL = "mailgun@sandbox085b59febc2f4799894ea0d9310f4bbc.mailgun.org"

    @classmethod
    def send_email(cls, email_to: List[str], subject: str, text: str, html: str) -> Response:
        if cls.MAILGUN_API_KEY is None:
            raise MailGunException(get_text("mailgun_failed_load_api_key"))

        if cls.MAILGUN_DOMAIN is None:
            raise MailGunException(get_text("mailgun_failed_load_domain"))

        response = post(
            f"http://api.mailgun.net/v3/{cls.MAILGUN_DOMAIN}/messages",
            auth=("api", cls.MAILGUN_API_KEY),
            data={
                "from": f"{cls.FROM_TITLE} <{cls.FROM_EMAIL}>",
                "to": email_to,
                "subject": subject,
                "text": text,
                "html": html
            },
            timeout=2
        )
        if response.status_code != 200:
            raise MailGunException(get_text("mailgun_error_sending_email"))

        return response


class MailGunException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
