import imaplib
import email
import os
import re
from django.conf import settings
import logging

logger = logging.getLogger("payment_inbox")

class PaymentInbox:
    def __init__(self):
        self.host = os.environ.get('EMAIL_INBOX_IMAP_HOST', 'imap.gmail.com')
        self.username = getattr(settings, 'PAYMENT_INBOX_USERNAME', None) or os.environ.get('EMAIL_INBOX_USERNAME', 'kingfoodca@gmail.com')
        self.password = getattr(settings, 'PAYMENT_INBOX_PASSWORD', None) or os.environ.get('EMAIL_INBOX_PASSWORD', 'jmwr jxhb rgnt npbq')
        self.mailbox = os.environ.get('EMAIL_INBOX_MAILBOX', 'INBOX')

    def fetch_recent(self, from_email: str, from_name: str = ""):
        logger.info(f"Fetching recent emails for: {from_email}")
        results = []

        try:
            if not self.password:
                logger.error("PAYMENT_INBOX_PASSWORD not set!")
                return results

            M = imaplib.IMAP4_SSL(self.host)
            M.login(self.username, self.password)
            logger.info(f"Logged in as {self.username}")
            M.select(self.mailbox)
            typ, data = M.search(None, 'ALL')
            if typ != 'OK':
                logger.error("Failed to search mailbox")
                M.logout()
                return results

            ids = data[0].split()[-30:][::-1]  # آخرین ۳۰ ایمیل
            logger.info(f"Found {len(ids)} emails in mailbox")

            for msg_id in ids:
                typ, msg_data = M.fetch(msg_id, '(RFC822)')
                if typ != 'OK':
                    continue
                msg = email.message_from_bytes(msg_data[0][1])
                body = ''
                html = ''
                if msg.is_multipart():
                    for part in msg.walk():
                        ct = part.get_content_type()
                        if ct == 'text/plain':
                            try: body += part.get_payload(decode=True).decode(errors='ignore')
                            except: pass
                        if ct == 'text/html':
                            try: html += part.get_payload(decode=True).decode(errors='ignore')
                            except: pass
                else:
                    try: body = msg.get_payload(decode=True).decode(errors='ignore')
                    except: body = str(msg.get_payload())

                if html:
                    text = re.sub('<[^<]+?>', ' ', html)
                    body = (body + ' ' + text).strip()
                body = body.replace('\xa0', ' ')

                from_header = msg.get('From') or ''
                m = re.search(r'[A-Za-z0-9_.+-]+@[A-Za-z0-9_.+-]+', from_header)
                from_addr = (m.group(0) if m else '').lower()
                logger.info(f"Email from: {from_addr}")

                # فقط ایمیل کاربر
                if from_email.lower() != from_addr:
                    logger.info("Skipped: Not from user email")
                    continue

                # بررسی شماره رفرنس
# فقط دنبال Reference Number باشه
                ref_match = re.search(
                    r'Reference\s+Number\s*[:#\-]?\s*([A-Za-z0-9]{4,})',
                    body,
                    re.IGNORECASE | re.DOTALL
                )
                reference = ref_match.group(1) if ref_match else ''
                if not reference:
                    # ایمیل بدون Reference Number => رد کن و برو سراغ بعدی
                    logger.info("No Reference Number found in this email, skipped")
                    continue



                # بررسی Amount
                amount_match = re.search(r'Amount\s*[:\-]?\s*(?:CAD)?\s*\$?\s*(\d+(?:[\.,]\d{2})?)', body, re.IGNORECASE)
                amount = 0.0
                if amount_match:
                    amt = amount_match.group(1).replace(',', '.')
                    try: amount = float(amt)
                    except: amount = 0.0

                logger.info(f"Found email - Reference: {reference} | Amount: {amount}")
                results.append({'amount': amount, 'reference': reference})

            M.logout()
        except Exception as e:
            logger.exception(f"Error fetching emails: {str(e)}")
        logger.info(f"Total valid payment emails found: {len(results)}")
        logger.info(f"From: {from_addr}, Subject: {msg.get('Subject')}, Reference: {reference}")

        return results

payment_inbox = PaymentInbox()
