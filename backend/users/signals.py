"""
users/signals.py — CareerCompass Kenya
Handles: admin is_staff sync, StudentProfile creation, welcome email,
         OTP generation for password reset.
"""
import random
import string
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def _ensure_default_school():
    from .models import School
    school = School.objects.filter(name="Not Specified").first()
    if not school:
        school = School.objects.create(
            name="Not Specified", code="000000", county="Nairobi", type="private"
        )
    return school


def generate_otp(length=6):
    """Generate a numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))


@receiver(pre_save, sender='users.CustomUser')
def sync_staff_flag(sender, instance, **kwargs):
    """Guarantee is_staff=True for every admin user on every save."""
    if instance.user_type == 'admin':
        instance.is_staff = True


@receiver(post_save, sender='users.CustomUser')
def on_user_created(sender, instance, created, **kwargs):
    """
    On user creation:
    1. Create a StudentProfile for all non-admin users.
    2. Send a welcome email.
    """
    if not created:
        return

    from .models import StudentProfile
    if instance.user_type != 'admin':
        profile, _ = StudentProfile.objects.get_or_create(
            user=instance,
            defaults={'school': _ensure_default_school()}
        )

    if instance.email:
        _send_welcome_email(instance)


def _send_welcome_email(user):
    """Send a styled HTML welcome email to a newly registered user."""
    try:
        site_url  = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
        site_name = getattr(settings, 'SITE_NAME', 'CareerCompass Kenya')
        subject   = f"Welcome to {site_name} 🧭"

        html_body = render_to_string('emails/welcome.html', {
            'user':      user,
            'site_name': site_name,
            'login_url': f"{site_url}/users/login/",
        })
        plain_body = (
            f"Hello {user.get_full_name() or user.username},\n\n"
            f"Welcome to {site_name}!\n"
            f"Sign in at: {site_url}/users/login/\n\n"
            f"— The {site_name} Team"
        )
        send_mail(
            subject=subject, message=plain_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_body, fail_silently=True,
        )
    except Exception:
        pass  # Never crash registration due to email failure


def send_otp_email(user, purpose='password_reset'):
    """
    Generate and send a 6-digit OTP to the user's email.

    • Production (SMTP configured): delivers a real email.
    • Development (console backend): prints the email to the terminal AND
      logs a clearly visible line so the OTP is easy to find during testing.

    Always returns the OTP string so the caller can store it in the session.
    Returns None only if an unexpected error prevents OTP generation.
    """
    from django.conf import settings as dj_settings

    otp       = generate_otp(6)
    site_name = getattr(dj_settings, 'SITE_NAME', 'CareerCompass Kenya')
    site_url  = getattr(dj_settings, 'SITE_URL',  'http://127.0.0.1:8000')
    backend   = getattr(dj_settings, 'EMAIL_BACKEND', '')
    is_console = 'console' in backend

    if purpose == 'password_reset':
        subject = f"Your {site_name} Password Reset Code"
        message = (
            f"Hello {user.get_full_name() or user.username},\n\n"
            f"Your password reset code is: {otp}\n\n"
            f"This code expires in 10 minutes.\n"
            f"If you did not request this, please ignore this email.\n\n"
            f"— {site_name}"
        )
        html_msg = f"""
        <div style="font-family:system-ui,sans-serif;max-width:480px;margin:0 auto;padding:32px;">
          <h2 style="color:#1e3a8a;">&#x1F9ED; {site_name}</h2>
          <h3 style="color:#374151;">Password Reset Code</h3>
          <p style="color:#6b7280;">Hello {user.get_full_name() or user.username},</p>
          <p style="color:#6b7280;">Your password reset code is:</p>
          <div style="font-size:36px;font-weight:800;color:#2563eb;letter-spacing:8px;
                      text-align:center;padding:20px;background:#eff6ff;border-radius:12px;
                      margin:16px 0;">{otp}</div>
          <p style="color:#9ca3af;font-size:13px;">Expires in 10 minutes.<br>
          If you did not request this, ignore this email.</p>
          <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
          <p style="color:#d1d5db;font-size:11px;">
            {site_name} · <a href="{site_url}" style="color:#3b82f6;">{site_url}</a>
          </p>
        </div>"""
    else:
        subject  = f"Your {site_name} Verification Code"
        message  = f"Your verification code is: {otp}\nExpires in 10 minutes."
        html_msg = f"""
        <div style="font-family:system-ui,sans-serif;max-width:480px;margin:0 auto;padding:32px;">
          <h2 style="color:#1e3a8a;">&#x1F9ED; {site_name}</h2>
          <p>Your verification code is:</p>
          <div style="font-size:36px;font-weight:800;color:#2563eb;letter-spacing:8px;
                      text-align:center;padding:20px;background:#eff6ff;border-radius:12px;
                      margin:16px 0;">{otp}</div>
          <p style="color:#9ca3af;font-size:13px;">Expires in 10 minutes.</p>
        </div>"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=dj_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_msg,
            fail_silently=False,   # raise so we know if SMTP is broken
        )
    except Exception as exc:
        if is_console:
            # Console backend never raises — this branch won't be reached in dev
            logger.info(f"[EMAIL-DEV] OTP for {user.email}: {otp}")
        else:
            logger.error(
                f"[EMAIL-ERROR] Failed to send {purpose} email to {user.email}: {exc}"
            )
            # Still return the OTP — the view will show it was "sent" and the
            # user can retry. Returning None here would break the reset flow.

    # In dev/console mode: print a highly visible line so the developer
    # can find the OTP without digging through the full email dump.
    if is_console:
        separator = "=" * 60
        logger.info(
            f"\n{separator}\n"
            f"  DEV MODE — OTP EMAIL NOT SENT\n"
            f"  Recipient : {user.email}\n"
            f"  Subject   : {subject}\n"
            f"  OTP CODE  : {otp}\n"
            f"  (Copy the code above to complete the reset flow)\n"
            f"{separator}"
        )

    return otp
