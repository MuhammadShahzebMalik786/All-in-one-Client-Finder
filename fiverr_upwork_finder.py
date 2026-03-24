"""
Fiverr & Upwork Client Finder
Extracts active client profiles and their project history
to build a targeted outreach list.
"""

import csv
import re
import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config


class FreelanceClientFinder:
    """Extract client info from Fiverr & Upwork."""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    def __init__(self):
        self.config = Config()
        self.config.ensure_data_dir()
        self.clients = []

    def search_upwork_clients(self, keywords: List[str], limit: int = 50) -> List[Dict]:
        """
        Search Upwork for active clients (public profiles).
        Args:
            keywords: Search terms (e.g., ['need automation', 'lead generation'])
            limit: Max results
        """
        print(f"\n  === Upwork Client Search ===")
        upwork_clients = []

        try:
            for keyword in keywords:
                print(f"  Searching Upwork: '{keyword}'...")
                # Note: This uses Upwork's public search (rate-limited)
                search_url = (
                    f"https://www.upwork.com/ab/find-work/best-matches"
                    f"?q={keyword}&sort=recency"
                )

                resp = requests.get(search_url, headers=self.HEADERS, timeout=10)
                soup = BeautifulSoup(resp.content, "html.parser")

                # Extract job postings with client info
                jobs = soup.find_all("div", class_="job-tile")

                for job in jobs[:limit]:
                    try:
                        # Extract client profile link
                        client_link = job.find(
                            "a", href=re.compile(r"/o/[0-9]+/")
                        )
                        title = job.find("h2")
                        budget = job.find(class_="budget")

                        if client_link and title:
                            client = {
                                "platform": "Upwork",
                                "client_name": client_link.text.strip(),
                                "client_url": client_link.get("href", ""),
                                "job_title": title.text.strip(),
                                "budget": budget.text.strip() if budget else "N/A",
                                "posted_date": datetime.now().strftime("%Y-%m-%d"),
                                "email": None,  # Will be extracted from profile
                                "category": self._infer_category(title.text),
                            }
                            upwork_clients.append(client)
                            print(
                                f"    ✓ Found: {client['client_name'][:30]} "
                                f"({client['job_title'][:40]})"
                            )
                    except Exception as e:
                        continue

        except Exception as e:
            print(f"  [!] Upwork search error: {e}")

        return upwork_clients

    def search_fiverr_clients(self, keywords: List[str], limit: int = 50) -> List[Dict]:
        """
        Search Fiverr for active buyers.
        Args:
            keywords: Search terms
            limit: Max results
        """
        print(f"\n  === Fiverr Buyer Search ===")
        fiverr_clients = []

        try:
            for keyword in keywords:
                print(f"  Searching Fiverr: '{keyword}'...")

                # Fiverr has public buyer requests
                search_url = (
                    f"https://www.fiverr.com/search/gigs"
                    f"?query={keyword}&source=pagination"
                )

                resp = requests.get(search_url, headers=self.HEADERS, timeout=10)
                soup = BeautifulSoup(resp.content, "html.parser")

                # Note: Fiverr heavily uses JS, so scraping is limited
                # Alternative: Use listed seller recommendations that match

                gigs = soup.find_all("div", class_="gig-card")

                for gig in gigs[:limit]:
                    try:
                        seller_link = gig.find("a", class_="seller-avatar")
                        title = gig.find("h3")

                        if seller_link and title:
                            client = {
                                "platform": "Fiverr",
                                "seller_name": seller_link.get("aria-label", "").strip(),
                                "seller_url": seller_link.get("href", ""),
                                "service_title": title.text.strip(),
                                "posted_date": datetime.now().strftime("%Y-%m-%d"),
                                "email": None,
                                "category": self._infer_category(title.text),
                            }
                            fiverr_clients.append(client)
                            print(
                                f"    ✓ Found: {client['seller_name'][:30]} "
                                f"({client['service_title'][:40]})"
                            )
                    except Exception as e:
                        continue

        except Exception as e:
            print(f"  [!] Fiverr search error: {e}")

        return fiverr_clients

    def _infer_category(self, text: str) -> str:
        """Infer industry category from job title."""
        text_lower = text.lower()

        categories = {
            "automation": [
                "automat",
                "workflow",
                "process",
                "rpa",
                "zapier",
                "integr",
            ],
            "leads": ["lead", "generat", "prospecт", "outreach", "scrape"],
            "marketing": [
                "market",
                "seo",
                "social",
                "content",
                "campaign",
                "email",
            ],
            "development": ["develop", "code", "app", "web", "software", "python"],
            "design": ["design", "graphic", "ui", "ux", "web design"],
            "sales": ["sales", "crm", "pipeline", "close"],
            "other": [],
        }

        for category, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                return category

        return "other"

    def save_clients(self, clients: List[Dict], filename: str = None):
        """Save clients to CSV."""
        if not clients:
            print("  [!] No clients to save")
            return

        filename = filename or "freelance_platform_clients.csv"
        filepath = os.path.join(self.config.DATA_DIR, filename)

        keys = list(clients[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=keys)
            writer.writeheader()
            writer.writerows(clients)

        print(f"\n  ✓ Saved {len(clients)} clients to {filename}")

    def get_outreach_targets(self) -> List[Dict]:
        """Generate prioritized outreach targets from all platforms."""
        print("\n  === Building Outreach Target List ===\n")

        # Define search keywords related to your services
        automation_keywords = [
            "need automation",
            "lead generation",
            "data extraction",
            "tasks automation",
            "workflow setup",
            "email automation",
            "web scraping",
            "bot development",
        ]

        # Search Upwork and Fiverr
        upwork_clients = self.search_upwork_clients(automation_keywords[:3], limit=30)
        fiverr_clients = self.search_fiverr_clients(automation_keywords[:3], limit=30)

        all_clients = upwork_clients + fiverr_clients

        # Score by relevance
        for client in all_clients:
            relevance_score = 0

            # High-value categories
            if client.get("category") in ["automation", "leads", "marketing"]:
                relevance_score += 3

            # Budget indication (if available)
            if "k" in str(client.get("budget", "")).lower():
                relevance_score += 2

            client["relevance_score"] = relevance_score

        # Sort by relevance
        all_clients.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        self.save_clients(all_clients)
        self.clients = all_clients

        return all_clients


if __name__ == "__main__":
    finder = FreelanceClientFinder()
    targets = finder.get_outreach_targets()

    print(f"\n  Found {len(targets)} potential clients")
    if targets:
        print(f"\n  Top 5 targets:")
        for i, client in enumerate(targets[:5], 1):
            print(
                f"    {i}. {client.get('client_name') or client.get('seller_name')} "
                f"({client.get('category')})"
            )
