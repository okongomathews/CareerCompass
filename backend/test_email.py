#!/usr/bin/env python3
"""
Run this from the backend directory to test your Gmail config
BEFORE starting the server:

    cd Careeratlas/backend
    python test_email.py your-test-recipient@email.com
"""
import sys, os

# Load .env manually
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ .env file loaded")
except Exception as e:
    print(f"✗ Could not load .env: {e}")
    sys.exit(1)

host     = os.getenv('EMAIL_HOST', '')
user     = os.getenv('EMAIL_HOST_USER', '')
password = os.getenv('EMAIL_HOST_PASSWORD', '')
port     = int(os.getenv('EMAIL_PORT', 587))

print(f"\nConfiguration read from .env:")
print(f"  EMAIL_HOST      = {host or '(not set)'}")
print(f"  EMAIL_PORT      = {port}")
print(f"  EMAIL_HOST_USER = {user or '(not set)'}")
print(f"  EMAIL_HOST_PASSWORD = {'*' * len(password) if password else '(not set)'}")

if not all([host, user, password]):
    print("\n✗ One or more EMAIL variables are missing in your .env file.")
    print("  Make sure EMAIL_HOST, EMAIL_HOST_USER, and EMAIL_HOST_PASSWORD are all set.")
    sys.exit(1)

recipient = sys.argv[1] if len(sys.argv) > 1 else user
print(f"\nSending test email to: {recipient}")

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'CareerCompass Kenya — Email Test'
    msg['From']    = f'CareerCompass Kenya <{user}>'
    msg['To']      = recipient

    text = "This is a test email from CareerCompass Kenya. Your email backend is working correctly!"
    html = """\
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px;">
      <h2 style="color:#1F3864;">&#x1F9ED; CareerCompass Kenya</h2>
      <h3 style="color:#2E75B6;">Email Backend Test</h3>
      <p>Your Gmail SMTP configuration is working correctly.</p>
      <div style="font-size:36px;font-weight:800;color:#2563eb;letter-spacing:8px;
                  text-align:center;padding:20px;background:#eff6ff;border-radius:12px;
                  margin:16px 0;">123456</div>
      <p style="color:#9ca3af;font-size:13px;">
        This is what OTP emails look like to your users.
      </p>
    </div>"""

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP(host, port, timeout=10) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(user, password)
        server.sendmail(user, recipient, msg.as_string())

    print(f"\n✓ SUCCESS — test email sent to {recipient}")
    print("  Check your inbox. If you see it, your Django email backend will work too.")

except smtplib.SMTPAuthenticationError:
    print("\n✗ AUTHENTICATION FAILED")
    print("  Your App Password is wrong. Check these things:")
    print("  1. Did you use the App Password (16 chars), not your Gmail login password?")
    print("  2. Is 2-Step Verification enabled on your Google account?")
    print("  3. Copy the App Password exactly as shown — spaces are OK to include or remove")

except smtplib.SMTPConnectError:
    print("\n✗ CONNECTION FAILED — cannot reach smtp.gmail.com:587")
    print("  Check your internet connection or firewall settings.")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
