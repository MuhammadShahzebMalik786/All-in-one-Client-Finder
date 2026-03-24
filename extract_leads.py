"""
Website Contact Extractor
Visits business websites, extracts emails and phone numbers using regex
pattern matching, deduplicates, and saves unique contacts to CSV.
"""

import csv
import os
import re
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import Config


class ContactExtractor:
    """Extracts email addresses and phone numbers from websites."""

    EMAIL_RE = re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    )
    PHONE_RE = re.compile(
        r"[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}"
    )

    # Domains to ignore when extracting emails
    JUNK_DOMAINS = {
        "example.com", "test.com", "email.com", "domain.com",
        "yoursite.com", "website.com", "company.com", "sentry.io",
        "w3.org", "schema.org", "googleapis.com", "google.com",
        "facebook.com", "twitter.com", "instagram.com", "linkedin.com",
        "wixpress.com", "wordpress.com", "squarespace.com",
    }

    CONTACT_KEYWORDS = ["contact", "about", "team", "reach", "connect", "get-in-touch"]

    FIELDNAMES = [
        "company", "website", "emails", "phones",
        "contact_page", "source", "date_extracted",
    ]

    def __init__(self):
        self.config = Config()
        self.config.ensure_data_dir()
        self.output_file = os.path.join(self.config.DATA_DIR, "extracted_contacts.csv")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        })

    # ------------------------------------------------------------------
    # Core extraction
    # ------------------------------------------------------------------

    def extract_from_url(self, url, company_name="", source=""):
        """Visit a URL, extract emails & phones, return a contact dict."""
        if not url:
            return None

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        print(f"  [*] Scraping: {url}")

        contact = {
            "company": company_name,
            "website": url,
            "emails": set(),
            "phones": set(),
            "contact_page": "",
            "source": source,
            "date_extracted": datetime.now().strftime("%Y-%m-%d"),
        }

        try:
            resp = self.session.get(url, timeout=10, allow_redirects=True)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Extract from main page
            self._find_emails(resp.text, contact)
            self._find_phones(resp.text, contact)

            # Discover and visit contact / about pages on the same domain
            sub_links = self._find_contact_links(soup, url)
            for link in sub_links[:3]:
                time.sleep(1)
                try:
                    r = self.session.get(link, timeout=8)
                    if r.status_code == 200:
                        self._find_emails(r.text, contact)
                        self._find_phones(r.text, contact)
                        if not contact["contact_page"]:
                            contact["contact_page"] = link
                except Exception:
                    pass

            # Also try common paths if we still have no emails
            if not contact["emails"]:
                for path in ("/contact", "/contact-us", "/about", "/about-us"):
                    try:
                        r = self.session.get(urljoin(url, path), timeout=6)
                        if r.status_code == 200:
                            self._find_emails(r.text, contact)
                            self._find_phones(r.text, contact)
                    except Exception:
                        pass

        except Exception as e:
            print(f"  [!] Error scraping {url}: {e}")

        # Convert sets to semicolon-separated strings
        contact["emails"] = "; ".join(sorted(contact["emails"]))
        contact["phones"] = "; ".join(sorted(contact["phones"]))

        if contact["emails"] or contact["phones"]:
            print(f"  [+] Found: {contact['emails']} | {contact['phones']}")
        else:
            print("  [-] No contacts found")

        return contact

    def _find_emails(self, html_text, contact):
        """Extract valid email addresses from raw HTML text."""
        for email in self.EMAIL_RE.findall(html_text):
            email = email.lower().strip()
            domain = email.split("@")[1] if "@" in email else ""
            if domain in self.JUNK_DOMAINS:
                continue
            if email.endswith((".png", ".jpg", ".gif", ".svg", ".css", ".js")):
                continue
            contact["emails"].add(email)

    def _find_phones(self, html_text, contact):
        """Extract phone numbers from text (HTML tags stripped)."""
        clean = re.sub(r"<[^>]+>", " ", html_text)
        for phone in self.PHONE_RE.findall(clean):
            phone = phone.strip()
            digits = re.sub(r"[^\d]", "", phone)
            if 7 <= len(digits) <= 15:
                contact["phones"].add(phone)

    def _find_contact_links(self, soup, base_url):
        """Return unique same-domain links that look like contact pages."""
        links = set()
        base_domain = urlparse(base_url).netloc
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].lower()
            text = a_tag.get_text().lower()
            if any(kw in href or kw in text for kw in self.CONTACT_KEYWORDS):
                full = urljoin(base_url, a_tag["href"])
                if urlparse(full).netloc == base_domain:
                    links.add(full)
        return list(links)

    # ------------------------------------------------------------------
    # Batch processing from CSV files
    # ------------------------------------------------------------------

    def extract_from_csv(self, csv_path, url_column="website", name_column="name"):
        """Read a CSV, visit every website, and extract contacts."""
        if not os.path.exists(csv_path):
            print(f"[!] File not found: {csv_path}")
            return []

        contacts = []
        with open(csv_path, "r", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                url = row.get(url_column, "").strip()
                name = row.get(name_column, "").strip()
                if not url or url.startswith("https://www.linkedin.com"):
                    continue  # skip LinkedIn profile URLs
                c = self.extract_from_url(url, company_name=name, source=csv_path)
                if c and (c["emails"] or c["phones"]):
                    contacts.append(c)
                time.sleep(self.config.SCRAPE_DELAY)

        return contacts

    # ------------------------------------------------------------------
    # CSV persistence with deduplication
    # ------------------------------------------------------------------

    def save_contacts(self, contacts):
        """Append unique contacts to CSV (deduplicate by email set)."""
        existing = self._load_existing_emails()
        new = []
        for c in contacts:
            emails = c.get("emails", "")
            if emails and emails not in existing:
                new.append(c)
                existing.add(emails)

        if not new:
            print("[*] No new contacts to save")
            return 0

        write_header = not os.path.exists(self.output_file)
        with open(self.output_file, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=self.FIELDNAMES)
            if write_header:
                writer.writeheader()
            for c in new:
                writer.writerow({k: c.get(k, "") for k in self.FIELDNAMES})

        print(f"[+] Saved {len(new)} new contacts -> {self.output_file}")
        return len(new)

    def _load_existing_emails(self):
        emails = set()
        if os.path.exists(self.output_file):
            with open(self.output_file, "r", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    emails.add(row.get("emails", ""))
        return emails

    # ------------------------------------------------------------------
    # Public runner
    # ------------------------------------------------------------------

    def run(self):
        """Extract contacts from all lead CSVs in data/."""
        all_contacts = []

        gmaps = os.path.join(self.config.DATA_DIR, "google_maps_leads.csv")
        if os.path.exists(gmaps):
            print("\n[*] Extracting contacts from Google Maps leads...")
            all_contacts.extend(
                self.extract_from_csv(gmaps, url_column="website", name_column="name")
            )
        else:
            print("[*] No Google Maps leads found — skipping")

        linkedin = os.path.join(self.config.DATA_DIR, "linkedin_leads.csv")
        if os.path.exists(linkedin):
            print("\n[*] Checking LinkedIn leads for company websites...")
            all_contacts.extend(
                self.extract_from_csv(linkedin, url_column="website", name_column="name")
            )

        self.save_contacts(all_contacts)
        return all_contacts


# Allow standalone execution
if __name__ == "__main__":
    extractor = ContactExtractor()
    print("\n=== Website Contact Extractor ===")
    print("1. Extract from lead CSVs in data/")
    print("2. Extract from a single URL")
    choice = input("Choice [1]: ").strip() or "1"

    if choice == "2":
        url = input("Website URL: ").strip()
        name = input("Company name (optional): ").strip()
        c = extractor.extract_from_url(url, company_name=name, source="manual")
        if c:
            extractor.save_contacts([c])
    else:
        extractor.run()
