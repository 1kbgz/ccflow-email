from os import environ
from unittest.mock import MagicMock, patch

import pytest

from ccflow_email import SMTP, Attachment, Email, Message


class TestEmail:
    def test_email_creation(self):
        email = Email(
            message=Message(content="<p>Hello, World!</p>", subject="Test Email", from_=("Test", "test@example.com")),
            smtp=SMTP(host="smtp.example.com", port=587, user="user", password="pass", tls=True),
            attachments=[Attachment(filename="test.txt", content_disposition="attachment", data=b"Test file content")],
        )
        assert email.message.subject == "Test Email"
        assert email.smtp.host == "smtp.example.com"
        assert email.attachments is not None
        assert email.attachments[0].filename == "test.txt"

    @pytest.mark.skipif(not environ.get("SMTP_HOST"), reason="SMTP server not configured")
    def test_email_send(self):
        email = Email(
            message=Message(
                content="<p>Hello, World!</p>",
                subject="Test Email",
                from_=("Test", environ["SMTP_USER"]),
            ),
            smtp=SMTP(
                host=environ["SMTP_HOST"],
                port=587,
                user=environ["SMTP_USER"],
                password=environ["SMTP_PASSWORD"],
                tls=True,
            ),
            attachments=[Attachment(filename="test.txt", content_disposition="attachment", data=b"Test file content")],
        )
        response = email.send(to=environ.get("SMTP_USER", "recipient@example.com"))
        assert response.status_code == 250

    def test_email(self):
        smtp = SMTP(
            user="user",
            password="password",
            host="host",
            port=587,
            tls=True,
        )

        attachment = Attachment(
            filename="test.txt",
            data=b"Hello, this is a test attachment.",
        )

        message = Message(
            content="This is a test email sent from ccflow_email.",
            subject="Test Email",
            from_="user",
        )

        email = Email(
            attachments=[attachment],
            smtp=smtp,
            message=message,
        )

        assert email.smtp == smtp
        assert email.message == message
        assert email.attachments == [attachment]

        with patch("emails.message.MessageSendMixin.send") as mock_sendmail:
            mock_sendmail.return_value = MagicMock(success=True, status_text=b"Message received")
            response = email.send("user")

        assert response.success is True
        assert response.status_text == b"Message received"

    def test_send_without_attachments(self):
        email = Email(
            message=Message(content="Hello", subject="Test", from_="sender@example.com"),
            smtp=SMTP(host="smtp.example.com"),
            attachments=None,
        )
        recipient = ("Recipient", "recipient@example.com")
        with patch("emails.Message") as message:
            response = email.send(to=recipient)
        message.assert_called_once_with(html="Hello", subject="Test", mail_from="sender@example.com", mail_to=recipient, cc=None, bcc=None)
        message.return_value.attach.assert_not_called()
        assert response is message.return_value.send.return_value
        assert "type_" not in message.return_value.send.call_args.kwargs["smtp"]
