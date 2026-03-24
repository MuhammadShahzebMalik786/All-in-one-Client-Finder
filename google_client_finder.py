"""
Business Finder
Discovers businesses using AI (OpenRouter/Gemini) to find real companies,
then scrapes their websites for contact details. Saves to CSV.
"""

import csv
import json
import os
import re
import time
import hashlib
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from config import Config


class GoogleMapsFinder:
    """Finds businesses using AI search + website scraping."""

    # Free models on OpenRouter (verified available)
    FREE_MODELS = [
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemma-3-12b-it:free",
        "mistralai/mistral-small-3.1-24b-instruct:free",
        "qwen/qwen3-4b:free",
    ]

    DEFAULT_CATEGORIES = [
        "startup struggling with manual processes",
        "ecommerce company with growing order volume",
        "marketing agency doing repetitive reporting",
        "SaaS company needing internal tools built fast",
        "logistics company with manual data entry problems",
        "real estate agency needing better client tools",
        "recruitment agency doing manual candidate research",
        "healthcare company needing patient-facing apps",
        "fintech startup building a new product",
        "consulting firm with disconnected business systems",
        "insurance company drowning in paperwork",
        "digital agency outsourcing development work",
        "manufacturing company with quality control bottlenecks",
        "media company needing automated data collection",
        "accounting firm with repetitive document processing",
    ]

    DEFAULT_LOCATIONS = [
        "New York, USA",
        "Los Angeles, USA",
        "London, UK",
        "Toronto, Canada",
        "Sydney, Australia",
        "Dubai, UAE",
        "Singapore",
        "Berlin, Germany",
        "Chicago, USA",
        "Austin, USA",
        "San Francisco, USA",
        "Amsterdam, Netherlands",
    ]

    FIELDNAMES = [
        "name", "address", "website", "phone", "email", "category",
        "rating", "total_reviews", "place_id", "maps_url",
        "source", "search_query", "search_location", "date_found",
    ]

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    def __init__(self):
        self.config = Config()
        self.config.ensure_data_dir()
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.output_file = os.path.join(self.config.DATA_DIR, "google_maps_leads.csv")
        self.ai_clients = []
        self._setup_ai()

    def _setup_ai(self):
        """Set up AI clients for business discovery."""
        try:
            from openai import OpenAI
        except ImportError:
            print("[!] openai not installed. Run: pip install openai")
            return

        for i, key in enumerate(self.config.OPENROUTER_KEYS, 1):
            try:
                client = OpenAI(api_key=key, base_url=self.config.OPENROUTER_BASE_URL, max_retries=0)
                self.ai_clients.append((client, self.FREE_MODELS, f"OpenRouter-Key{i}"))
            except Exception as e:
                print(f"[!] OpenRouter key {i} failed: {e}")

        if self.config.GEMINI_API_KEY:
            try:
                client = OpenAI(api_key=self.config.GEMINI_API_KEY, base_url=self.config.GEMINI_BASE_URL, max_retries=0)
                self.ai_clients.append((client, ["gemini-2.0-flash"], "Gemini"))
            except Exception as e:
                print(f"[!] Gemini init failed: {e}")

        if self.ai_clients:
            print(f"[+] AI business finder ready ({len(self.ai_clients)} providers)")
        else:
            print("[!] No AI providers available for business discovery")

    def _ai_find_businesses(self, category, location, count=10):
        """Use AI to find real businesses."""
        prompt = f"""You are a business research assistant. Return ONLY valid JSON arrays with real, verifiable businesses.

List {count} real {category} businesses located in {location}.

Return ONLY a valid JSON array. Each object must have:
- "name": the company name
- "website": their actual website URL (must be real)
- "address": their address if known, otherwise "{location}"
- "phone": phone number if known, otherwise ""
- "description": one sentence about what they do

Return ONLY the JSON array. No markdown fences. No explanation. No extra text."""

        messages = [{"role": "user", "content": prompt}]

        for client, models, label in self.ai_clients:
            for model in models:
                try:
                    print(f"  [*] Asking {label} / {model}...")
                    resp = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=2000,
                        timeout=30,
                    )
                    text = resp.choices[0].message.content.strip()

                    # Clean markdown fences if present
                    if text.startswith("```"):
                        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                    if text.endswith("```"):
                        text = text.rsplit("```", 1)[0]
                    text = text.strip()

                    # Find the JSON array in the response
                    start = text.find("[")
                    end = text.rfind("]") + 1
                    if start >= 0 and end > start:
                        text = text[start:end]

                    businesses = json.loads(text)
                    if isinstance(businesses, list) and len(businesses) > 0:
                        print(f"  [+] {label} returned {len(businesses)} businesses")
                        return businesses

                except json.JSONDecodeError:
                    print(f"  [!] {label} / {model}: invalid JSON response")
                    continue
                except Exception as e:
                    err = str(e)
                    if "429" in err:
                        print(f"  [!] {label} / {model}: rate limited, trying next...")
                    elif "timeout" in err.lower() or "timed out" in err.lower():
                        print(f"  [!] {label} / {model}: timed out, trying next...")
                    else:
                        print(f"  [!] {label} / {model} failed: {err[:100]}")
                    continue

        print("  [!] All AI providers failed")
        return []

    def search_businesses(self, category, location=None, max_results=10):
        """Find businesses using AI + website scraping."""
        query = f"{category} in {location}" if location else category
        print(f"\n[*] Finding businesses: '{query}'")

        # Step 1: Get business list from AI
        raw = self._ai_find_businesses(category, location or "United States", count=max_results)
        if not raw:
            return []

        # Step 2: Process and enrich each business
        businesses = []
        for item in raw:
            name = item.get("name", "").strip()
            website = item.get("website", "").strip()
            if not name:
                continue

            place_id = hashlib.md5(f"{name}_{website}".encode()).hexdigest()[:16]

            biz = {
                "name": name,
                "address": item.get("address", location or ""),
                "category": category,
                "rating": "",
                "total_reviews": "",
                "place_id": place_id,
                "maps_url": "",
                "website": website,
                "phone": item.get("phone", ""),
                "email": "",
                "source": "ai_search",
                "search_query": category,
                "search_location": location or "",
                "date_found": datetime.now().strftime("%Y-%m-%d"),
            }

            # Enrich from actual website
            if website:
                try:
                    self._enrich_from_website(biz)
                except Exception:
                    pass

            businesses.append(biz)
            contacts = [x for x in [biz.get("email"), biz.get("phone")] if x]
            status = ", ".join(contacts) if contacts else "no contact info"
            print(f"  [+] {name} | {status}")

        print(f"[+] Found {len(businesses)} businesses")
        return businesses

    def _enrich_from_website(self, biz):
        """Visit the business website to extract phone numbers and address."""
        url = biz.get("website", "")
        if not url:
            return

        try:
            resp = self.session.get(url, timeout=(5, 8), allow_redirects=True)
            if resp.status_code != 200:
                return

            text = resp.text[:50000]
            soup = BeautifulSoup(text, "lxml")
            page_text = soup.get_text(" ", strip=True)

            # Extract emails
            email_patterns = re.findall(
                r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
                page_text
            )
            # Filter out common non-business emails
            skip_emails = {'noreply', 'no-reply', 'mailer-daemon', 'example', 'test', 'webmaster'}
            valid_emails = [
                e for e in email_patterns
                if not any(s in e.lower() for s in skip_emails)
                and not e.endswith(('.png', '.jpg', '.svg', '.gif', '.css', '.js'))
            ]
            if valid_emails:
                biz["email"] = valid_emails[0]

            # Also check mailto: links
            if not biz.get("email"):
                mailto = soup.select_one('a[href^="mailto:"]')
                if mailto:
                    email = mailto.get('href', '').replace('mailto:', '').split('?')[0].strip()
                    if '@' in email:
                        biz["email"] = email

            # Extract phone numbers if not already found
            if not biz.get("phone"):
                phone_patterns = re.findall(
                    r'[\+]?1?[\s\-\.]?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}',
                    page_text
                )
                if phone_patterns:
                    biz["phone"] = phone_patterns[0].strip()

            # Try to find address
            if not biz.get("address") or biz["address"] == biz.get("search_location"):
                addr_el = soup.select_one(
                    "[itemprop='address'], .address, .contact-address, "
                    "[class*='address'], footer address"
                )
                if addr_el:
                    addr_text = addr_el.get_text(" ", strip=True)
                    if 5 < len(addr_text) < 200:
                        biz["address"] = addr_text

            # Update final URL after redirects
            biz["website"] = resp.url

        except (Exception, KeyboardInterrupt):
            pass

    # ------------------------------------------------------------------
    # CSV persistence with deduplication
    # ------------------------------------------------------------------

    def save_leads(self, businesses):
        """Save businesses to CSV, skip duplicates by place_id."""
        existing_ids = self._load_existing_ids()
        new = [b for b in businesses if b.get("place_id") and b["place_id"] not in existing_ids]

        if not new:
            print("[*] No new businesses to save")
            return 0

        write_header = not os.path.exists(self.output_file)
        with open(self.output_file, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=self.FIELDNAMES)
            if write_header:
                writer.writeheader()
            for biz in new:
                writer.writerow({k: biz.get(k, "") for k in self.FIELDNAMES})

        print(f"[+] Saved {len(new)} new businesses -> {self.output_file}")
        return len(new)

    def _load_existing_ids(self):
        ids = set()
        if os.path.exists(self.output_file):
            with open(self.output_file, "r", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    ids.add(row.get("place_id", ""))
        return ids

    # ------------------------------------------------------------------
    # Public runner
    # ------------------------------------------------------------------

    def run(self, categories=None, locations=None):
        """Run AI-powered business discovery."""
        categories = categories or self.DEFAULT_CATEGORIES[:3]
        locations = locations or self.DEFAULT_LOCATIONS[:2]

        all_businesses = []
        for loc in locations:
            for cat in categories:
                results = self.search_businesses(cat, loc)
                all_businesses.extend(results)
                time.sleep(self.config.SCRAPE_DELAY)

        self.save_leads(all_businesses)
        return all_businesses


# Allow standalone execution
if __name__ == "__main__":
    finder = GoogleMapsFinder()
    print("\n=== Business Finder (AI-Powered) ===")
    print("Enter categories (one per line, empty to use defaults):")
    cats = []
    while True:
        c = input("  Category > ").strip()
        if not c:
            break
        cats.append(c)

    print("Enter locations (one per line, empty to use defaults):")
    locs = []
    while True:
        l = input("  Location > ").strip()
        if not l:
            break
        locs.append(l)

    finder.run(categories=cats or None, locations=locs or None)
