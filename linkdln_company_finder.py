"""
LinkedIn Lead Finder
Finds potential clients and decision-makers on LinkedIn using linkedin-api.
Targets: Founders, CEOs, MDs, HR Managers, Tech Leads, Engineering Managers.
"""

import csv
import os
import time
from datetime import datetime

from config import Config


class LinkedInFinder:
    """Scrapes LinkedIn for decision-makers at target companies."""

    TARGET_ROLES = [
        "founder", "co-founder", "ceo", "chief executive officer",
        "managing director", "president", "owner",
        "cto", "chief technology officer", "vp of engineering",
        "hr director", "hr manager", "head of hr", "head of people",
        "tech lead", "engineering manager", "director of engineering",
        "head of technology", "partner", "director of operations",
        "software engineering manager",
    ]

    FIELDNAMES = [
        "name", "title", "company", "location", "linkedin_url",
        "industry", "about", "website", "source", "date_found", "search_query",
    ]

    def __init__(self):
        self.config = Config()
        self.config.ensure_data_dir()
        self.api = None
        self.output_file = os.path.join(self.config.DATA_DIR, "linkedin_leads.csv")

    def connect(self):
        """Connect to LinkedIn using credentials from .env."""
        if not self.config.LINKEDIN_EMAIL or not self.config.LINKEDIN_PASSWORD:
            print("[!] Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env")
            return False
        try:
            from linkedin_api import Linkedin

            self.api = Linkedin(
                self.config.LINKEDIN_EMAIL,
                self.config.LINKEDIN_PASSWORD,
            )
            print("[+] Connected to LinkedIn")
            return True
        except ImportError:
            print("[!] linkedin-api not installed. Run: pip install linkedin-api")
            return False
        except Exception as e:
            print(f"[!] LinkedIn connection failed: {e}")
            return False

    def _is_decision_maker(self, headline):
        """Check if headline contains a target decision-maker role."""
        if not headline:
            return False
        hl = headline.lower()
        return any(role in hl for role in self.TARGET_ROLES)

    def search_leads(self, keywords, limit=20):
        """Search LinkedIn for people matching keywords, filter by role."""
        if not self.api and not self.connect():
            return []

        print(f"\n[*] Searching LinkedIn: '{keywords}' (limit {limit})")
        leads = []

        try:
            people = self.api.search_people(keywords=keywords, limit=limit)

            for person in people:
                name = person.get("name", "Unknown")
                headline = (
                    person.get("jobtitle", "")
                    or person.get("headline", "")
                    or ""
                )
                location = person.get("location", "")
                public_id = person.get("public_id", "")

                if not self._is_decision_maker(headline):
                    continue

                lead = {
                    "name": name,
                    "title": headline,
                    "company": "",
                    "location": location,
                    "linkedin_url": (
                        f"https://www.linkedin.com/in/{public_id}"
                        if public_id
                        else ""
                    ),
                    "industry": "",
                    "about": "",
                    "website": "",
                    "source": "linkedin",
                    "date_found": datetime.now().strftime("%Y-%m-%d"),
                    "search_query": keywords,
                }

                # Fetch full profile for richer data
                if public_id:
                    time.sleep(self.config.LINKEDIN_DELAY)
                    try:
                        profile = self.api.get_profile(public_id)
                        if profile:
                            exps = profile.get("experience", [])
                            if exps:
                                lead["company"] = exps[0].get("companyName", "")
                            lead["about"] = (profile.get("summary", "") or "")[:500]
                            lead["industry"] = profile.get("industryName", "")
                    except Exception:
                        pass  # Profile detail fetch is best-effort

                leads.append(lead)
                print(f"  [+] {name} | {headline}")
                time.sleep(self.config.LINKEDIN_DELAY)

        except Exception as e:
            print(f"[!] LinkedIn search error: {e}")

        print(f"[+] Found {len(leads)} decision-makers")
        return leads

    # ------------------------------------------------------------------
    # CSV persistence with deduplication
    # ------------------------------------------------------------------

    def save_leads(self, leads):
        """Append new leads to CSV, skip duplicates by LinkedIn URL."""
        existing = self._load_existing_urls()
        new = [
            l for l in leads
            if l.get("linkedin_url") and l["linkedin_url"] not in existing
        ]

        if not new:
            print("[*] No new LinkedIn leads to save")
            return 0

        write_header = not os.path.exists(self.output_file)
        with open(self.output_file, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=self.FIELDNAMES)
            if write_header:
                writer.writeheader()
            for lead in new:
                writer.writerow({k: lead.get(k, "") for k in self.FIELDNAMES})

        print(f"[+] Saved {len(new)} new leads -> {self.output_file}")
        return len(new)

    def _load_existing_urls(self):
        urls = set()
        if os.path.exists(self.output_file):
            with open(self.output_file, "r", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    urls.add(row.get("linkedin_url", ""))
        return urls

    # ------------------------------------------------------------------
    # Public runner
    # ------------------------------------------------------------------

    def run(self, queries=None):
        """Run LinkedIn lead search with given or default queries."""
        if queries is None:
            queries = [
                "CEO marketing agency",
                "Founder tech startup",
                "Managing Director software company",
                "CTO ecommerce",
                "Founder digital agency",
            ]

        all_leads = []
        for q in queries:
            leads = self.search_leads(q, limit=15)
            all_leads.extend(leads)
            time.sleep(5)  # cooldown between queries

        self.save_leads(all_leads)
        return all_leads


# Allow standalone execution
if __name__ == "__main__":
    finder = LinkedInFinder()
    print("\n=== LinkedIn Lead Finder ===")
    print("Enter search queries (one per line, empty line to start):")
    queries = []
    while True:
        q = input("> ").strip()
        if not q:
            break
        queries.append(q)
    finder.run(queries or None)
