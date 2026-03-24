"""
SMTP Email Sender
Sends personalized emails via SMTP with rate limiting, duplicate
prevention, and sent-email logging.
"""

import csv
import os
import smtplib
import sys
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Allow importing config from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config


class EmailSender:
    """Sends emails through SMTP (Gmail / Outlook / custom)."""

    def __init__(self):
        self.config = Config()
        self.config.ensure_data_dir()
        self.sent_log = os.path.join(self.config.DATA_DIR, "sent_emails.csv")
        self.server = None

    # ------------------------------------------------------------------
    # SMTP connection
    # ------------------------------------------------------------------

    def connect(self):
        """Establish SMTP connection and authenticate."""
        if not self.config.SMTP_EMAIL or not self.config.SMTP_PASSWORD:
            print("[!] Set SMTP_EMAIL and SMTP_PASSWORD in .env")
            return False
        try:
            self.server = smtplib.SMTP(
                self.config.SMTP_SERVER, self.config.SMTP_PORT
            )
            self.server.ehlo()
            self.server.starttls()
            self.server.ehlo()
            self.server.login(self.config.SMTP_EMAIL, self.config.SMTP_PASSWORD)
            print("[+] SMTP connected and authenticated")
            return True
        except Exception as e:
            print(f"[!] SMTP connection failed: {e}")
            return False

    def disconnect(self):
        """Gracefully close the SMTP connection."""
        if self.server:
            try:
                self.server.quit()
            except Exception:
                pass
            self.server = None

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------

    def send_email(self, to_email, subject, body):
        """Send a single plain-text email."""
        if not self.server and not self.connect():
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.config.YOUR_NAME} <{self.config.SMTP_EMAIL}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            self.server.sendmail(self.config.SMTP_EMAIL, to_email, msg.as_string())
            self._log_sent(to_email, subject, "sent")
            print(f"  [+] Sent -> {to_email}")
            return True

        except smtplib.SMTPException as e:
            print(f"  [!] Send failed ({to_email}): {e}")
            self._log_sent(to_email, subject, "failed")
            self.disconnect()  # force reconnect on next send
            return False

    def send_bulk(self, drafts):
        """Send a list of email drafts with rate limiting.

        Each draft dict must have: to_email, subject, body
        Skips emails already in sent_emails.csv.
        """
        already = self._load_sent_emails()
        sent, failed = 0, 0

        for draft in drafts:
            to = draft.get("to_email", "").strip()
            if not to:
                continue
            if to in already:
                print(f"  [*] Already sent to {to} — skipping")
                continue

            subj = draft.get("subject", "(no subject)")
            body = draft.get("body", "")

            if self.send_email(to, subj, body):
                sent += 1
            else:
                failed += 1

            time.sleep(self.config.EMAIL_DELAY)

        print(f"\n[+] Results: {sent} sent, {failed} failed")
        return sent, failed

    # ------------------------------------------------------------------
    # Logging & dedup
    # ------------------------------------------------------------------

    def _log_sent(self, to_email, subject, status):
        """Append a row to sent_emails.csv."""
        file_exists = os.path.exists(self.sent_log)
        with open(self.sent_log, "a", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            if not file_exists:
                writer.writerow(["email", "subject", "date_sent", "status"])
            writer.writerow([
                to_email,
                subject,
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                status,
            ])

    def _load_sent_emails(self):
        """Return set of emails we've already sent to."""
        emails = set()
        if os.path.exists(self.sent_log):
            with open(self.sent_log, "r", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    emails.add(row.get("email", ""))
        return emails


# Allow standalone execution
if __name__ == "__main__":
    sender = EmailSender()
    print("\n=== SMTP Email Sender (test) ===")
    to = input("Send test email to: ").strip()
    if to:
        if sender.connect():
            sender.send_email(to, "Test from Client Finder", "This is a test email.")
            sender.disconnect()
            print("[+] Done")
