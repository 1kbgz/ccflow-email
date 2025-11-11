from os import environ

import pytest

from ccflow_email import SMTP, Attachment, Message


@pytest.fixture
def smtp():
    try:
        return SMTP(
            user=environ["SMTP_USER"],
            password=environ["SMTP_PASSWORD"],
            host=environ["SMTP_HOST"],
            port=587,
            tls=True,
        )
    except KeyError:
        pytest.skip("SMTP credentials not set in environment variables")


@pytest.fixture
def smtp_or_dummy():
    try:
        return SMTP(
            user=environ["SMTP_USER"],
            password=environ["SMTP_PASSWORD"],
            host=environ["SMTP_HOST"],
            port=587,
            tls=True,
        )
    except KeyError:
        return SMTP(
            user="dummy_user",
            password="dummy_password",
            host="smtp.notareal.domain",
            port=587,
            tls=True,
        )


@pytest.fixture
def attachment():
    # TODO text, binary ,etc
    return Attachment(
        filename="test.txt",
        data=b"Hello, this is a test attachment.",
    )


@pytest.fixture
def message():
    return Message(
        content="This is a test email sent from ccflow_email.",
        subject="Test Email",
        mail_from=environ.get("SMTP_USER", "blerg"),
    )
