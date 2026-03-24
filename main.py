"""
Client Finder App — Main Orchestrator
CLI menu that ties together all modules:
  1. LinkedIn lead scraping
  2. Google Maps business discovery
  3. Website contact extraction
  4. AI-powered personalized email generation
  5. SMTP bulk email sending
"""

import csv
import os
import sys
from datetime import datetime

# --------------- path setup ---------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "auto emailing system"))

from config import Config
from linkdln_company_finder import LinkedInFinder
from google_client_finder import GoogleMapsFinder
from extract_leads import ContactExtractor


# ================================================================== #
#  Helpers                                                            #
# ================================================================== #

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def banner():
    print(r"""
 ╔═══════════════════════════════════════════════════╗
 ║           C L I E N T   F I N D E R              ║
 ║       Automated Lead Generation & Outreach       ║
 ╚═══════════════════════════════════════════════════╝
    """)


def menu():
    print("""  ┌──────────────────────────────────────┐
  │  1.  Find Leads on LinkedIn          │
  │  2.  Find Businesses on Google Maps  │
  │  3.  Extract Contacts from Websites  │
  │  4.  Generate Personalized Emails    │
  │  5.  Send Emails                     │
  │  6.  Run Full Pipeline               │
  │  ──────────────────────────────────  │
  │  7.  Find Clients on Fiverr/Upwork   │
  │  8.  Generate AI Sales Pitches       │
  │  9.  Test Local Model (Ollama)       │
  │  ──────────────────────────────────  │
  │  10. View Statistics                 │
  │  11. Import Leads from CSV           │
  │  0.  Exit                            │
  └──────────────────────────────────────┘
    """)


def pause():
    input("\n  Press Enter to continue...")


def get_stats():
    """Return dict of label -> row count for each data CSV."""
    config = Config()
    config.ensure_data_dir()
    files = {
        "LinkedIn Leads":      "linkedin_leads.csv",
        "Google Maps Leads":   "google_maps_leads.csv",
        "Extracted Contacts":  "extracted_contacts.csv",
        "Freelance Clients":   "freelance_platform_clients.csv",
        "Generated Pitches":   "generated_pitches.csv",
        "Email Drafts":        "email_drafts.csv",
        "Sent Emails":         "sent_emails.csv",
    }
    stats = {}
    for label, fname in files.items():
        fp = os.path.join(config.DATA_DIR, fname)
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as fh:
                count = sum(1 for _ in csv.reader(fh)) - 1
            stats[label] = max(count, 0)
        else:
            stats[label] = 0
    return stats


# ================================================================== #
#  Menu actions                                                       #
# ================================================================== #

def action_linkedin():
    print("\n  === LinkedIn Lead Finder ===")
    finder = LinkedInFinder()

    print("  Enter search queries (one per line, empty line to start):")
    print("  Examples: 'CEO marketing agency', 'Founder tech startup'")
    queries = []
    while True:
        q = input("    > ").strip()
        if not q:
            break
        queries.append(q)

    if not queries:
        print("  [*] Using default queries...")
    finder.run(queries or None)


def action_google_maps():
    print("\n  === Google Maps Business Finder ===")
    finder = GoogleMapsFinder()

    print("  Enter categories (one per line, empty to use defaults):")
    print("  Examples: 'marketing agency', 'software company'")
    categories = []
    while True:
        c = input("    Category > ").strip()
        if not c:
            break
        categories.append(c)

    print("  Enter locations (one per line, empty to use defaults):")
    print("  Examples: 'New York, USA', 'London, UK'")
    locations = []
    while True:
        loc = input("    Location > ").strip()
        if not loc:
            break
        locations.append(loc)

    finder.run(
        categories=categories or None,
        locations=locations or None,
    )


def action_extract():
    print("\n  === Website Contact Extractor ===")
    extractor = ContactExtractor()

    print("  1. Extract from lead CSVs in data/")
    print("  2. Extract from a custom CSV file")
    print("  3. Extract from a single URL")
    choice = input("  Choice [1]: ").strip() or "1"

    if choice == "1":
        extractor.run()
    elif choice == "2":
        path = input("  CSV file path: ").strip()
        url_col = input("  URL column name [website]: ").strip() or "website"
        name_col = input("  Name column name [name]: ").strip() or "name"
        contacts = extractor.extract_from_csv(path, url_column=url_col, name_column=name_col)
        extractor.save_contacts(contacts)
    elif choice == "3":
        url = input("  Website URL: ").strip()
        name = input("  Company name (optional): ").strip()
        c = extractor.extract_from_url(url, company_name=name, source="manual")
        if c:
            extractor.save_contacts([c])


def action_generate_emails():
    print("\n  === Personalized Email Generator ===")

    from personalize_email_gen import EmailGenerator

    config = Config()
    config.ensure_data_dir()
    generator = EmailGenerator()

    contacts_file = os.path.join(config.DATA_DIR, "extracted_contacts.csv")
    drafts_file = os.path.join(config.DATA_DIR, "email_drafts.csv")

    if not os.path.exists(contacts_file):
        print("  [!] No extracted contacts found. Run contact extraction first (option 3).")
        return

    # Load contacts that have emails
    contacts = []
    with open(contacts_file, "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("emails", "").strip():
                contacts.append(row)

    if not contacts:
        print("  [!] No contacts with email addresses found")
        return

    # Load already-drafted emails to avoid duplicates
    drafted = set()
    if os.path.exists(drafts_file):
        with open(drafts_file, "r", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                drafted.add(row.get("to_email", ""))

    print(f"  [*] {len(contacts)} contacts with emails, {len(drafted)} already drafted")

    drafts = []
    for contact in contacts:
        primary_email = contact["emails"].split(";")[0].strip()
        if primary_email in drafted:
            continue

        lead_info = {
            "name": contact.get("company", ""),
            "company": contact.get("company", ""),
            "category": contact.get("source", ""),
            "about": "",
        }

        # Try to enrich with Google Maps data
        gmaps_file = os.path.join(config.DATA_DIR, "google_maps_leads.csv")
        if os.path.exists(gmaps_file):
            website = contact.get("website", "")
            with open(gmaps_file, "r", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    if row.get("website", "") == website:
                        lead_info["name"] = row.get("name", lead_info["name"])
                        lead_info["company"] = row.get("name", lead_info["company"])
                        lead_info["category"] = row.get("search_query", lead_info["category"])
                        break

        print(f"\n  [*] Generating email for: {lead_info['company'] or primary_email}")
        result = generator.generate_email(lead_info)

        drafts.append({
            "to_email": primary_email,
            "company": lead_info["company"],
            "subject": result["subject"],
            "body": result["body"],
            "method": result["method"],
            "date_generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        print(f"    Subject: {result['subject']}")
        print(f"    Method:  {result['method']}")

    if drafts:
        fieldnames = ["to_email", "company", "subject", "body", "method", "date_generated"]
        write_header = not os.path.exists(drafts_file)
        with open(drafts_file, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerows(drafts)
        print(f"\n  [+] Generated {len(drafts)} email drafts -> {drafts_file}")
    else:
        print("  [*] No new emails to generate")


def action_send_emails():
    print("\n  === Email Sender ===")

    from smtp_mail_sender import EmailSender

    config = Config()
    drafts_file = os.path.join(config.DATA_DIR, "email_drafts.csv")

    if not os.path.exists(drafts_file):
        print("  [!] No email drafts found. Generate emails first (option 4).")
        return

    drafts = []
    with open(drafts_file, "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            drafts.append(row)

    if not drafts:
        print("  [!] No drafts to send")
        return

    print(f"  [*] {len(drafts)} email drafts loaded")
    print(f"\n  Preview (first email):")
    print(f"    To:      {drafts[0].get('to_email')}")
    print(f"    Subject: {drafts[0].get('subject')}")
    body_preview = drafts[0].get("body", "")[:200]
    print(f"    Body:    {body_preview}...")

    confirm = input(f"\n  Send {len(drafts)} emails? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("  [*] Cancelled")
        return

    sender = EmailSender()
    sent, failed = sender.send_bulk(drafts)
    sender.disconnect()


def action_full_pipeline():
    print("\n  === Full Pipeline ===")
    print("  Steps: LinkedIn -> Google Maps -> Extract Contacts -> Generate Emails -> Send")
    confirm = input("  Continue? (yes/no): ").strip().lower()
    if confirm != "yes":
        return

    steps = [
        ("1/5  LinkedIn Lead Finder",       action_linkedin),
        ("2/5  Google Maps Business Finder", action_google_maps),
        ("3/5  Contact Extraction",          action_extract),
        ("4/5  Email Generation",            action_generate_emails),
        ("5/5  Send Emails",                 action_send_emails),
    ]

    for label, func in steps:
        print(f"\n  --- Step {label} ---")
        try:
            func()
        except KeyboardInterrupt:
            print("\n  [*] Step interrupted")
        except Exception as e:
            print(f"  [!] Step failed: {e}")

    print("\n  === Pipeline Complete ===")


def action_fiverr_upwork():
    """Find client prospects on Fiverr/Upwork."""
    print("\n  === Fiverr/Upwork Client Finder ===")
    print("\n  This extracts active client profiles looking for services like yours.")
    print("  Results will be saved to 'freelance_platform_clients.csv'\n")

    try:
        from fiverr_upwork_finder import FreelanceClientFinder

        finder = FreelanceClientFinder()
        targets = finder.get_outreach_targets()

        if targets:
            print(f"\n  ✓ Found {len(targets)} potential clients")
            print("\n  Top prospects (by relevance):")
            for i, client in enumerate(targets[:5], 1):
                name = client.get("client_name") or client.get("seller_name", "Unknown")
                category = client.get("category", "N/A")
                print(f"    {i}. {name} ({category})")
        else:
            print("\n  [!] No clients found. Try again later.")

    except Exception as e:
        print(f"  [!] Error: {e}")


def action_generate_pitches():
    """Generate AI sales pitches for prospects."""
    print("\n  === AI Pitch Generator ===\n")

    try:
        # Import from auto emailing system
        sys.path.insert(0, os.path.join(BASE_DIR, "auto emailing system"))
        from pitch_generator import PitchGenerator

        generator = PitchGenerator()
        config = Config()

        # Load freelance clients
        freelance_file = os.path.join(
            config.DATA_DIR, "freelance_platform_clients.csv"
        )

        if not os.path.exists(freelance_file):
            print("  [!] No freelance clients found. Run Fiverr/Upwork finder first.")
            return

        prospects = []
        with open(freelance_file, "r", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                name = row.get("client_name") or row.get("seller_name", "Prospect")
                prospects.append({
                    "name": name,
                    "company": row.get("service_title", ""),
                    "industry": row.get("category", ""),
                    "context": {
                        "pain_point": "manual lead generation and market research",
                        "metric_value": "500 verified leads",
                    },
                })

        if not prospects:
            print("  [!] No valid prospects found")
            return

        pitch_types = ["automation", "leads", "integration", "email_outreach"]
        print("  Pitch types:")
        for i, ptype in enumerate(pitch_types, 1):
            print(f"    {i}. {ptype}")

        choice = input("\n  Choose pitch type [1]: ").strip() or "1"
        pitch_type = pitch_types[int(choice) - 1] if choice.isdigit() else "automation"

        num_to_gen = min(10, len(prospects))
        confirm_num = input(f"\n  Generate pitches for first {num_to_gen} prospects? (yes/no): ").strip()
        if confirm_num.lower() != "yes":
            print("  [*] Cancelled")
            return

        print(f"\n  Generating {pitch_type} pitches...\n")
        pitches = generator.batch_generate_pitches(prospects[:num_to_gen], pitch_type)

        # Save pitches
        pitches_file = os.path.join(config.DATA_DIR, "generated_pitches.csv")
        fieldnames = ["name", "company", "industry", "subject", "body"]

        with open(pitches_file, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for p in pitches:
                writer.writerow({
                    "name": p.get("name"),
                    "company": p.get("company"),
                    "industry": p.get("industry"),
                    "subject": p["pitch"].get("subject", ""),
                    "body": p["pitch"].get("body", ""),
                })

        print(f"\n  ✓ {len(pitches)} pitches generated -> {pitches_file}")

    except Exception as e:
        print(f"  [!] Error: {e}")
        import traceback
        traceback.print_exc()


def action_test_local_model():
    """Test local Ollama model setup."""
    print("\n  === Local Model Status ===\n")

    try:
        from local_model_handler import LocalModelHandler

        handler = LocalModelHandler(model="phi")

        if handler.is_available():
            print("  ✓ Ollama is running locally")
            print(f"  Model: {handler.model}")
            print(f"  URL:   {handler.base_url}")

            print("\n  Testing model generation...")
            test_prompt = "Summarize in 2 sentences: Automation saves time and reduces errors."
            result = handler.generate(test_prompt)

            if result:
                print(f"\n  Model response:\n    {result}\n")
                print("  ✓ Local model ready as AI fallback!")
            else:
                print("  [!] Model generation failed (no GPU acceleration?)")
        else:
            print("  [!] Ollama not running\n")
            print("  To enable local CPU-based AI fallback:")
            print("    1. Download Ollama from https://ollama.ai")
            print("    2. Install and run: ollama serve")
            print("    3. In another terminal: ollama run phi")
            print("    4. Come back here and try again")

    except ImportError:
        print("  [!] local_model_handler not found")
    except Exception as e:
        print(f"  [!] Error: {e}")


def action_stats():
    print("\n  === Statistics ===\n")
    stats = get_stats()
    for label, count in stats.items():
        bar = "█" * min(count, 50)
        print(f"    {label:25s} | {count:5d} | {bar}")
    print()


def action_import():
    print("\n  === Import Leads from CSV ===")
    filepath = input("  CSV file path: ").strip()
    if not os.path.exists(filepath):
        print(f"  [!] File not found: {filepath}")
        return

    config = Config()
    config.ensure_data_dir()

    print("  Import as:")
    print("    1. LinkedIn leads")
    print("    2. Google Maps leads")
    choice = input("  Choice [1]: ").strip() or "1"

    dest_name = "linkedin_leads.csv" if choice == "1" else "google_maps_leads.csv"
    dest_path = os.path.join(config.DATA_DIR, dest_name)

    import shutil
    shutil.copy2(filepath, dest_path)
    print(f"  [+] Imported -> {dest_path}")


# ================================================================== #
#  Entry point                                                        #
# ================================================================== #

def main():
    config = Config()
    config.ensure_data_dir()

    actions = {
        "1": action_linkedin,
        "2": action_google_maps,
        "3": action_extract,
        "4": action_generate_emails,
        "5": action_send_emails,
        "6": action_full_pipeline,
        "7": action_fiverr_upwork,
        "8": action_generate_pitches,
        "9": action_test_local_model,
        "10": action_stats,
        "11": action_import,
        "0": lambda: sys.exit(0),
    }

    while True:
        clear()
        banner()

        # Show quick stats bar
        stats = get_stats()
        total = sum(stats.values())
        if total > 0:
            li = stats.get("LinkedIn Leads", 0)
            gm = stats.get("Google Maps Leads", 0)
            co = stats.get("Extracted Contacts", 0)
            fc = stats.get("Freelance Clients", 0)
            dr = stats.get("Email Drafts", 0)
            se = stats.get("Sent Emails", 0)
            print(f"   Leads: {li + gm}  |  Contacts: {co}  |  Freelance: {fc}  |  Drafts: {dr}  |  Sent: {se}\n")

        menu()
        choice = input("  Select option: ").strip()

        action = actions.get(choice)
        if action:
            try:
                action()
            except KeyboardInterrupt:
                print("\n  [*] Interrupted")
            except Exception as e:
                print(f"\n  [!] Error: {e}")
            pause()
        else:
            print("  [!] Invalid option")
            pause()


if __name__ == "__main__":
    main()
