"""
Automatic Client Finder — Unattended Pipeline
Runs the full lead-generation + email-outreach pipeline automatically.
Designed to be triggered by Task Scheduler / .bat on PC startup.

Logic:
  1. Check last_run.txt — skip if < 12 hours since last run
  2. Find leads on LinkedIn (default queries)
  3. Find businesses on Google Maps (default categories/locations)
  4. Extract emails/phones from discovered websites
  5. Generate personalized emails for NEW contacts only
  6. Send emails only to people NOT already emailed (marked in sent_emails.csv)
  7. Write timestamp to last_run.txt
"""

import csv
import os
import random
import sys
import traceback
from datetime import datetime, timedelta

# --------------- path setup ---------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "auto emailing system"))

from config import Config
from linkdln_company_finder import LinkedInFinder
from google_client_finder import GoogleMapsFinder
from extract_leads import ContactExtractor
from personalize_email_gen import EmailGenerator
from smtp_mail_sender import EmailSender

# --------------- settings ---------------
COOLDOWN_HOURS = 12
LAST_RUN_FILE = os.path.join(BASE_DIR, "data", "last_run.txt")
LOG_FILE = os.path.join(BASE_DIR, "data", "auto_run.log")


# ================================================================== #
#  Logging                                                            #
# ================================================================== #

def log(msg):
    """Print and append to log file."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


# ================================================================== #
#  Cooldown check                                                     #
# ================================================================== #

def should_run():
    """Return True if 12+ hours passed since last run (or first run)."""
    if not os.path.exists(LAST_RUN_FILE):
        return True
    try:
        with open(LAST_RUN_FILE, "r") as fh:
            last = datetime.fromisoformat(fh.read().strip())
        elapsed = datetime.now() - last
        if elapsed >= timedelta(hours=COOLDOWN_HOURS):
            return True
        remaining = timedelta(hours=COOLDOWN_HOURS) - elapsed
        hours, remainder = divmod(int(remaining.total_seconds()), 3600)
        mins = remainder // 60
        log(f"Cooldown active — last run was {elapsed.seconds // 3600}h ago. "
            f"Next run in {hours}h {mins}m. Exiting.")
        return False
    except Exception:
        return True


def mark_run():
    """Save current timestamp as last run time."""
    with open(LAST_RUN_FILE, "w") as fh:
        fh.write(datetime.now().isoformat())


# ================================================================== #
#  Pipeline steps                                                     #
# ================================================================== #

def step_linkedin():
    """Step 1: Find leads on LinkedIn (skipped if no credentials)."""
    log("STEP 1/5 — LinkedIn Lead Finder")
    config = Config()
    if not config.LINKEDIN_EMAIL or not config.LINKEDIN_PASSWORD:
        log("  LinkedIn credentials not configured — skipping")
        return
    finder = LinkedInFinder()
    queries = [
        "CEO startup needing mobile app",
        "Founder SaaS company",
        "CTO ecommerce needing automation",
        "Managing Director logistics tech",
        "Founder digital agency",
        "CTO fintech startup",
        "CEO healthcare tech company",
    ]
    # Pick a random subset of 4 each run for variety
    selected = random.sample(queries, min(4, len(queries)))
    try:
        leads = finder.run(selected)
        log(f"  LinkedIn: found {len(leads)} leads")
    except Exception as e:
        log(f"  LinkedIn failed: {e}")


def step_google_maps():
    """Step 2: Find businesses via AI-powered search."""
    log("STEP 2/5 — AI Business Finder")
    finder = GoogleMapsFinder()

    # Rotate categories and locations each run for variety
    all_cats = list(finder.DEFAULT_CATEGORIES)
    all_locs = list(finder.DEFAULT_LOCATIONS)
    random.shuffle(all_cats)
    random.shuffle(all_locs)

    # Pick 3 categories and 2 locations each run (different combo each time)
    cats = all_cats[:3]
    locs = all_locs[:2]
    log(f"  Categories: {cats}")
    log(f"  Locations: {locs}")

    try:
        businesses = finder.run(categories=cats, locations=locs)
        log(f"  Business Finder: found {len(businesses)} businesses")
    except Exception as e:
        log(f"  Business Finder failed: {e}")


def step_extract_contacts():
    """Step 3: Extract emails/phones from websites."""
    log("STEP 3/5 — Website Contact Extractor")
    extractor = ContactExtractor()
    try:
        contacts = extractor.run()
        log(f"  Extractor: found {len(contacts)} contacts with email/phone")
    except Exception as e:
        log(f"  Extractor failed: {e}")


def step_generate_emails():
    """Step 4: Generate personalized emails for new contacts only."""
    log("STEP 4/5 — Email Generation")
    config = Config()
    contacts_file = os.path.join(config.DATA_DIR, "extracted_contacts.csv")
    drafts_file = os.path.join(config.DATA_DIR, "email_drafts.csv")
    sent_log = os.path.join(config.DATA_DIR, "sent_emails.csv")

    if not os.path.exists(contacts_file):
        log("  No contacts file yet — skipping email generation")
        return

    # Load contacts with emails
    contacts = []
    with open(contacts_file, "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("emails", "").strip():
                contacts.append(row)

    if not contacts:
        log("  No contacts with email addresses — skipping")
        return

    # Load already-drafted emails
    drafted = set()
    if os.path.exists(drafts_file):
        with open(drafts_file, "r", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                drafted.add(row.get("to_email", ""))

    # Load already-sent emails (these are MARKED — never contact again)
    sent = set()
    if os.path.exists(sent_log):
        with open(sent_log, "r", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                sent.add(row.get("email", ""))

    # Filter to truly new contacts
    new_contacts = []
    for c in contacts:
        primary_email = c["emails"].split(";")[0].strip()
        if primary_email not in drafted and primary_email not in sent:
            new_contacts.append(c)

    if not new_contacts:
        log("  All contacts already drafted/sent — nothing new")
        return

    log(f"  Generating emails for {len(new_contacts)} new contacts...")

    generator = EmailGenerator()
    drafts = []

    # Enrich from Google Maps data if available
    gmaps_file = os.path.join(config.DATA_DIR, "google_maps_leads.csv")
    gmaps_lookup = {}
    if os.path.exists(gmaps_file):
        with open(gmaps_file, "r", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                w = row.get("website", "").strip()
                if w:
                    gmaps_lookup[w] = row

    for contact in new_contacts:
        primary_email = contact["emails"].split(";")[0].strip()
        lead_info = {
            "name": contact.get("company", ""),
            "company": contact.get("company", ""),
            "category": contact.get("source", ""),
            "about": "",
        }

        # Enrich from Google Maps
        website = contact.get("website", "")
        if website in gmaps_lookup:
            gm = gmaps_lookup[website]
            lead_info["name"] = gm.get("name", lead_info["name"])
            lead_info["company"] = gm.get("name", lead_info["company"])
            lead_info["category"] = gm.get("search_query", lead_info["category"])

        try:
            result = generator.generate_email(lead_info)
            drafts.append({
                "to_email": primary_email,
                "company": lead_info["company"],
                "subject": result["subject"],
                "body": result["body"],
                "method": result["method"],
                "date_generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
            log(f"    Draft: {primary_email} | {result['subject']}")
        except Exception as e:
            log(f"    Failed for {primary_email}: {e}")

    if drafts:
        fieldnames = ["to_email", "company", "subject", "body", "method", "date_generated"]
        write_header = not os.path.exists(drafts_file)
        with open(drafts_file, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerows(drafts)
        log(f"  Generated {len(drafts)} new email drafts")
    else:
        log("  No new drafts generated")


def step_send_emails():
    """Step 5: Send all unsent email drafts. Already-sent are skipped."""
    log("STEP 5/5 — Sending Emails")
    config = Config()
    drafts_file = os.path.join(config.DATA_DIR, "email_drafts.csv")

    if not os.path.exists(drafts_file):
        log("  No drafts to send — skipping")
        return

    drafts = []
    with open(drafts_file, "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            drafts.append(row)

    if not drafts:
        log("  No drafts found — skipping")
        return

    sender = EmailSender()
    if not sender.connect():
        log("  SMTP connection failed — cannot send emails")
        return

    # send_bulk already checks sent_emails.csv and skips duplicates
    sent_count, failed_count = sender.send_bulk(drafts)
    sender.disconnect()

    log(f"  Emails sent: {sent_count}, failed: {failed_count}")


# ================================================================== #
#  Main                                                               #
# ================================================================== #

def run_pipeline(skip_linkedin=False):
    """Execute the full automated pipeline."""
    config = Config()
    config.ensure_data_dir()

    log("=" * 60)
    log("AUTOMATIC CLIENT FINDER — Pipeline Starting")
    log("=" * 60)

    steps = [
        ("LinkedIn",    step_linkedin),
        ("Google Maps", step_google_maps),
        ("Extractor",   step_extract_contacts),
        ("Email Gen",   step_generate_emails),
        ("Send",        step_send_emails),
    ]

    for name, func in steps:
        if skip_linkedin and name == "LinkedIn":
            log("STEP 1/5 — LinkedIn Lead Finder")
            log("  Skipped (--no-linkedin flag)")
            log("")
            continue
        try:
            func()
        except Exception as e:
            log(f"  {name} step crashed: {e}")
            traceback.print_exc()
        log("")  # blank line between steps

    mark_run()
    log("Pipeline complete. Next run allowed after 12 hours.")
    log("=" * 60)


if __name__ == "__main__":
    Config.ensure_data_dir()

    skip_li = "--no-linkedin" in sys.argv

    if not should_run():
        sys.exit(0)

    run_pipeline(skip_linkedin=skip_li)
