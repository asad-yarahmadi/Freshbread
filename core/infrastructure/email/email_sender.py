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
        logo_url: str = "https://kingfood.ca/static/images/logo.png",
        cta_text: str | None = None,
        action_url: str | None = None,
    ) -> str:
        if body_html:
            # جایگزینی خطوط جدید با تگ بریک، اما با حفظ پاراگراف بندی استاندارد
            body_html = body_html.replace("\n", "<br>")

        # دکمه CTA (کاملاً سازگار با Outlook)
        cta_block = ""
        if cta_text and action_url:
            cta_block = f"""
            <tr>
                <td align="center" style="padding:28px 40px 36px 40px;">
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center">
                        <tr>
                            <td style="border-radius:50px; background-color:{brand_color};">
                                <a href="{action_url}" 
                                   style="font-size:15px; font-family:Arial,Helvetica,sans-serif; font-weight:700; color:#ffffff; text-decoration:none; display:inline-block; padding:14px 40px; border-radius:50px; border:1px solid {brand_color};">
                                    {cta_text}
                                </a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            """

        return f"""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kingfood</title>
</head>
<body style="margin:0; padding:0; background-color:#f8f1eb; -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%;">
<table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color:#f8f1eb;">
  <tr>
    <td align="center" style="padding:30px 10px;">
      <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="max-width:600px; width:100%; background:#ffffff; border:1px solid #e0e0e0; border-radius:16px; overflow:hidden; box-shadow:0 10px 30px rgba(0,0,0,0.08);">
        
        <!-- Top accent stripe -->
        <tr><td style="background:{brand_color}; height:5px; font-size:0; line-height:0;">&nbsp;</td></tr>
        
        <!-- Logo -->
        <tr>
          <td align="center" style="padding:32px 0 14px 0;">
            <img src="{logo_url}" width="180" alt="Kingfood" style="display:block; border:0; outline:none; text-decoration:none; -ms-interpolation-mode:bicubic;">
          </td>
        </tr>
        
        <!-- Safe Divider (جایگزین گرادیانت که در Outlook می‌شکند) -->
        <tr>
          <td style="padding:0 40px 20px 40px;">
            <hr style="border:none; border-top:1px solid #eeeeee; margin:0;">
          </td>
        </tr>
        
        <!-- Title + Body -->
        <tr>
          <td style="padding:0 40px 10px 40px; font-family:Arial,Helvetica,sans-serif;">
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
          <td style="border-top:1px solid #eeeeee; padding:24px 40px 32px 40px; text-align:center; font-family:Arial,Helvetica,sans-serif;">
            <p style="margin:0 0 6px 0; font-size:14px; color:#666666; line-height:1.8;">
              Please do not reply to this email.<br>Best regards,<br>
              <strong style="color:{brand_color};">Kingfood team</strong>
            </p>
            <p style="margin:6px 0 0 0; font-size:13px;">
              <a href="https://kingfood.ca" style="color:{brand_color}; text-decoration:none;">kingfood.ca</a>
            </p>
            
            <!-- Instagram Icon -->
            <div style="margin:20px 0;">
              <a href="https://instagram.com/kingfood.ca">
                <img src="https://cdn-icons-png.flaticon.com/512/4138/4138124.png" width="35" height="35" style="display:block; width:35px; height:35px; border-radius:50%; border:1px solid {brand_color}; padding:2px;" alt="Instagram">
              </a>
            </div>

            <p style="margin:0 0 4px 0; font-size:12px; color:#aaaaaa;">
              © 2026 Kingfood. All rights reserved.<br>
              Kingfood, 2935 Richmond Rd, Ottawa, ON K2B 8C9، Canada
            </p>
          </td>
        </tr>
        
        <!-- Bottom accent stripe -->
        <tr><td style="background:{brand_color}; height:4px; font-size:0; line-height:0;">&nbsp;</td></tr>
        
      </table>
      
      <!-- تصاویر تزئینی به عنوان عکس (بدون SVG مستقیم) -->
      <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top:0;">
        <tr>
          <td align="left" style="width:110px; vertical-align:bottom; padding-right:10px;">
            <!-- لطفا فایل های SVG را تبدیل به PNG کرده و آپلود کنید -->
            <img src="https://kingfood.ca/static/images/room-service.png" width="90" height="80" style="display:block; opacity:0.85;" alt="">
          </td>
          <td style=""></td>
          <td align="right" style="width:100px; vertical-align:top; padding-left:10px;">
            <img src="https://kingfood.ca/static/images/bonfire.png" width="80" height="85" style="display:block; opacity:0.85;" alt="">
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
                    message = strip_tags(body_body)
        send_mail(
            final_subject,
            message or "",
            "kingfoodca@gmail.com", 
            [to],
            fail_silently=False,
            html_message=html_body,
        )

email_sender = EmailSender()