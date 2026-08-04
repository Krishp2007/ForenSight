import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from loguru import logger
from backend.app.config import settings

class EmailService:
    @staticmethod
    async def send_password_reset_email(to_email: str, username: str, reset_token: str) -> bool:
        """
        Sends a Password Reset email containing the frontend reset link.
        Order of priority:
        1. Brevo REST API (if BREVO_API_KEY is configured)
        2. Generic SMTP Server (if SMTP_HOST is configured)
        3. Console/Log Fallback (for local development testing)
        """
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; color: #e2e8f0; margin: 0; padding: 20px; }}
                .container {{ max-width: 580px; margin: 0 auto; background-color: #111827; border: 1px solid #1e293b; border-radius: 8px; padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
                .header {{ border-bottom: 1px solid #1e293b; padding-bottom: 16px; margin-bottom: 24px; }}
                .brand {{ font-size: 22px; font-weight: bold; color: #38bdf8; letter-spacing: 1px; }}
                .content {{ font-size: 15px; line-height: 1.6; color: #cbd5e1; }}
                .button-container {{ margin: 32px 0; text-align: center; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%); color: #ffffff !important; text-decoration: none; padding: 12px 28px; border-radius: 6px; font-weight: 600; font-size: 15px; box-shadow: 0 4px 12px rgba(37,99,235,0.3); }}
                .footer {{ border-top: 1px solid #1e293b; margin-top: 32px; padding-top: 16px; font-size: 12px; color: #64748b; text-align: center; }}
                .code-box {{ background-color: #0f172a; border: 1px solid #334155; padding: 12px; border-radius: 4px; font-family: monospace; font-size: 13px; word-break: break-all; margin-top: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="brand">FORENSIGHT SECURITY</div>
                </div>
                <div class="content">
                    <p>Hello <strong>{username}</strong>,</p>
                    <p>We received a request to reset your password for your ForenSight account.</p>
                    <p>Click the button below to set a new password. This link will expire in <strong>15 minutes</strong>.</p>
                    <div class="button-container">
                        <a href="{reset_link}" class="button" target="_blank">Reset Password</a>
                    </div>
                    <p>Or copy and paste this link into your browser:</p>
                    <div class="code-box">{reset_link}</div>
                    <p style="margin-top: 24px;">If you did not request a password reset, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    &copy; ForenSight Forensic Analytics Platform &bull; Secure Automated Email Notification
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"Hello {username},\n\nWe received a request to reset your password.\n\nUse this link to set a new password (expires in 15 mins):\n{reset_link}\n\nIf you did not request this, please ignore this email."

        # ── 1. BREVO REST API DISPATCH ──
        if settings.BREVO_API_KEY:
            try:
                url = "https://api.brevo.com/v3/smtp/email"
                headers = {
                    "accept": "application/json",
                    "api-key": settings.BREVO_API_KEY,
                    "content-type": "application/json"
                }
                payload = {
                    "sender": {
                        "name": settings.EMAILS_FROM_NAME,
                        "email": settings.EMAILS_FROM_EMAIL
                    },
                    "to": [
                        {
                            "email": to_email,
                            "name": username
                        }
                    ],
                    "subject": "ForenSight Account Password Reset Request",
                    "htmlContent": html_content,
                    "textContent": text_content
                }
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    if response.status_code in (200, 201, 202):
                        logger.info(f"Password reset email sent to {to_email} via Brevo API")
                        return True
                    else:
                        logger.error(f"Brevo API error ({response.status_code}): {response.text}")
            except Exception as e:
                logger.error(f"Brevo API request exception for {to_email}: {str(e)}")

        # ── 2. SMTP DISPATCH FALLBACK ──
        if settings.SMTP_HOST and settings.SMTP_USER:
            try:
                def _send():
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = "ForenSight Account Password Reset Request"
                    msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
                    msg["To"] = to_email

                    part1 = MIMEText(text_content, "plain")
                    part2 = MIMEText(html_content, "html")
                    msg.attach(part1)
                    msg.attach(part2)

                    if settings.SMTP_PORT == 465:
                        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                            server.sendmail(settings.EMAILS_FROM_EMAIL, [to_email], msg.as_string())
                    else:
                        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                            server.starttls()
                            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                            server.sendmail(settings.EMAILS_FROM_EMAIL, [to_email], msg.as_string())
                    return True

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, _send)
                logger.info(f"Password reset email sent to {to_email} via SMTP ({settings.SMTP_HOST})")
                return True
            except Exception as e:
                logger.error(f"Failed to send password reset email to {to_email} via SMTP: {str(e)}")

        # ── 3. LOCAL DEV CONSOLE LOGGING FALLBACK ──
        logger.info("==========================================================================")
        logger.info(f"[EMAIL SERVICE FALLBACK] Password Reset requested for: {to_email}")
        logger.info(f"[RESET LINK]: {reset_link}")
        logger.info("==========================================================================")
        return True
