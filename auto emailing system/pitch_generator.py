"""
AI Pitch Generator — Creates compelling cold outreach messages
Uses OpenRouter → Gemini → Local Model (Ollama) fallback chain
"""

import os
import sys
import json
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

try:
    from openai import OpenAI
except ImportError:
    pass


class PitchGenerator:
    """Generate AI-powered sales pitches using fallback chain."""

    # Core pitch templates (when AI is unavailable)
    PITCH_TEMPLATES = {
        "automation": {
            "subject": "Automate {prospect_name}'s {pain_point} — Free Audit",
            "body": """Hi {prospect_name},

I noticed {prospect_company} handles a lot of {pain_point} manually.

I specialize in **automation solutions** that save teams 10-20 hours weekly. 
Recent clients now:
• Process {metric_value} tasks daily automatically
• Cut operational costs by 40%
• Scale without hiring extra staff

Would you be open to a 15-min chat about how this applies to your team?

Best,
{sender_name}
{sender_title}
{sender_phone}""",
        },
        "leads": {
            "subject": "Get {metric_value} Verified Leads Daily — Automatically",
            "body": """Hi {prospect_name},

{prospect_company} could be acquiring {metric_value} qualified leads **daily** 
through our automated system (without manual work).

We help {prospect_industry} companies:
✓ Find 500+ pre-qualified prospects daily
✓ Extract verified emails & contact info
✓ Auto-segment by fit & engagement level
✓ Integrate with your CRM instantly

Would you like to see a sample of verified leads for your niche?

{sender_name}
{sender_title}""",
        },
        "integration": {
            "subject": "Connect Your Tools — Stop Manual Data Entry",
            "body": """Hi {prospect_name},

Your team probably uses 5+ tools that don't talk to each other.

I build **custom integrations** that:
• Sync data across {tools_mentioned}
• Eliminate manual spreadsheet updates
• Reduce errors by 95%
• Save {metric_value}+ hours per week

How much time does {prospect_company} waste on manual data syncing?

Let's discuss:
{sender_name}
{sender_title}
{sender_phone}""",
        },
        "email_outreach": {
            "subject": "Scale Your Outreach — Personalized Emails at Scale",
            "body": """Hi {prospect_name},

{prospect_company} can reach {metric_value} prospects weekly with 
**AI-personalized, hand-written-style emails** (not spam templates).

Our system:
✓ Generates unique, contextual emails per prospect
✓ Auto-extracts perfect prospect lists
✓ Tracks opens, clicks, replies
✓ Moves responses to your CRM

Average result: {conversion_metric}% reply rate instead of 1-3%.

Interested in a test campaign?

{sender_name}
{sender_title}""",
        },
    }

    def __init__(self):
        self.config = Config()
        self.clients = []
        self._setup_clients()
        self.local_model = None

        # Lazy load local model
        try:
            from local_model_handler import LocalModelHandler

            self.local_model = LocalModelHandler(model="mistral")
        except ImportError:
            pass

    def _setup_clients(self):
        """Set up AI client chain: OpenRouter → Gemini → Local Model."""
        try:
            # OpenRouter clients
            for i, key in enumerate(self.config.OPENROUTER_KEYS, 1):
                try:
                    client = OpenAI(
                        api_key=key,
                        base_url=self.config.OPENROUTER_BASE_URL,
                        max_retries=0,
                    )
                    self.clients.append(
                        (client, "mistralai/mistral-small-3.1-24b-instruct:free", f"OpenRouter-Key{i}")
                    )
                except Exception as e:
                    pass

            # Gemini fallback
            if self.config.GEMINI_API_KEY:
                try:
                    client = OpenAI(
                        api_key=self.config.GEMINI_API_KEY,
                        base_url=self.config.GEMINI_BASE_URL,
                        max_retries=0,
                    )
                    self.clients.append((client, "gemini-2.0-flash", "Gemini"))
                except Exception as e:
                    pass
        except NameError:
            pass

    def generate_pitch(
        self,
        prospect_name: str,
        prospect_company: str,
        prospect_industry: str = "your industry",
        pitch_type: str = "automation",
        context: Optional[dict] = None,
    ) -> dict:
        """
        Generate a personalized pitch.

        Args:
            prospect_name: Contact name
            prospect_company: Company name
            prospect_industry: Industry/category
            pitch_type: Type of pitch (automation, leads, integration, email_outreach)
            context: Optional extra context dict with pain_point, metric_value, etc.

        Returns:
            Dict with 'subject' and 'body'
        """

        if context is None:
            context = {}

        # Fill in common variables
        variables = {
            "prospect_name": prospect_name,
            "prospect_company": prospect_company,
            "prospect_industry": prospect_industry,
            "sender_name": self.config.YOUR_NAME,
            "sender_title": self.config.YOUR_TITLE,
            "sender_phone": self.config.YOUR_PHONE,
            "sender_business": self.config.YOUR_BUSINESS,
            # Smart defaults
            "pain_point": context.get("pain_point", "repetitive tasks"),
            "metric_value": context.get("metric_value", "500"),
            "conversion_metric": context.get("conversion_metric", "15-20%"),
            "tools_mentioned": context.get(
                "tools_mentioned", "Salesforce, Google Sheets, Zapier"
            ),
        }

        # Try AI generation first
        ai_pitch = self._generate_with_ai(
            prospect_name, prospect_company, pitch_type, variables
        )

        if ai_pitch:
            return ai_pitch

        # Fallback to template
        return self._generate_template_pitch(pitch_type, variables)

    def _generate_with_ai(
        self, prospect_name: str, prospect_company: str, pitch_type: str, variables: dict
    ) -> Optional[dict]:
        """Generate pitch using AI (OpenRouter → Gemini → Local)."""

        system_prompt = f"""You are an expert B2B sales copywriter specializing in {pitch_type} solutions.
Generate a compelling, personalized cold outreach email that:
- Speaks to specific pain points
- Opens with a hook (not generic greeting)
- Includes social proof or specific metrics
- Has a clear CTA
- Is 3-4 short paragraphs max
- Feels personal, not templated
- Includes sender contact info

Format response as JSON:
{{"subject": "...", "body": "..."}}"""

        user_prompt = f"""Generate a {pitch_type} pitch for:
- Prospect: {prospect_name}
- Company: {prospect_company}
- Pain point they likely face: {variables.get('pain_point')}
- Key metric to mention: {variables.get('metric_value')} (e.g., leads, hours saved, cost reduction)

Sender details to include:
- Name: {variables['sender_name']}
- Title: {variables['sender_title']}
- Phone: {variables['sender_phone']}"""

        # Try API chain
        for client, model, label in self.clients:
            try:
                print(f"  [→] Generating with {label}...", end="", flush=True)

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.8,
                    max_tokens=500,
                    timeout=30,
                )

                content = response.choices[0].message.content.strip()

                # Try to parse JSON
                if "json" in content.lower():
                    content = content[content.find("{") : content.rfind("}") + 1]

                result = json.loads(content)

                if result.get("subject") and result.get("body"):
                    print(" ✓")
                    return result
            except Exception as e:
                print(f" ✗")
                continue

        # Try local model as last resort
        if self.local_model and self.local_model.is_available():
            try:
                print(f"  [→] Generating with Local Model...", end="", flush=True)

                response = self.local_model.generate(user_prompt, system=system_prompt)

                if response:
                    try:
                        result = json.loads(response)
                        if result.get("subject") and result.get("body"):
                            print(" ✓")
                            return result
                    except json.JSONDecodeError:
                        pass

                print(" ✗")
            except Exception as e:
                print(f" ✗ ({e})")
                pass

        return None

    def _generate_template_pitch(self, pitch_type: str, variables: dict) -> dict:
        """Generate pitch from template."""
        template = self.PITCH_TEMPLATES.get(pitch_type, self.PITCH_TEMPLATES["automation"])

        subject = template.get("subject", "").format(**variables)
        body = template.get("body", "").format(**variables)

        return {"subject": subject, "body": body}

    def batch_generate_pitches(self, prospects: list, pitch_type: str = "automation") -> list:
        """Generate pitches for multiple prospects."""
        results = []

        for i, prospect in enumerate(prospects, 1):
            print(f"\n[{i}/{len(prospects)}] Generating pitch for {prospect.get('name', 'Unknown')}...")
            
            pitch = self.generate_pitch(
                prospect_name=prospect.get("name", "there"),
                prospect_company=prospect.get("company", "your company"),
                prospect_industry=prospect.get("industry", "your industry"),
                pitch_type=pitch_type,
                context=prospect.get("context", {}),
            )

            results.append({**prospect, "pitch": pitch})

        return results


if __name__ == "__main__":
    generator = PitchGenerator()

    # Test
    test_prospect = {
        "name": "Jane Johnson",
        "company": "TechStartup Inc",
        "industry": "software",
        "context": {
            "pain_point": "manual lead generation",
            "metric_value": "500 leads",
        },
    }

    print("\n=== Testing Pitch Generator ===\n")
    pitch = generator.generate_pitch(**test_prospect)

    print("Subject:", pitch["subject"])
    print("\nBody:\n", pitch["body"])
