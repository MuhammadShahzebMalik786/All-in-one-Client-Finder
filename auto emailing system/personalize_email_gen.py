"""
Personalized Email Generator
Creates AI-powered personalized outreach emails using OpenAI.
Matches portfolio projects to the lead's industry/category, places
related projects first, and generates psychologically compelling subject lines.
Falls back to high-quality templates when OpenAI is unavailable.
"""

import json
import os
import random
import sys

# Allow importing config from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config


class EmailGenerator:
    """Generates personalized cold outreach emails."""

    # Free models on OpenRouter (verified available)
    FREE_MODELS = [
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemma-3-12b-it:free",
        "mistralai/mistral-small-3.1-24b-instruct:free",
        "qwen/qwen3-4b:free",
    ]

    def __init__(self):
        self.config = Config()
        self.portfolio = self._load_portfolio()
        self.clients = []  # list of (client, model, label) tuples
        self._setup_clients()

    def _load_portfolio(self):
        """Load portfolio data from portfolio.json."""
        if os.path.exists(self.config.PORTFOLIO_FILE):
            with open(self.config.PORTFOLIO_FILE, "r", encoding="utf-8") as fh:
                return json.load(fh)
        print("[!] portfolio.json not found — emails won't include project references")
        return {"services": [], "projects": [], "category_mapping": {}}

    def _setup_clients(self):
        """Set up AI clients: OpenRouter key1 -> OpenRouter key2 -> Gemini."""
        try:
            from openai import OpenAI
        except ImportError:
            print("[!] openai not installed. Run: pip install openai")
            return

        # Add OpenRouter clients (one per key)
        for i, key in enumerate(self.config.OPENROUTER_KEYS, 1):
            try:
                client = OpenAI(
                    api_key=key,
                    base_url=self.config.OPENROUTER_BASE_URL,
                    max_retries=0,
                )
                self.clients.append((client, self.FREE_MODELS, f"OpenRouter-Key{i}"))
            except Exception as e:
                print(f"[!] OpenRouter key {i} init failed: {e}")

        # Add Gemini client as final fallback
        if self.config.GEMINI_API_KEY:
            try:
                client = OpenAI(
                    api_key=self.config.GEMINI_API_KEY,
                    base_url=self.config.GEMINI_BASE_URL,
                    max_retries=0,
                )
                self.clients.append((client, ["gemini-2.0-flash"], "Gemini"))
            except Exception as e:
                print(f"[!] Gemini init failed: {e}")

        if self.clients:
            labels = [c[2] for c in self.clients]
            print(f"[+] AI ready: {' -> '.join(labels)} (fallback chain)")
        else:
            print("[*] No AI clients available — will use template-based emails")

    # ------------------------------------------------------------------
    # Portfolio matching
    # ------------------------------------------------------------------

    def _get_relevant_projects(self, business_category):
        """Return projects sorted: related first, then others."""
        mapping = self.portfolio.get("category_mapping", {})
        projects = self.portfolio.get("projects", [])

        # Find best-matching category key
        relevant_cats = None
        cat_lower = (business_category or "").lower()
        for key, cats in mapping.items():
            if key.lower() in cat_lower or cat_lower in key.lower():
                relevant_cats = cats
                break
        if not relevant_cats:
            relevant_cats = mapping.get("default", [])

        related, other = [], []
        for p in projects:
            if p.get("category") in relevant_cats:
                related.append(p)
            else:
                other.append(p)

        return related + other  # related on top, as requested

    # ------------------------------------------------------------------
    # AI-powered generation
    # ------------------------------------------------------------------

    def generate_email(self, lead_info):
        """Generate a personalized email for a single lead.

        lead_info keys: name, company, category/industry, about
        Returns dict with: subject, body, method
        """
        name = lead_info.get("name", "there")
        company = lead_info.get("company", "")
        category = lead_info.get("category", "") or lead_info.get("industry", "")
        about = lead_info.get("about", "")

        projects = self._get_relevant_projects(category)

        if self.clients:
            return self._ai_email(name, company, category, about, projects)
        return self._template_email(name, company, category, projects)

    def _ai_email(self, name, company, category, about, projects):
        """Try each AI client/model in fallback chain until one works."""
        # Build outcome-focused project blocks (no tool names)
        projects_block = "\n".join(
            f"- {p['name']}: {p['description']} → Result: {p.get('outcome', 'Significant efficiency gains')}"
            for p in projects[:3]
        )

        # Pull proven results for social proof
        proven = self.portfolio.get("proven_results", [])
        proof_block = "\n".join(f"- {r}" for r in proven[:3]) if proven else "- Clients report 20-40% efficiency gains from automation"

        prompt = f"""You are writing a cold outreach email. Your goal is to get a REPLY — not a sale.

PSYCHOLOGY RULES (non-negotiable):
- Open with something specific about THEIR business or industry — show you did homework
- Create a "curiosity gap" — hint at a result without fully explaining how
- Use the "pattern interrupt" technique — say something unexpected that breaks the boring email pattern
- Include ONE specific number or result (social proof) from the proven results below
- End with a low-commitment question, NOT a meeting request. Make replying feel effortless
- Write like a human texting a colleague, not a marketer writing copy
- NEVER use phrases like "I hope this email finds you well", "I'd love to", "touching base", "synergy", "leverage"
- NEVER mention specific tool names (no "n8n", "FastAPI", "Flutter", "Python", "Firebase"). Describe OUTCOMES only
- NEVER include any website URL or link
- Keep it under 150 words. Shorter = higher reply rate

SENDER:
- Name: {self.config.YOUR_NAME}
- Role: {self.config.YOUR_TITLE} at {self.config.YOUR_BUSINESS}

RECIPIENT:
- Name/Company: {name} at {company}
- Industry: {category}
- Context: {about}

RELEVANT WORK (describe outcomes, NOT tools):
{projects_block}

PROVEN RESULTS (use one for social proof):
{proof_block}

EMAIL STRUCTURE:
Line 1: Pattern interrupt or specific observation about their business
Line 2-3: Bridge to a relevant outcome you've delivered (with a number)
Line 4: Curiosity gap — tease what's possible for THEM
Line 5: One simple question that's easy to reply to

FORMAT — return EXACTLY:
SUBJECT: [curiosity-driven, under 6 words, no company name]
---
[email body with signature]

Signature format:
Shahzeb
{self.config.YOUR_TITLE}"""

        system_msg = (
            "You are a world-class cold email strategist who understands behavioral psychology. "
            "You write emails that feel like they came from a sharp friend, not a vendor. "
            "Every word earns its place. You never waste the reader's time. "
            "You know that people buy outcomes and hate being sold to. "
            "Your emails get replies because they make people genuinely curious."
        )

        # Try each client in the fallback chain
        for client, models, label in self.clients:
            for model in models:
                try:
                    # Gemma doesn't support system messages — merge into user prompt
                    if "gemma" in model.lower():
                        msgs = [{"role": "user", "content": f"{system_msg}\n\n{prompt}"}]
                    else:
                        msgs = [
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": prompt},
                        ]

                    print(f"    [*] Trying {label} / {model}...")
                    resp = client.chat.completions.create(
                        model=model,
                        messages=msgs,
                        temperature=0.8,
                        max_tokens=600,
                        timeout=30,
                    )

                    text = resp.choices[0].message.content.strip()

                    # Parse subject / body
                    if "SUBJECT:" in text and "---" in text:
                        header, body = text.split("---", 1)
                        subject = header.replace("SUBJECT:", "").strip()
                        body = body.strip()
                    else:
                        subject = f"Quick idea for {company}"
                        body = text

                    print(f"    [+] Success via {label} / {model}")
                    return {"subject": subject, "body": body, "method": f"ai:{label}/{model}"}

                except Exception as e:
                    print(f"    [!] {label} / {model} failed: {e}")
                    continue

        print("  [!] All AI providers failed, falling back to template")
        return self._template_email(name, company, category, projects)

    # ------------------------------------------------------------------
    # Template fallback
    # ------------------------------------------------------------------

    def _template_email(self, name, company, category, projects):
        """Generate psychology-driven email from templates when AI is unavailable."""
        first = name.split()[0] if name and name != "there" else "there"

        # Pick the most relevant project outcome
        proj = projects[0] if projects else None
        outcome = proj.get("outcome", "significant efficiency gains") if proj else "significant efficiency gains"

        # Proven results for social proof
        proven = self.portfolio.get("proven_results", [])
        proof = random.choice(proven) if proven else "20+ hours/week saved through automation"

        subjects = [
            f"Quick question about {company}",
            f"Noticed something interesting",
            f"Weird idea for {category}",
            f"This might be relevant",
            f"Two-minute read, {first}",
        ]

        templates = [
            (
                f"Hi {first},\n\n"
                f"I was looking into {company} and noticed something that reminded me "
                f"of a project I wrapped up recently.\n\n"
                f"We built a system for a company in a similar space — result was {outcome.lower()}. "
                f"Before that, one of our clients saw {proof.lower()}.\n\n"
                f"I have a rough idea of how something similar could work for {company}, "
                f"but I'd need to understand your setup first.\n\n"
                f"Worth a quick conversation?\n\n"
                f"Shahzeb\n"
                f"{self.config.YOUR_TITLE}"
            ),
            (
                f"Hi {first},\n\n"
                f"Most {category} companies I talk to are still doing manually "
                f"what could run on autopilot. Not judging — it's shockingly common.\n\n"
                f"We recently helped a similar business automate their core workflow. "
                f"The result: {proof.lower()}.\n\n"
                f"Curious — is {company} running into any of those same bottlenecks?\n\n"
                f"Shahzeb\n"
                f"{self.config.YOUR_TITLE}"
            ),
            (
                f"Hi {first},\n\n"
                f"Random question — if you could eliminate one repetitive task "
                f"at {company} tomorrow, what would it be?\n\n"
                f"I ask because I build systems that do exactly that. "
                f"Last project delivered {outcome.lower()} for a {category} company.\n\n"
                f"No pitch — genuinely curious what eats up your team's time.\n\n"
                f"Shahzeb\n"
                f"{self.config.YOUR_TITLE}"
            ),
        ]

        return {
            "subject": random.choice(subjects),
            "body": random.choice(templates),
            "method": "template",
        }


# Allow standalone execution
if __name__ == "__main__":
    gen = EmailGenerator()
    print("\n=== Personalized Email Generator (test) ===")
    lead = {
        "name": input("Lead name: ").strip() or "John",
        "company": input("Company: ").strip() or "Acme Corp",
        "category": input("Industry: ").strip() or "marketing agency",
        "about": input("About (optional): ").strip(),
    }
    result = gen.generate_email(lead)
    print(f"\n--- Subject: {result['subject']} ---")
    print(result["body"])
    print(f"\n[method: {result['method']}]")
