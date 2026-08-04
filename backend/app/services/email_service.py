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
        Sends a Password Reset email containing a clean CTA Reset Password button.
        Order of priority:
        1. Brevo REST API (if BREVO_API_KEY is configured)
        2. Generic SMTP Server (if SMTP_HOST is configured)
        3. Console/Log Fallback (for local development testing)
        """
        clean_frontend_url = settings.FRONTEND_URL.strip().rstrip("/")
        reset_link = f"{clean_frontend_url}/reset-password?token={reset_token}"

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background-color: #030712;
                    color: #f8fafc;
                    margin: 0;
                    padding: 40px 16px;
                    -webkit-font-smoothing: antialiased;
                }}
                .email-wrapper {{
                    max-width: 520px;
                    margin: 0 auto;
                    background: #0f172a;
                    border: 1px solid rgba(59, 130, 246, 0.3);
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6), 0 0 30px rgba(59, 130, 246, 0.1);
                }}
                .email-header {{
                    padding: 32px 36px 20px 36px;
                    border-bottom: 1px solid rgba(51, 65, 85, 0.6);
                    background: linear-gradient(180deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.8) 100%);
                }}
                .brand-title {{
                    font-size: 20px;
                    font-weight: 800;
                    color: #38bdf8;
                    letter-spacing: 1.5px;
                    margin: 0 0 6px 0;
                    text-transform: uppercase;
                }}
                .security-badge {{
                    display: inline-block;
                    padding: 3px 10px;
                    border-radius: 12px;
                    background: rgba(59, 130, 246, 0.12);
                    border: 1px solid rgba(59, 130, 246, 0.3);
                    color: #60a5fa;
                    font-size: 11px;
                    font-weight: 600;
                }}
                .email-body {{
                    padding: 32px 36px;
                    color: #cbd5e1;
                    font-size: 14.5px;
                    line-height: 1.65;
                }}
                .greeting {{
                    font-size: 16px;
                    font-weight: 600;
                    color: #f8fafc;
                    margin-top: 0;
                    margin-bottom: 14px;
                }}
                .button-wrapper {{
                    margin: 32px 0;
                    text-align: center;
                }}
                .btn-reset {{
                    display: inline-block;
                    background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
                    color: #ffffff !important;
                    text-decoration: none;
                    padding: 14px 36px;
                    border-radius: 10px;
                    font-weight: 700;
                    font-size: 15px;
                    letter-spacing: 0.3px;
                    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.4);
                    transition: all 0.2s ease;
                }}
                .info-notice {{
                    background: rgba(30, 41, 59, 0.6);
                    border-left: 3px solid #3b82f6;
                    padding: 12px 16px;
                    border-radius: 0 8px 8px 0;
                    font-size: 12.5px;
                    color: #94a3b8;
                    margin-top: 24px;
                }}
                .email-footer {{
                    padding: 20px 36px;
                    background: #090d16;
                    border-top: 1px solid rgba(51, 65, 85, 0.5);
                    font-size: 11.5px;
                    color: #64748b;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="email-wrapper">
                <div class="email-header">
                    <div class="brand-title">FORENSIGHT AI</div>
                    <div class="security-badge">&#128274; Password Reset Verification</div>
                </div>
                <div class="email-body">
                    <p class="greeting">Hello {username},</p>
                    <p>We received a request to reset the password for your ForenSight account. Click the button below to choose a new password:</p>
                    
                    <div class="button-wrapper">
                        <a href="{reset_link}" class="btn-reset" target="_blank">Reset Password</a>
                    </div>
                    
                    <div class="info-notice">
                        <strong>Security Notice:</strong> This password reset link expires in <strong>15 minutes</strong>. If you did not request this reset, your account is safe and no action is required.
                    </div>
                </div>
                <div class="email-footer">
                    &copy; ForenSight AI Platform &bull; Secure Encrypted Verification System
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"Hello {username},\n\nWe received a request to reset your password.\n\nClick the link below to choose a new password (expires in 15 mins):\n{reset_link}\n\nIf you did not request this, please ignore this message."

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
