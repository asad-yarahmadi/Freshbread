import os
from typing import Any

from django.conf import settings
from django.utils.html import strip_tags
from zeep import Client


class EmailSender:
    def _normalize_recipients(self, to):
        if to is None:
            return []

        if isinstance(to, str):
            recipients = [to]
        elif isinstance(to, (list, tuple, set)):
            recipients = list(to)
        else:
            recipients = [to]

        cleaned = []
        for item in recipients:
            value = str(item).strip()
            if value:
                cleaned.append(value)

        return cleaned[:100]

    def _parse_response(self, response: Any):
        if isinstance(response, dict):
            return response

        if isinstance(response, (list, tuple)):
            return {"result": list(response)}

        if hasattr(response, "SendSimpleSMSResult"):
            result = getattr(response, "SendSimpleSMSResult")
            return {"result": result}

        if hasattr(response, "SendSimpleSMSResult") is False and hasattr(response, "sendSimpleSMSResult"):
            result = getattr(response, "sendSimpleSMSResult")
            return {"result": result}

        return {"raw": str(response)}

    def send(self, *, subject=None, message="", to=None, html_template=None, context=None, html_message=None, title=None, cta_text=None, action_url=None, wrap=True):
        recipients = self._normalize_recipients(to)
        if not recipients:
            raise ValueError("No SMS recipient provided.")

        sms_text = message or ""
        if not sms_text and html_message:
            sms_text = strip_tags(html_message)

        if subject and not sms_text:
            sms_text = str(subject)

        if not sms_text.strip():
            raise ValueError("SMS text cannot be empty.")

        url = getattr(settings, "MELI_SMS_API_URL", None) or os.getenv("MELI_SMS_API_URL")
        username = getattr(settings, "MELI_SMS_USERNAME", None) or os.getenv("MELI_SMS_USERNAME")
        password = getattr(settings, "MELI_SMS_PASSWORD", None) or os.getenv("MELI_SMS_PASSWORD")
        sender = getattr(settings, "MELI_SMS_FROM", None) or os.getenv("MELI_SMS_FROM")
        is_flash = getattr(settings, "MELI_SMS_IS_FLASH", False)

        if not all([url, username, password, sender]):
            raise RuntimeError("Meli SMS settings are incomplete.")

        wsdl_url = url if url.endswith("?wsdl") else f"{url}?wsdl" if "?wsdl" not in url else url
        client = Client(wsdl_url)
        response = client.service.SendSimpleSMS(
            username=username,
            password=password,
            to=recipients,
            from_=sender,
            text=sms_text,
            isflash=bool(is_flash),
        )
        return self._parse_response(response)


email_sender = EmailSender()