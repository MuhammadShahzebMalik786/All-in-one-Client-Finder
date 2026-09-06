# All-in-one-Client-Finder

A Python automation toolkit to find business leads, extract contacts, generate AI outreach messages, and send emails from one CLI.

It supports two outreach tracks:
- Traditional pipeline: LinkedIn -> Google Maps -> contact extraction -> personalized email -> SMTP sending
- Freelance pipeline: Fiverr/Upwork discovery -> AI sales pitch generation

The project also includes a local AI fallback with Ollama so generation can keep working when cloud APIs are unavailable.

## Features

- LinkedIn lead discovery
- Google Maps business discovery
- Website contact extraction (emails/phones)
- AI email draft generation for extracted contacts
- SMTP bulk email sending with sent-log tracking
- Fiverr/Upwork client discovery workflow
- AI sales pitch generation (automation, leads, integration, email_outreach)
- Local model fallback (Ollama)
- Automatic unattended pipeline runner with cooldown logic
- CSV-based data outputs for easy review and reuse

## Project Structure

- `main.py`: Interactive CLI menu (options 1-11)
- `automatic_main.py`: Unattended full pipeline runner
- `config.py`: Central configuration loaded from `.env`
- `extract_leads.py`: Contact extraction from websites/CSV/URL
- `google_client_finder.py`: Google Maps client discovery
- `linkdln_company_finder.py`: LinkedIn lead finder
- `fiverr_upwork_finder.py`: Freelance platform client finder
- `local_model_handler.py`: Ollama availability and generation helper
- `auto emailing system/personalize_email_gen.py`: Personalized email generator
- `auto emailing system/pitch_generator.py`: Sales pitch generator
- `auto emailing system/smtp_mail_sender.py`: SMTP sender and send logging

## Requirements

- Python 3.10+
- Windows PowerShell (recommended for provided scripts)
- Optional: Ollama for local AI fallback

Python dependencies are listed in `requirements.txt`.

## Installation

1. Clone the repo and open the project folder.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Configure `.env`.

PowerShell example:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Environment Configuration

Copy `.env.example` to `.env` and fill values:

```powershell
Copy-Item .env.example .env
```

Important variables used by the current code:

- `LINKEDIN_EMAIL`
- `LINKEDIN_PASSWORD`
- `OPENROUTER_KEYS` (comma-separated keys)
- `GEMINI_API_KEY`
- `SMTP_EMAIL`
- `SMTP_PASSWORD`
- `SMTP_SERVER`
- `SMTP_PORT`

Notes:
- `.env` is ignored by Git via `.gitignore`.
- Keep real API keys and app passwords only in `.env`.

## Optional: Local AI Fallback (Ollama)

Install Ollama and start a local model:

```powershell
ollama pull phi
ollama serve
```

Then test from the app menu (option 9) or run:

```powershell
python local_model_handler.py
```

## Run the App

Start the interactive menu:

```powershell
python main.py
```

### Main Menu Options

1. Find Leads on LinkedIn
2. Find Businesses on Google Maps
3. Extract Contacts from Websites
4. Generate Personalized Emails
5. Send Emails
6. Run Full Pipeline
7. Find Clients on Fiverr/Upwork
8. Generate AI Sales Pitches
9. Test Local Model (Ollama)
10. View Statistics
11. Import Leads from CSV
0. Exit

## Typical Workflows

### Workflow A: Freelance Outreach Fast Path

1. Option 7: Find Fiverr/Upwork clients
2. Option 8: Generate AI sales pitches
3. Use `data/generated_pitches.csv` for LinkedIn/email outreach

### Workflow B: Traditional Email Outreach

1. Option 1: LinkedIn leads
2. Option 2: Google Maps leads
3. Option 3: Extract website contacts
4. Option 4: Generate email drafts
5. Option 5: Send emails

### Workflow C: Full Pipeline in One Run

Use option 6 to execute the traditional sequence end-to-end.

## Automated Runs

`automatic_main.py` supports unattended execution and:
- Enforces a cooldown (`data/last_run.txt`)
- Avoids re-drafting and re-sending already processed contacts
- Logs progress to `data/auto_run.log`

Use helper scripts:

- `run_client_finder.bat`: Run unattended pipeline once (respecting cooldown)
- `force_run.bat`: Loop until target sent-email count is reached

## Output Files

Generated CSV/log files appear in `data/`:

- `linkedin_leads.csv`
- `google_maps_leads.csv`
- `extracted_contacts.csv`
- `email_drafts.csv`
- `sent_emails.csv`
- `freelance_platform_clients.csv`
- `generated_pitches.csv`
- `auto_run.log`
- `last_run.txt`

## Safety and Compliance

- Respect website terms of service and platform usage policies.
- Use outreach responsibly and follow anti-spam laws in your region.
- Start with small batches and validate message quality before scaling.

## Troubleshooting

- `Module not found`: activate `.venv` and run `pip install -r requirements.txt`
- SMTP login fails: use app password and verify `SMTP_*` values in `.env`
- No emails generated: ensure `data/extracted_contacts.csv` has valid email entries
- Ollama unavailable: run `ollama serve` and verify local endpoint is reachable

## License

Add your preferred license file (for example MIT) if you plan public reuse.

## Author

Muhammad Shahzeb Malik

## Status

Actively maintained — last touched September 2026.


