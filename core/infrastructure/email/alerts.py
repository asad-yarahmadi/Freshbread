from django.core.mail import send_mail, mail_admins

class EmailAlertSender:

    ADMINS = [
        'order.freshbread911@gmail.com',
        'programing.mahdi@gmail.com',
        'parsafahhim1390@gmail.com',
    ]

    def send(self, subject, message):
        try:
            send_mail(
                subject,
                message,
                'order.freshbread911@gmail.com',
                self.ADMINS,
                fail_silently=False,
            )
        except Exception:
            pass

        try:
            mail_admins(subject, message, fail_silently=True)
        except Exception:
            pass

email_alert_sender = EmailAlertSender()
