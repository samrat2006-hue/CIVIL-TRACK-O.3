
import os
import smtplib
import html

import streamlit as st

from email.message import EmailMessage
from email.utils import formataddr


# --------------------------------------------------
# EMAIL CONFIGURATION
# --------------------------------------------------

SENDER_EMAIL = "gangulyrohit2008@gmail.com"
SENDER_NAME = "CivicTrack Administration"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

OTP_VALIDITY_MINUTES = 5


# --------------------------------------------------
# GMAIL APP PASSWORD
# --------------------------------------------------

def get_email_app_password():
    """
    Read the Gmail App Password from Streamlit secrets
    or the CIVICTRACK_EMAIL_APP_PASSWORD environment variable.
    """

    try:
        password = st.secrets.get("GMAIL_APP_PASSWORD")

        if password:
            return str(password).replace(" ", "")

    except Exception:
        pass

    password = os.environ.get(
        "CIVICTRACK_EMAIL_APP_PASSWORD"
    )

    if password:
        return password.replace(" ", "")

    return None


# --------------------------------------------------
# PASSWORD RESET EMAIL
# --------------------------------------------------

def send_password_reset_email(recipient_email, otp):

    if not recipient_email or not otp:
        return False, "Recipient email or OTP is missing."

    app_password = get_email_app_password()

    if not app_password:
        return (
            False,
            "Email service is not configured. Please configure "
            "the Gmail App Password in Streamlit secrets."
        )

    safe_otp = html.escape(str(otp))

    message = EmailMessage()

    message["Subject"] = "CivicTrack | Password Reset Verification"
    message["From"] = formataddr(
        (SENDER_NAME, SENDER_EMAIL)
    )
    message["To"] = recipient_email

    plain_text = f"""
Hello,

We received a request to reset the password associated
with your CivicTrack account.

YOUR PASSWORD RESET OTP

{otp}

This OTP is valid for {OTP_VALIDITY_MINUTES} minutes
and can only be used once.

IMPORTANT SECURITY INFORMATION:

- Never share this OTP with anyone.
- CivicTrack administrators will never ask you to disclose
  your OTP.
- If you did not request this password reset, please ignore
  this email. Your existing password will remain unchanged.

Regards,
Team CivicTrack Administration
"""

    message.set_content(plain_text)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CivicTrack Password Reset</title>
    </head>

    <body style="margin:0;padding:25px 10px;background-color:#f3f6fb;font-family:Arial,Helvetica,sans-serif;color:#253247;">

        <div style="max-width:560px;margin:0 auto;background-color:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e2e8f0;">

            <div style="background-color:#123b70;padding:28px 25px;text-align:center;color:#ffffff;">
                <h1 style="margin:0;font-size:27px;letter-spacing:1px;">CivicTrack</h1>
                <p style="margin:9px 0 0;font-size:14px;color:#dbeafe;">
                    Password Recovery Verification
                </p>
            </div>

            <div style="padding:30px 28px;">

                <h2 style="margin-top:0;color:#123b70;font-size:21px;">
                    Password Reset Request
                </h2>

                <p style="font-size:15px;line-height:1.7;color:#475569;">
                    Hello,
                </p>

                <p style="font-size:15px;line-height:1.7;color:#475569;">
                    We received a request to reset the password
                    associated with your CivicTrack account.
                    Please use the verification code below
                    to continue.
                </p>

                <div style="margin:28px 0;padding:23px 15px;text-align:center;background-color:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;">

                    <p style="margin:0 0 12px;font-size:12px;font-weight:bold;letter-spacing:1.5px;color:#475569;">
                        YOUR VERIFICATION OTP
                    </p>

                    <div style="font-size:34px;font-weight:bold;letter-spacing:9px;color:#123b70;">
                        {safe_otp}
                    </div>

                    <p style="margin:14px 0 0;font-size:13px;color:#64748b;">
                        Valid for {OTP_VALIDITY_MINUTES} minutes
                    </p>

                </div>

                <div style="padding:17px;background-color:#fff7ed;border-left:4px solid #f59e0b;border-radius:5px;">

                    <p style="margin:0 0 9px;font-size:14px;font-weight:bold;color:#92400e;">
                        Important Security Information
                    </p>

                    <p style="margin:0;font-size:13px;line-height:1.7;color:#78350f;">
                        Never share this OTP with anyone.
                        CivicTrack administrators will never
                        ask you to disclose your OTP.
                    </p>

                </div>

                <p style="margin-top:23px;font-size:14px;line-height:1.7;color:#475569;">
                    If you did not request this password reset,
                    please ignore this email. Your existing
                    password will remain unchanged.
                </p>

                <p style="margin-top:27px;font-size:14px;line-height:1.7;color:#475569;">
                    Regards,<br>
                    <strong>Team CivicTrack Administration</strong>
                </p>

            </div>

            <div style="padding:17px 20px;text-align:center;background-color:#f8fafc;border-top:1px solid #e2e8f0;">
                <p style="margin:0;font-size:12px;color:#94a3b8;">
                    This is an automated email.
                    Please do not reply to this message.
                </p>
            </div>

        </div>

    </body>
    </html>
    """

    message.add_alternative(
        html_content,
        subtype="html"
    )

    try:

        with smtplib.SMTP_SSL(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=20
        ) as smtp:

            smtp.login(
                SENDER_EMAIL,
                app_password
            )

            smtp.send_message(message)

        return (
            True,
            "Password reset OTP sent successfully."
        )

    except Exception:
        return (
            False,
            "The OTP email could not be delivered. "
            "Please check the email configuration and try again."
        )
