from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
import time
from core.interfaces.http.decorators import admin_login_protect
from core.infrastructure.models import SiteLock, SecurityEventLog, SuspiciousActivity, SuspiciousEvent


@admin_login_protect
def admin_security(request):
    site_lock = SiteLock.get_solo()

    if request.method == "POST":
        action = request.POST.get("action")
        reason = (request.POST.get("reason") or "").strip()
        start = request.POST.get("schedule_start") or ""
        end = request.POST.get("schedule_end") or ""

        # =========================================================
        # SITE LOCK
        # =========================================================

        if action == "lock":
            if site_lock.is_locked is True:
                messages.info(request, "Please unlock site first!")

            if site_lock.schedule_start or site_lock.schedule_end:
                site_lock.schedule_start = None
                site_lock.schedule_end = None
                site_lock.save()

            site_lock.is_locked = True

            if reason:
                site_lock.reason = reason

            site_lock.updated_by = request.user
            site_lock.save()

            cache.set(
                "site_lock_state",
                {
                    "is_locked": True,
                    "reason": site_lock.reason or "",
                },
                60,
            )

            messages.success(request, "Site locked.")

            try:
                SecurityEventLog.objects.create(
                    event_type=SecurityEventLog.EVENT_LOCK,
                    actor=request.user,
                    message=(
                        reason
                        or "Some thing is happening. We will notify you by "
                           "Social media or Email. Thanks!"
                    ),
                )
            except Exception:
                pass

            try:
                User = get_user_model()

                emails = list(
                    User.objects.filter(
                        is_active=True,
                        is_staff=True,
                    )
                    | User.objects.filter(
                        is_superuser=True,
                    )
                )

                to_list = [u.email for u in emails if u.email]

                if to_list:
                    send_mail(
                        subject="Site locked - Kingfood",
                        message=(
                            f"Dear Admins, Wish everything is fine. "
                            f"Admin {request.user.username} locked the site. "
                            f"Reason: {reason or 'No reason given.'} "
                            f"Have a nice day! "
                            f"(Automaticly created by Kingfood_bckend)"
                        ),
                        from_email=getattr(
                            settings,
                            "DEFAULT_FROM_EMAIL",
                            None,
                        ),
                        recipient_list=to_list,
                        fail_silently=True,
                    )

            except Exception:
                pass

            return redirect("admin_security")

        # =========================================================
        # SITE UNLOCK
        # =========================================================

        if action == "unlock":
            site_lock.is_locked = False
            site_lock.reason = reason or "Manual unlock"
            site_lock.updated_by = request.user
            site_lock.save()

            cache.set(
                "site_lock_state",
                {
                    "is_locked": False,
                    "reason": "",
                },
                60,
            )

            cache.delete("site_locked")
            cache.delete("request_log")

            messages.success(
                request,
                "Site unlocked. DDoS protection cleared if active.",
            )

            try:
                SecurityEventLog.objects.create(
                    event_type=SecurityEventLog.EVENT_UNLOCK,
                    actor=request.user,
                    message=reason or "Manual unlock",
                )
            except Exception:
                pass

            return redirect("admin_security")

        # =========================================================
        # SCHEDULE
        # =========================================================

        if action == "schedule":
            if site_lock.schedule_start or site_lock.schedule_end:
                site_lock.schedule_start = None
                site_lock.schedule_end = None
                site_lock.save()

            try:
                schedule_start = (
                    datetime.fromisoformat(start)
                    if start
                    else None
                )

                schedule_end = (
                    datetime.fromisoformat(end)
                    if end
                    else None
                )

                if schedule_start and timezone.is_naive(schedule_start):
                    schedule_start = timezone.make_aware(
                        schedule_start,
                        timezone.get_default_timezone(),
                    )

                if schedule_end and timezone.is_naive(schedule_end):
                    schedule_end = timezone.make_aware(
                        schedule_end,
                        timezone.get_default_timezone(),
                    )

                if (
                    schedule_start
                    and schedule_end
                    and schedule_start >= schedule_end
                ):
                    messages.error(
                        request,
                        "Schedule start must be before end.",
                    )
                    return redirect("admin_security")

            except Exception:
                messages.error(
                    request,
                    "Invalid date format. Use YYYY-MM-DDTHH:MM",
                )
                return redirect("admin_security")

            site_lock.schedule_start = schedule_start
            site_lock.schedule_end = schedule_end

            if reason:
                site_lock.reason = reason

            site_lock.updated_by = request.user
            site_lock.save()

            cache.delete("site_lock_state")

            messages.success(
                request,
                "Schedule updated.",
            )

            try:
                if schedule_start and schedule_end:
                    event_type = SecurityEventLog.EVENT_LOCK
                    message = (
                        f"Site lock scheduled: "
                        f"{schedule_start} -> {schedule_end}."
                    )

                    if reason:
                        message += f" Reason: {reason}"

                else:
                    event_type = SecurityEventLog.EVENT_UNLOCK
                    message = "Scheduled site lock cleared."

                    if reason:
                        message += f" Reason: {reason}"

                SecurityEventLog.objects.create(
                    event_type=event_type,
                    actor=request.user,
                    message=message,
                )

            except Exception:
                pass

            return redirect("admin_security")

        # =========================================================
        # BLOCK SINGLE IP
        # =========================================================

        if action == "block_ip":
            aid = request.POST.get("activity_id")

            if aid:
                obj = SuspiciousActivity.objects.filter(
                    id=aid
                ).first()

                if obj:
                    obj.is_blocked = True

                    obj.save(
                        update_fields=[
                            "is_blocked",
                            "last_seen",
                        ]
                    )

                    cache.set(
                        f"ip_blocked:{obj.ip}",
                        True,
                        60,
                    )

                    messages.success(
                        request,
                        f"IP {obj.ip} blocked.",
                    )

                    try:
                        SecurityEventLog.objects.create(
                            event_type=SecurityEventLog.EVENT_LOCK,
                            actor=request.user,
                            message=f"IP blocked: {obj.ip}",
                        )
                    except Exception:
                        pass

            return redirect("admin_security")

        # =========================================================
        # UNBLOCK SINGLE IP
        # =========================================================

        if action == "unblock_ip":
            aid = request.POST.get("activity_id")

            if aid:
                obj = SuspiciousActivity.objects.filter(
                    id=aid
                ).first()

                if obj:
                    obj.is_blocked = False

                    obj.save(
                        update_fields=[
                            "is_blocked",
                            "last_seen",
                        ]
                    )

                    cache.set(
                        f"ip_blocked:{obj.ip}",
                        False,
                        60,
                    )

                    messages.success(
                        request,
                        f"IP {obj.ip} unblocked.",
                    )

                    try:
                        SecurityEventLog.objects.create(
                            event_type=SecurityEventLog.EVENT_UNLOCK,
                            actor=request.user,
                            message=f"IP unblocked: {obj.ip}",
                        )
                    except Exception:
                        pass

            return redirect("admin_security")

        # =========================================================
        # MUTE SINGLE IP
        # =========================================================

        if action == "mute_logs":
            aid = request.POST.get("activity_id")

            if aid:
                obj = SuspiciousActivity.objects.filter(
                    id=aid
                ).first()

                if obj:
                    obj.suppress_logging = True

                    obj.save(
                        update_fields=[
                            "suppress_logging",
                            "last_seen",
                        ]
                    )

                    messages.success(
                        request,
                        f"Logging muted for {obj.ip}.",
                    )

                    try:
                        SecurityEventLog.objects.create(
                            event_type=SecurityEventLog.EVENT_LOCK,
                            actor=request.user,
                            message=f"Logging muted for IP: {obj.ip}",
                        )
                    except Exception:
                        pass

            return redirect("admin_security")

        # =========================================================
        # UNMUTE SINGLE IP
        # =========================================================

        if action == "unmute_logs":
            aid = request.POST.get("activity_id")

            if aid:
                obj = SuspiciousActivity.objects.filter(
                    id=aid
                ).first()

                if obj:
                    obj.suppress_logging = False

                    obj.save(
                        update_fields=[
                            "suppress_logging",
                            "last_seen",
                        ]
                    )

                    messages.success(
                        request,
                        f"Logging unmuted for {obj.ip}.",
                    )

                    try:
                        SecurityEventLog.objects.create(
                            event_type=SecurityEventLog.EVENT_UNLOCK,
                            actor=request.user,
                            message=f"Logging unmuted for IP: {obj.ip}",
                        )
                    except Exception:
                        pass

            return redirect("admin_security")

        # =========================================================
        # MARK REVIEWED SINGLE IP
        # =========================================================

        if action == "mark_reviewed":
            aid = request.POST.get("activity_id")

            if aid:
                obj = SuspiciousActivity.objects.filter(
                    id=aid
                ).first()

                if obj:
                    obj.unread = False

                    obj.save(
                        update_fields=[
                            "unread",
                            "last_seen",
                        ]
                    )

                    try:
                        SecurityEventLog.objects.create(
                            event_type=SecurityEventLog.EVENT_UNLOCK,
                            actor=request.user,
                            message=f"IP marked as reviewed: {obj.ip}",
                        )
                    except Exception:
                        pass

            return redirect("admin_security")

        # =========================================================
        # BULK ACTION
        # =========================================================

        if action == "bulk_action":
            bulk_action = request.POST.get("bulk_action")
            selected_ids = request.POST.getlist("selected_ids")

            if not selected_ids:
                messages.warning(
                    request,
                    "No suspicious activities were selected.",
                )
                return redirect("admin_security")

            allowed_bulk_actions = {
                "mark_reviewed",
                "mute",
                "block",
                "delete_reports",
                "delete_ips",
            }

            if bulk_action not in allowed_bulk_actions:
                messages.error(
                    request,
                    "Invalid bulk action.",
                )
                return redirect("admin_security")

            activities = SuspiciousActivity.objects.filter(
                id__in=selected_ids,
                is_tracking=True,
            )

            if not activities.exists():
                messages.warning(
                    request,
                    "No valid suspicious activities were found.",
                )
                return redirect("admin_security")

            now = timezone.now()

            # -----------------------------------------------------
            # BULK MARK REVIEWED
            # -----------------------------------------------------

            if bulk_action == "mark_reviewed":

                count = 0

                for obj in activities:
                    obj.unread = False

                    obj.save(
                        update_fields=[
                            "unread",
                            "last_seen",
                        ]
                    )

                    count += 1

                    try:
                        SecurityEventLog.objects.create(
                            event_type=SecurityEventLog.EVENT_UNLOCK,
                            actor=request.user,
                            message=(
                                f"Bulk action: IP marked as reviewed: "
                                f"{obj.ip}"
                            ),
                        )
                    except Exception:
                        pass

                messages.success(
                    request,
                    f"{count} IP(s) marked as reviewed.",
                )

            # -----------------------------------------------------
            # BULK MUTE
            # -----------------------------------------------------

            elif bulk_action == "mute":

                count = 0

                for obj in activities:
                    obj.suppress_logging = True
                    obj.last_seen = now

                    obj.save(
                        update_fields=[
                            "suppress_logging",
                            "last_seen",
                        ]
                    )

                    count += 1

                    try:
                        SecurityEventLog.objects.create(
                            event_type=SecurityEventLog.EVENT_LOCK,
                            actor=request.user,
                            message=(
                                f"Bulk action: logging muted for IP: "
                                f"{obj.ip}"
                            ),
                        )
                    except Exception:
                        pass

                messages.success(
                    request,
                    f"{count} IP(s) muted.",
                )

            # -----------------------------------------------------
            # BULK BLOCK
            # -----------------------------------------------------

            elif bulk_action == "block":

                count = 0

                for obj in activities:
                    obj.is_blocked = True
                    obj.last_seen = now

                    obj.save(
                        update_fields=[
                            "is_blocked",
                            "last_seen",
                        ]
                    )

                    cache.set(
                        f"ip_blocked:{obj.ip}",
                        True,
                        60,
                    )

                    count += 1

                    try:
                        SecurityEventLog.objects.create(
                            event_type=SecurityEventLog.EVENT_LOCK,
                            actor=request.user,
                            message=(
                                f"Bulk action: IP blocked: "
                                f"{obj.ip}"
                            ),
                        )
                    except Exception:
                        pass

                messages.success(
                    request,
                    f"{count} IP(s) blocked.",
                )

            # -----------------------------------------------------
            # BULK DELETE REPORTS
            # -----------------------------------------------------

            elif bulk_action == "delete_reports":

                until_iso = request.session.get(
                    "report_delete_verified_until"
                )

                allowed = False

                if until_iso:
                    try:
                        until = timezone.datetime.fromisoformat(
                            until_iso
                        )

                        if timezone.is_naive(until):
                            until = timezone.make_aware(
                                until,
                                timezone.get_default_timezone(),
                            )

                        allowed = timezone.now() <= until

                    except Exception:
                        allowed = False

                if not allowed:
                    messages.error(
                        request,
                        "Verification required to delete reports.",
                    )
                    return redirect("admin_security")

                count = 0

                for obj in activities:

                    deleted_count, _ = obj.events.all().delete()

                    count += 1

                    try:
                        SecurityEventLog.objects.create(
                            event_type=SecurityEventLog.EVENT_LOCK,
                            actor=request.user,
                            message=(
                                f"Bulk action: reports cleared for IP: "
                                f"{obj.ip}. "
                                f"Deleted events: {deleted_count}"
                            ),
                        )
                    except Exception:
                        pass

                messages.success(
                    request,
                    f"Reports cleared for {count} IP(s).",
                )

            # -----------------------------------------------------
            # BULK DELETE IP RECORDS
            # -----------------------------------------------------

            elif bulk_action == "delete_ips":

                until_iso = request.session.get(
                    "report_delete_verified_until"
                )

                allowed = False

                if until_iso:
                    try:
                        until = timezone.datetime.fromisoformat(
                            until_iso
                        )

                        if timezone.is_naive(until):
                            until = timezone.make_aware(
                                until,
                                timezone.get_default_timezone(),
                            )

                        allowed = timezone.now() <= until

                    except Exception:
                        allowed = False

                if not allowed:
                    messages.error(
                        request,
                        "Verification required to delete IP records.",
                    )
                    return redirect("admin_security")

                count = 0

                for obj in activities:

                    ip = obj.ip
                    activity_id = obj.id

                    # Log BEFORE deleting the database record.
                    try:
                        SecurityEventLog.objects.create(
                            event_type=SecurityEventLog.EVENT_LOCK,
                            actor=request.user,
                            message=(
                                f"Bulk action: IP record deleted: "
                                f"{ip} "
                                f"(activity_id={activity_id})"
                            ),
                        )
                    except Exception:
                        pass

                    obj.delete()

                    cache.set(
                        f"ip_blocked:{ip}",
                        False,
                        60,
                    )

                    count += 1

                messages.success(
                    request,
                    f"{count} IP record(s) deleted.",
                )

            return redirect("admin_security")

        # =========================================================
        # REQUEST DELETE VERIFICATION
        # =========================================================

        if action == "request_delete_verify":
            import secrets

            code = f"{secrets.randbelow(1000000):06d}"

            request.session["report_delete_verify_code"] = code

            request.session["report_delete_verify_expires"] = (
                timezone.now().isoformat()
            )

            request.session["report_delete_attempts"] = 0

            session_code = request.session.get(
                "report_delete_verify_code"
            )

            print(session_code)

            try:
                if request.user.email:
                    send_mail(
                        subject=(
                            "Verification code for deleting reports - "
                            "Kingfood"
                        ),
                        message=(
                            f"Your verification code is: {code}"
                        ),
                        from_email=getattr(
                            settings,
                            "DEFAULT_FROM_EMAIL",
                            None,
                        ),
                        recipient_list=[
                            request.user.email
                        ],
                        fail_silently=True,
                    )
            except Exception:
                pass

            messages.success(
                request,
                "Verification code sent to your email.",
            )

            return redirect("admin_security")

        # =========================================================
        # CONFIRM DELETE VERIFICATION
        # =========================================================

        if action == "confirm_delete_verify":
            code_in = (
                request.POST.get("verify_code") or ""
            ).strip()

            code_saved = request.session.get(
                "report_delete_verify_code"
            )

            attempts = int(
                request.session.get(
                    "report_delete_attempts",
                    0,
                )
            )

            ok = bool(
                code_saved
                and code_in
                and code_in == code_saved
            )

            if ok:
                until = timezone.now() + timezone.timedelta(
                    minutes=4
                )

                request.session[
                    "report_delete_verified_until"
                ] = until.isoformat()

                request.session.pop(
                    "report_delete_verify_code",
                    None,
                )

                request.session[
                    "report_delete_attempts"
                ] = 0

                messages.success(
                    request,
                    "Verification successful. "
                    "You can delete reports for 4 minutes.",
                )

            else:
                attempts += 1

                request.session[
                    "report_delete_attempts"
                ] = attempts

                messages.error(
                    request,
                    "Invalid code.",
                )

                if attempts >= 2:
                    try:
                        User = get_user_model()

                        emails = list(
                            User.objects.filter(
                                is_active=True,
                                is_staff=True,
                            )
                            | User.objects.filter(
                                is_superuser=True,
                            )
                        )

                        to_list = [
                            u.email
                            for u in emails
                            if u.email
                        ]

                        if to_list:
                            send_mail(
                                subject=(
                                    "Admin verification failures - "
                                    "Kingfood"
                                ),
                                message=(
                                    f"Dear admins, Wish you are good, "
                                    f"Admin {request.user.username} "
                                    f"entered wrong verification code "
                                    f"twice. Have nice day. "
                                    f"(Automaticlly created by "
                                    f"Kingfood_bakend)"
                                ),
                                from_email=getattr(
                                    settings,
                                    "DEFAULT_FROM_EMAIL",
                                    None,
                                ),
                                recipient_list=to_list,
                                fail_silently=True,
                            )

                    except Exception:
                        pass

            return redirect("admin_security")

        # =========================================================
        # DELETE ALL REPORTS FOR ONE IP
        # =========================================================

        if action == "delete_reports":
            aid = request.POST.get("activity_id")

            until_iso = request.session.get(
                "report_delete_verified_until"
            )

            allowed = False

            if until_iso:
                try:
                    until = timezone.datetime.fromisoformat(
                        until_iso
                    )

                    if timezone.is_naive(until):
                        until = timezone.make_aware(
                            until,
                            timezone.get_default_timezone(),
                        )

                    allowed = timezone.now() <= until

                except Exception:
                    allowed = False

            if not allowed:
                messages.error(
                    request,
                    "Verification required to delete reports.",
                )
                return redirect("admin_security")

            if aid:
                obj = SuspiciousActivity.objects.filter(
                    id=aid
                ).first()

                if obj:
                    ip = obj.ip

                    deleted_count, _ = (
                        obj.events.all().delete()
                    )

                    try:
                        SecurityEventLog.objects.create(
                            event_type=SecurityEventLog.EVENT_LOCK,
                            actor=request.user,
                            message=(
                                f"Reports deleted for IP: {ip}. "
                                f"Deleted events: {deleted_count}"
                            ),
                        )
                    except Exception:
                        pass

                    messages.success(
                        request,
                        "All reports deleted for this IP.",
                    )

            return redirect("admin_security")

        # =========================================================
        # DELETE ONE REPORT EVENT
        # =========================================================

        if action == "delete_report_event":
            eid = request.POST.get("event_id")

            until_iso = request.session.get(
                "report_delete_verified_until"
            )

            allowed = False

            if until_iso:
                try:
                    until = timezone.datetime.fromisoformat(
                        until_iso
                    )

                    if timezone.is_naive(until):
                        until = timezone.make_aware(
                            until,
                            timezone.get_default_timezone(),
                        )

                    allowed = timezone.now() <= until

                except Exception:
                    allowed = False

            if not allowed:
                messages.error(
                    request,
                    "Verification required to delete a report.",
                )
                return redirect("admin_security")

            if eid:
                event = SuspiciousEvent.objects.filter(
                    id=eid
                ).first()

                if event:
                    event_ip = (
                        event.activity.ip
                        if hasattr(event, "activity")
                        and event.activity
                        else None
                    )

                    event.delete()

                    try:
                        SecurityEventLog.objects.create(
                            event_type=SecurityEventLog.EVENT_LOCK,
                            actor=request.user,
                            message=(
                                f"Report event deleted"
                                + (
                                    f" for IP: {event_ip}"
                                    if event_ip
                                    else ""
                                )
                            ),
                        )
                    except Exception:
                        pass

                    messages.success(
                        request,
                        "Report deleted.",
                    )

            return redirect("admin_security")

        # =========================================================
        # DELETE ONE IP RECORD
        # =========================================================

        if action == "delete_ip_record":
            aid = request.POST.get("activity_id")

            until_iso = request.session.get(
                "report_delete_verified_until"
            )

            allowed = False

            if until_iso:
                try:
                    until = timezone.datetime.fromisoformat(
                        until_iso
                    )

                    if timezone.is_naive(until):
                        until = timezone.make_aware(
                            until,
                            timezone.get_default_timezone(),
                        )

                    allowed = timezone.now() <= until

                except Exception:
                    allowed = False

            if not allowed:
                messages.error(
                    request,
                    "Verification required to delete IP record.",
                )
                return redirect("admin_security")

            if aid:
                obj = SuspiciousActivity.objects.filter(
                    id=aid
                ).first()

                if obj:
                    ip = obj.ip

                    # Audit BEFORE deleting the record.
                    try:
                        SecurityEventLog.objects.create(
                            event_type=SecurityEventLog.EVENT_LOCK,
                            actor=request.user,
                            message=(
                                f"IP record deleted: {ip}"
                            ),
                        )
                    except Exception:
                        pass

                    obj.delete()

                    cache.set(
                        f"ip_blocked:{ip}",
                        False,
                        60,
                    )

                    messages.success(
                        request,
                        f"IP record {ip} deleted.",
                    )

            return redirect("admin_security")

    # =============================================================
    # GET / PAGE DATA
    # =============================================================

    logs = SecurityEventLog.objects.order_by("-created_at")

    # Active suspicious IPs
    suspicious = (
        SuspiciousActivity.objects
        .filter(
            is_tracking=True,
            is_blocked=False,
            suppress_logging=False,
        )
        .order_by("-unread", "-last_seen")
    )

    # Muted IPs
    muted = (
        SuspiciousActivity.objects
        .filter(
            is_tracking=True,
            is_blocked=False,
            suppress_logging=True,
        )
        .order_by("-last_seen")
    )

    # Blocked IPs
    blocked = (
        SuspiciousActivity.objects
        .filter(
            is_tracking=True,
            is_blocked=True,
        )
        .order_by("-last_seen")
    )

    ctx = {
        "site_lock": site_lock,
        "is_effective_lock": site_lock.is_effective_lock(),
        "logs": logs,

        "suspicious": suspicious,
        "muted": muted,
        "blocked": blocked,

        "delete_verified_until": request.session.get(
            "report_delete_verified_until"
        ),
    }

    return render(
        request,
        "freshbread/admin/security.html",
        ctx,
    )
