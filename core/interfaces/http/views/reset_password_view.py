from django.shortcuts import render, redirect
from django.contrib import messages


def reset_password_step1_view(request):
    # Lazy imports to avoid early app loading
    from core.application.security.ddos_checker import ddos_checker
    from core.application.services.password_reset_service import PasswordResetService, RateLimitedException, PasswordResetException
    from core.interfaces.http.utils.ip import get_client_ip

    blocked = ddos_checker.check(request)
    if blocked:
        return blocked

    if request.method == "POST":
        try:
            username = request.POST.get("username", "").strip()
            email = request.POST.get("email", "").strip()
            ip = get_client_ip(request)

            session_username = PasswordResetService.initiate_reset(username, email, ip)
            request.session['reset_username'] = session_username

            messages.success(request, "✅ Verification code sent to your email.")
            return redirect('reset_password_step2')

        except RateLimitedException as e:
            messages.error(request, str(e))
        except PasswordResetException as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, "Internal error during reset initiation")

    return render(request, "freshbread/reset_password/reset 1.html")


def reset_password_step2_view(request):
    # Lazy imports
    from core.application.security.ddos_checker import ddos_checker
    from core.application.services.password_reset_service import PasswordResetService, RateLimitedException, PasswordResetException
    from core.interfaces.http.utils.ip import get_client_ip

    blocked = ddos_checker.check(request)
    if blocked:
        return blocked

    if request.method == "POST":
        try:
            username = request.session.get("reset_username")
            if not username:
                messages.error(request, "⛔ Session expired. Please restart the reset process.")
                return redirect("reset_password_step1")

            code = request.POST.get("code", "").strip()
            ip = get_client_ip(request)

            PasswordResetService.verify_code(username, code, ip)
            messages.success(request, "✅ Code verified. You can now reset your password.")
            return redirect("reset_password_step3")

        except RateLimitedException as e:
            messages.error(request, str(e))
        except PasswordResetException as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, "Internal error during code verification")

    return render(request, "freshbread/reset_password/reset 2.html")


def reset_password_step3_view(request):
    # Lazy imports
    from core.application.security.ddos_checker import ddos_checker
    from core.application.services.password_reset_service import PasswordResetService, RateLimitedException, PasswordResetException
    from django.core.exceptions import ValidationError
    from core.interfaces.http.utils.ip import get_client_ip

    blocked = ddos_checker.check(request)
    if blocked:
        return blocked

    # Ensure step2 completed
    ip = get_client_ip(request)
    if not PasswordResetService.check_step_completion(ip):
        messages.error(request, "⛔ You must complete Step 2 first.")
        return redirect("reset_password_step2")

    if request.method == "POST":
        try:
            username = request.session.get("reset_username")
            if not username:
                messages.error(request, "⛔ Session expired. Please restart the reset process.")
                return redirect("reset_password_step1")

            password = request.POST.get("npassword", "")
            password_confirm = request.POST.get("npassword_confirm", "")
            if password != password_confirm:
                messages.error(request, "❌ Passwords do not match.")
                return render(request, "freshbread/reset_password/reset 3.html")

            PasswordResetService.reset_password(username, password, ip)

            # Clear session
            try:
                del request.session['reset_username']
            except KeyError:
                pass

            messages.success(request, "✅ Password changed successfully.")
            return redirect("ru")

        except ValidationError as e:
            for err in getattr(e, 'messages', [str(e)]):
                messages.error(request, err)
        except RateLimitedException as e:
            messages.error(request, str(e))
        except PasswordResetException as e:
            messages.error(request, str(e))
        except Exception:
            messages.error(request, "Internal error during password reset")

    return render(request, "freshbread/reset_password/reset 3.html")