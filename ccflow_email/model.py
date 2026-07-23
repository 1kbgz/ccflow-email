from ccflow import BaseModel
from pydantic import Field, field_validator, model_validator

__all__ = (
    "SMTP",
    "Attachment",
    "Email",
    "Message",
)


class Message(BaseModel):
    content: str | None = Field(default=None, description="HTML content of the email")
    subject: str | None = Field(default=None, description="Subject of the email")
    from_: tuple[str, str] | str | None = Field(default=None, description="Sender email address")
    to_: tuple[str, str] | str | None = Field(default=None, description="Recipient email address")
    cc: tuple[str, str] | str | None = Field(default=None, description="CC email address")
    bcc: tuple[str, str] | str | None = Field(default=None, description="BCC email address")

    @field_validator("from_")
    @classmethod
    def _validate_from(cls, v):
        # If tuple, must be (name, email)
        if isinstance(v, tuple):
            if len(v) != 2:
                raise ValueError("from_ tuple must be (name, email)")
            if not v[0]:
                return v[1]
        return v

    @field_validator("to_")
    @classmethod
    def _validate_to(cls, v):
        # If tuple, must be (name, email)
        if isinstance(v, tuple):
            if len(v) != 2:
                raise ValueError("to_ tuple must be (name, email)")
            if not v[0]:
                return v[1]
        return v

    @field_validator("cc")
    @classmethod
    def _validate_cc(cls, v):
        # If tuple, must be (name, email)
        if isinstance(v, tuple):
            if len(v) != 2:
                raise ValueError("cc tuple must be (name, email)")
            if not v[0]:
                return v[1]
        return v

    @field_validator("bcc")
    @classmethod
    def _validate_bcc(cls, v):
        # If tuple, must be (name, email)
        if isinstance(v, tuple):
            if len(v) != 2:
                raise ValueError("bcc tuple must be (name, email)")
            if not v[0]:
                return v[1]
        return v


class SMTP(BaseModel):
    host: str = Field(..., description="SMTP server host")
    port: int | None = Field(default=25, description="SMTP server port")
    user: str | None = Field(default=None, description="SMTP server username")
    password: str | None = Field(default=None, description="SMTP server password")
    tls: bool | None = Field(default=False, description="Use TLS for SMTP connection")
    ssl: bool | None = Field(default=False, description="Use SSL for SMTP connection")
    timeout: int | None = Field(default=30, description="Timeout for SMTP connection in seconds")


class Attachment(BaseModel):
    filename: str = Field(..., description="Name of the attachment file")
    content_disposition: str = Field(default="attachment", description="Content disposition of the attachment")
    data: bytes = Field(..., description="Binary data of the attachment")


class Email(BaseModel):
    message: Message = Field(description="Email message details")
    smtp: SMTP = Field(description="SMTP server configuration")
    attachments: list[Attachment] | None = Field(default_factory=list, description="List of email attachments")

    @model_validator(mode="after")
    def _validate_from(self):
        if not self.message.from_ and not self.smtp.user:
            raise ValueError("Either message.from_ or smtp.user must be set")
        if not self.message.from_:
            self.message.from_ = self.smtp.user
        if not self.smtp.user:
            self.smtp.user = self.message.from_[1] if isinstance(self.message.from_, tuple) else self.message.from_
        return self

    def send(self, to: str | list[str] | None = None, render: dict | None = None):
        # NOTE: defer import
        from emails import Message as EmailMessage

        # validate to
        if not to and not self.message.to_:
            # send back to from_
            to = self.message.from_
        elif not to:
            to = self.message.to_

        msg = EmailMessage(
            html=self.message.content,
            subject=self.message.subject,
            mail_from=self.message.from_,
            mail_to=to,
            cc=self.message.cc,
            bcc=self.message.bcc,
        )

        for attachment in self.attachments:
            msg.attach(filename=attachment.filename, content_disposition=attachment.content_disposition, data=attachment.data)

        smtp_config = self.smtp.model_dump(exclude_unset=True, exclude_none=True, exclude=["type_"])
        smtp_config["fail_silently"] = False
        response = msg.send(to=to, render=render or {}, smtp=smtp_config)
        return response
