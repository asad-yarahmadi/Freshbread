from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

class EmailSender:
    def _base_subject(self, base_subject: str) -> str:
        base_subject = base_subject or ""
        suffix = " - Fresh Bread Bakery"
        return base_subject[:-len(suffix)] if base_subject.endswith(suffix) else base_subject

    def _final_subject(self, base_subject: str) -> str:
        base_subject = base_subject or ""
        suffix = " - Fresh Bread Bakery"
        return base_subject if base_subject.endswith(suffix) else base_subject + suffix

    def _wrap_html(
        self,
        *,
        title: str,
        body_html: str,
        brand_color: str = "#C47A3A",
        logo_url: str = "https://res.cloudinary.com/dyx2ri33o/image/upload/v1767000009/logo_fcrm1r.png",
        cta_text: str | None = None,
        action_url: str | None = None,
    ) -> str:

    # تبدیل خط جدید به <br> برای نمایش درست در HTML
        if body_html:
            body_html = body_html.replace("\n", "<br>")

    # بلوک دکمه CTA
        cta_block = ""
        if cta_text and action_url:
            cta_block = f"""
            <tr>
                <td align="center" style="padding:20px 0 32px 0;">
                    <a href="{action_url}" target="_blank"
                   style="background:{brand_color};
                          color:#ffffff;
                          text-decoration:none;
                          display:inline-block;
                          padding:14px 34px;
                          border-radius:30px;
                          font-weight:600;
                          font-size:16px;
                          font-family:Arial, Helvetica, sans-serif;">
                    {cta_text}
                </a>
            </td>
        </tr>
        """

        return f"""
<html>
<body style="margin:0; padding:0; background-color:#f4f4f4;">
<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#f4f4f4;">
<tr>
<td align="center" style="padding:24px 12px;">

<table width="600" cellpadding="0" cellspacing="0" role="presentation"
       style="width:100%; max-width:600px; background:#ffffff; border-radius:12px; overflow:hidden;">

<!-- Logo -->
<tr>
<td align="center" style="padding:28px 0 12px 0;">
<img src="{logo_url}" width="160" alt="Fresh Bread Bakery"
     style="display:block; border:0;">
</td>
</tr>

<!-- Decorative lines -->
<tr>
<td style="padding:0 0 8px 0;">
<table width="100%" cellpadding="0" cellspacing="0" role="presentation">
<tr>
<td width="8" style="background:{brand_color}; border-radius:0 8px 8px 0;"></td>
<td style="padding:0;"></td>
<td width="8" style="background:{brand_color}; border-radius:8px 0 0 8px;"></td>
</tr>
</table>
</td>
</tr>

<!-- Content -->
<tr>
<td style="padding:20px 32px 8px 32px; font-family:Arial, Helvetica, sans-serif;">

<h1 style="margin:0 0 12px 0;
           font-size:24px;
           line-height:32px;
           color:#2b2b2b;
           font-weight:600;
           text-align:center;">
{title}
</h1>

<div style="font-size:16px;
            line-height:26px;
            color:#555555;
            text-align:center;">
{body_html}
</div>

</td>
</tr>

{cta_block}

<!-- Footer -->
<tr>
<td style="padding:24px 32px 32px 32px;
           border-top:1px solid #eeeeee;
           font-family:Arial, Helvetica, sans-serif;
           font-size:13px;
           line-height:20px;
           color:#777777;
           text-align:center;">
Please don't reply here.<br>
Best regards,<br>
<strong><span style="color: {brand_color};">Fresh Bread</span> Team</strong><br>
kingfood.ca
    </td>
    </tr>

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
            "order.freshbread911@gmail.com",
            [to],
            fail_silently=False,
            html_message=html_body,
        )

email_sender = EmailSender()
