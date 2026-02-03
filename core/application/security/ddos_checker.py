from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.utils import timezone
from datetime import timedelta
from core.infrastructure.email.alerts import email_alert_sender
from django.conf import settings

class DDOSChecker:

    THRESHOLD = 3000              # 3000 request / 3 min
    WINDOW_MINUTES = 3
    LOCKDOWN_TIME = 7200          # 2 hours

    def check(self, request):
        log = cache.get('request_log', {
            'timestamps': [],
            'locked': False,
            'alert_sent': False
        })

        now = timezone.now()

        # پاک‌سازی timestamp های قدیمی
        log['timestamps'] = [
            t for t in log['timestamps']
            if now - t < timedelta(minutes=self.WINDOW_MINUTES)
        ]
        log['timestamps'].append(now)

        # اگر هنوز لاک نشده و از حد گذشتیم
        if len(log['timestamps']) > self.THRESHOLD and not log['locked']:

            log['locked'] = True
            log['alert_sent'] = True

            cache.set('site_locked', True, self.LOCKDOWN_TIME)
            cache.set('request_log', log, self.LOCKDOWN_TIME)

            subject = "🚨 DDOS Protection Triggered"
            message = (
                f"Time: {now}\n"
                f"Requests in 3 minutes: {len(log['timestamps'])}\n"
                f"Lockdown activated for 2 hours."
            )

            # === ارسال هشدار (ایمیل) ===
            email_alert_sender.send(subject, message)


        # ذخیره مجدد Log
        cache.set('request_log', log, self.LOCKDOWN_TIME)

        # اگر سایت داخل حالت LOCK است → ورود فقط برای ادمین
        if log.get('locked'):
            user = getattr(request, 'user', None)
            if not (user and (user.is_staff or user.is_superuser)):
                return HttpResponseForbidden("""
                    <h3>🚫 Site Temporarily Locked</h3>
                    <p>The site is currently under protection due unusal Terrafic.</p>
                """)

        return None

ddos_checker = DDOSChecker()
