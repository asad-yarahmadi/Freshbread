from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

class EmailSender:
    def _base_subject(self, base_subject: str) -> str:
        base_subject = base_subject or ""
        suffix = " - Kingfood"
        return base_subject[:-len(suffix)] if base_subject.endswith(suffix) else base_subject

    def _final_subject(self, base_subject: str) -> str:
        base_subject = base_subject or ""
        suffix = " - Kingfood"
        return base_subject if base_subject.endswith(suffix) else base_subject + suffix

    def _wrap_html(
        self,
        *,
        title: str,
        body_html: str,
        brand_color: str = "#E63939",
        logo_url: str = "https://kingfood.ca/static/images/logo.webp",
        cta_text: str | None = None,
        action_url: str | None = None,
    ) -> str:
        if body_html:
            body_html = body_html.replace("\n", "<br>")

        cta_block = ""
        if cta_text and action_url:
            cta_block = f"""
            <tr>
                <td align="center" style="padding:28px 40px 36px 40px;">
                    <a href="{action_url}" target="_blank"
                       style="background:{brand_color};
                              color:#ffffff;
                              text-decoration:none;
                              display:inline-block;
                              padding:14px 40px;
                              border-radius:50px;
                              font-weight:700;
                              font-size:15px;
                              font-family:Arial,Helvetica,sans-serif;">
                        {cta_text}
                    </a>
                </td>
            </tr>
            """

        pot_svg = """
            <svg width="100" height="90" viewBox="0 0 100 90" xmlns="http://www.w3.org/2000/svg" opacity="0.82">
                <ellipse cx="50" cy="82" rx="30" ry="6" fill="#FF6B00" opacity="0.18"/>
                <ellipse cx="38" cy="76" rx="6" ry="9" fill="#FF9500" opacity="0.7" transform="rotate(-10 38 76)"/>
                <ellipse cx="38" cy="76" rx="3" ry="6" fill="#FFD000" opacity="0.9" transform="rotate(-10 38 76)"/>
                <ellipse cx="50" cy="74" rx="7" ry="11" fill="#FF6B00" opacity="0.8"/>
                <ellipse cx="50" cy="74" rx="4" ry="7" fill="#FFD000" opacity="0.95"/>
                <ellipse cx="62" cy="76" rx="6" ry="9" fill="#FF9500" opacity="0.7" transform="rotate(10 62 76)"/>
                <ellipse cx="62" cy="76" rx="3" ry="6" fill="#FFD000" opacity="0.9" transform="rotate(10 62 76)"/>
                <rect x="22" y="52" width="56" height="26" rx="8" fill="#C0392B"/>
                <rect x="28" y="55" width="20" height="6" rx="3" fill="#E74C3C" opacity="0.5"/>
                <rect x="18" y="49" width="64" height="8" rx="4" fill="#922B21"/>
                <rect x="24" y="42" width="52" height="12" rx="6" fill="#A93226"/>
                <rect x="44" y="36" width="12" height="9" rx="4" fill="#7B241C"/>
                <rect x="8" y="53" width="16" height="8" rx="4" fill="#922B21"/>
                <rect x="76" y="53" width="16" height="8" rx="4" fill="#922B21"/>
                <path d="M42 38 Q40 30 42 22 Q44 14 42 8" stroke="#ccc" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.5"/>
                <path d="M50 36 Q48 28 50 20 Q52 12 50 6" stroke="#ccc" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.5"/>
                <path d="M58 38 Q56 30 58 22 Q60 14 58 8" stroke="#ccc" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.5"/>
            </svg>
        """

        chef_hat_svg = """
            <svg width="90" height="95" viewBox="0 0 90 95" xmlns="http://www.w3.org/2000/svg" opacity="0.85">
                <circle cx="45" cy="6" r="4" fill="#aaa"/>
                <rect x="43" y="6" width="4" height="10" rx="2" fill="#bbb"/>
                <line x1="45" y1="16" x2="45" y2="26" stroke="#E63939" stroke-width="2.5" stroke-linecap="round"/>
                <rect x="18" y="62" width="54" height="14" rx="5" fill="#e0e0e0"/>
                <rect x="18" y="62" width="54" height="7" rx="4" fill="#E63939" opacity="0.9"/>
                <ellipse cx="45" cy="48" rx="28" ry="22" fill="#f7f7f7" stroke="#e0e0e0" stroke-width="1.5"/>
                <ellipse cx="27" cy="44" rx="10" ry="14" fill="#ffffff" stroke="#e8e8e8" stroke-width="1"/>
                <ellipse cx="45" cy="40" rx="12" ry="16" fill="#ffffff" stroke="#e8e8e8" stroke-width="1"/>
                <ellipse cx="63" cy="44" rx="10" ry="14" fill="#ffffff" stroke="#e8e8e8" stroke-width="1"/>
                <ellipse cx="38" cy="26" rx="7" ry="4" fill="#E63939" opacity="0.85" transform="rotate(-20 38 26)"/>
                <ellipse cx="52" cy="26" rx="7" ry="4" fill="#E63939" opacity="0.85" transform="rotate(20 52 26)"/>
                <circle cx="45" cy="26" r="4" fill="#C0392B"/>
                <rect x="18" y="58" width="54" height="10" rx="4" fill="#f7f7f7"/>
                <rect x="18" y="70" width="54" height="6" rx="3" fill="#d0d0d0"/>
            </svg>
        """

        return f"""
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0; padding:0; background-color:#f8f1eb;">
<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#f8f1eb;">
<tr>
<td align="center" style="padding:30px 10px;">
<table width="600" cellpadding="0" cellspacing="0" role="presentation" style="width:100%; max-width:600px;">
<tr><td>
<!-- Main card -->
<table width="100%" cellpadding="0" cellspacing="0" role="presentation"
       style="background:#ffffff; border-radius:16px; overflow:hidden; box-shadow:0 10px 30px rgba(0,0,0,0.08);">
    <!-- Top accent stripe -->
    <tr><td style="background:{brand_color}; height:5px; font-size:0; line-height:0;">&nbsp;</td></tr>
    <!-- Logo -->
    <tr>
        <td align="center" style="padding:32px 0 14px 0;">
            <img src="{logo_url}" width="180" alt="Kingfood" style="display:block; border:0;">
        </td>
    </tr>
    <!-- Gradient divider -->
    <tr>
        <td style="padding:0 40px 20px 40px;">
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="height:2px; background:linear-gradient(to right, transparent, {brand_color}, transparent);"></td>
                </tr>
            </table>
        </td>
    </tr>
    <!-- Title + Body -->
    <tr>
        <td style="padding:0 40px 20px 40px; font-family:Arial,Helvetica,sans-serif;">
            <h1 style="margin:0 0 16px 0; font-size:26px; line-height:1.35; color:#2b2b2b; font-weight:700; text-align:center;">
                {title}
            </h1>
            <div style="font-size:15px; line-height:1.8; color:#444444; text-align:center;">
                {body_html}
            </div>
        </td>
    </tr>
    {cta_block}
    <!-- Footer -->
    <tr>
        <td style="background:#ffffff; border-top:1px solid #eeeeee; padding:24px 40px 32px 40px; text-align:center; font-family:Arial,Helvetica,sans-serif;">

        <p style="margin:0 0 6px 0; font-size:14px; color:#666666; line-height:1.8;">
               Please do not reply to this email.<br>Best regards,<br>
                <strong style="color:{brand_color};">Kingfood team</strong>
            </p>
            <p style="margin:6px 0 0 0; font-size:13px;">
                <a href="https://kingfood.ca" style="color:{brand_color}; text-decoration:none;">kingfood.ca</a>
            </p>
            <p style="margin:10px 0 0 0; font-size:12px; color:#aaaaaa;">© 2026 Kingfood. All rights reserved.</p>
                    <!-- Instagram Icon -->
            <div style="margin-bottom:14px;">
                <a href="https://instagram.com/kingfood.ca" target="_blank">
                    <img src="https://cdn-icons-png.flaticon.com/512/4138/4138124.png" 
                         width="42" height="42" 
                         style="display:block; width:35px; height:35px; border-radius:50%; border:1px solid #E63939; padding:2px;"
                         alt="Instagram">
                </a>
            </div>
        </td>
    </tr>
    <!-- Bottom accent stripe -->
    <tr><td style="background:{brand_color}; height:4px; font-size:0; line-height:0;">&nbsp;</td></tr>
</table>
<!-- Decorative illustrations -->
<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="margin-top:0;">
<tr>
    <td align="left" style="width:110px; vertical-align:bottom; padding-right:10px;">
        {pot_svg}
    </td>
    <td style=""></td>
    <td align="right" style="width:100px; vertical-align:top; padding-left:10px;">
        {chef_hat_svg}
    </td>
</tr>
</table>
</td></tr>
</table>
</td>
</tr>
</table>
</body>
</html>
"""    
    def send(self, *, subject, message, to, html_template: str = None, context: dict | None = None, html_message: str | None = None, title: str | None = None, cta_text: str | None = None, action_url: str | None = None, wrap: bool = True):
        final_subject = self._final_subject(subject)
        html_body = html_message
        if html_template:
            ctx = context or {}
            html_body = render_to_string(html_template, ctx)
            # Fallback plain text from HTML when message not provided
            if not message:
                message = strip_tags(html_body)
        else:
            if wrap:
                base_title = title or self._base_subject(final_subject)
                body_html = html_body or (message or "")
                html_body = self._wrap_html(
                    title=base_title,
                    body_html=body_html,
                    cta_text=cta_text,
                    action_url=action_url,
                )
                if not message:
                    message = strip_tags(body_html)
        send_mail(
            final_subject,
            message or "",
            "kingfoodca@gmail.com",
            [to],
            fail_silently=False,
            html_message=html_body,
        )

email_sender = EmailSender()
