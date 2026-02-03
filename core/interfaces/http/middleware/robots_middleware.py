from typing import Iterable


class RobotsNoIndexMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._prefixes = [
            "/orders/",
            "/tickets/",
            "/admin_tools/",
            "/auth/ru",
            "/auth/su",
            "/auth/reset_password_step1",
            "/auth/reset_password_step2",
            "/auth/reset_password_step3",
            "/auth/verify_email",
            "/auth/complete_profile",
            "/auth/complete_profile_social",
            "/auth/check_profile",
            "/cart/",
            "/checkout/",
            "/coming/",
            "/reviews/review_check",
            "/blog/add",
            "/blog/manage",
            "/product/manage",
            "/product/add",
            "/profile/profile/",
            "/profile/edit_profile/",
            "/profile/user/",
        ]

    def __call__(self, request):
        response = self.get_response(request)
        try:
            path = (request.path or "").lower()
            should_noindex = False

            if response.status_code in {403, 404, 500}:
                should_noindex = True
            else:
                # admin/order/ticket/profile/product/blog restricted pages
                for p in self._prefixes:
                    if path.startswith(p):
                        should_noindex = True
                        break

                # blog edit/delete specific patterns
                if not should_noindex and path.startswith("/blog/"):
                    parts = path.strip("/").split("/")
                    if len(parts) >= 3 and parts[2] in {"edit", "delete"}:
                        should_noindex = True

                # product edit/delete specific patterns
                if not should_noindex and path.startswith("/product/"):
                    parts = path.strip("/").split("/")
                    if len(parts) >= 3 and parts[2] in {"edit", "delete"}:
                        should_noindex = True

            if should_noindex:
                response["X-Robots-Tag"] = "noindex, follow"
        except Exception:
            pass
        return response